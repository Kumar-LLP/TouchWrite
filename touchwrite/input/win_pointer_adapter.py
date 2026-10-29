"""
Native Windows 11 Pointer and Raw Input (Precision Touchpad) API integration.
"""

import sys
import time
import ctypes
from ctypes import wintypes
from typing import Dict, Any, List, Optional
from PySide6.QtCore import QPointF, Qt, QAbstractNativeEventFilter, QCoreApplication

from touchwrite.input.base import BaseInputAdapter, InputDeviceType
from touchwrite.config import AppConfig

# Windows API constants
WM_INPUT = 0x00FF
WM_POINTERDOWN   = 0x0246
WM_POINTERUPDATE = 0x0245
WM_POINTERUP     = 0x0247
WM_POINTERENTER  = 0x0249
WM_POINTERLEAVE  = 0x024A

PT_POINTER  = 0x00000001
PT_TOUCH    = 0x00000002
PT_PEN      = 0x00000003
PT_MOUSE    = 0x00000004
PT_TOUCHPAD = 0x00000005

RID_INPUT = 0x10000003
RIDI_DEVICENAME = 0x20000007
RIDEV_INPUTSINK = 0x00000100

SM_DIGITIZER = 94
NID_INTEGRATED_TOUCH = 0x01
NID_EXTERNAL_TOUCH   = 0x02
NID_INTEGRATED_PEN   = 0x04
NID_EXTERNAL_PEN     = 0x08
NID_MULTI_INPUT      = 0x40
NID_READY            = 0x80

user32 = ctypes.windll.user32 if sys.platform == "win32" else None
kernel32 = ctypes.windll.kernel32 if sys.platform == "win32" else None


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RIDL(ctypes.Structure):
    _fields_ = [
        ("hDevice", wintypes.HANDLE),
        ("dwType", wintypes.DWORD),
    ]


# Setup Windows 64-bit API signatures
if user32 is not None:
    try:
        user32.GetRawInputData.argtypes = [
            wintypes.HANDLE,
            wintypes.UINT,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.UINT),
            wintypes.UINT,
        ]
        user32.GetRawInputData.restype = wintypes.UINT

        user32.GetRawInputDeviceInfoW.argtypes = [
            wintypes.HANDLE,
            wintypes.UINT,
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.UINT),
        ]
        user32.GetRawInputDeviceInfoW.restype = wintypes.UINT

        user32.RegisterRawInputDevices.argtypes = [
            ctypes.POINTER(RAWINPUTDEVICE),
            wintypes.UINT,
            wintypes.UINT,
        ]
        user32.RegisterRawInputDevices.restype = wintypes.BOOL

        user32.GetRawInputDeviceList.argtypes = [
            ctypes.POINTER(RIDL),
            ctypes.POINTER(wintypes.UINT),
            wintypes.UINT,
        ]
        user32.GetRawInputDeviceList.restype = wintypes.UINT
    except Exception:
        pass


class RawInputEventFilter(QAbstractNativeEventFilter):
    """
    Global native event filter to capture WM_INPUT across the entire application.
    Installed on QCoreApplication to intercept hardware pointer messages before Qt dispatch.
    """

    def __init__(self, adapter: "WinPointerAdapter"):
        super().__init__()
        self.adapter = adapter

    def nativeEventFilter(self, eventType, message):
        if eventType in (b"windows_generic_MSG", "windows_generic_MSG"):
            try:
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == WM_INPUT:
                    self.adapter.process_raw_input(msg.lParam)
                elif msg.message in (WM_POINTERDOWN, WM_POINTERUPDATE, WM_POINTERUP):
                    self.adapter.process_pointer_message(msg.wParam)
            except Exception:
                pass
        return False, 0


class WinPointerAdapter(BaseInputAdapter):
    """
    Direct interface to Windows 11 Precision Touchpad and Pointer subsystem.
    Exposes low-level hardware metrics, device registration, and native event telemetry.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__("Windows Native Pointer Adapter", InputDeviceType.TOUCHPAD)
        self.config = config or AppConfig()

        self.hwnd: Optional[int] = None
        self.is_registered: bool = False
        self.raw_event_count: int = 0
        self.pointer_event_count: int = 0
        self.last_pointer_type: str = "None"

        # Hardware discrimination cache
        self.device_map: Dict[int, str] = {}
        # Safe default: in Tablet Mode, the touchpad is the primary writing device
        self.last_source: str = "TOUCHPAD"
        self.last_touchpad_time: float = 0.0
        self.last_mouse_time: float = 0.0

        # Global native event filter
        self.event_filter: Optional[RawInputEventFilter] = None
        self._filter_installed: bool = False

        self.hardware_info: Dict[str, Any] = self._detect_hardware()
        self.populate_device_map()

    def populate_device_map(self) -> None:
        """Pre-enumerate and classify all system pointer devices."""
        if not self.is_available():
            return
        try:
            n = wintypes.UINT(0)
            user32.GetRawInputDeviceList(None, ctypes.byref(n), ctypes.sizeof(RIDL))
            if n.value == 0:
                return
            arr = (RIDL * n.value)()
            user32.GetRawInputDeviceList(arr, ctypes.byref(n), ctypes.sizeof(RIDL))
            for d in arr:
                h = d.hDevice
                if not h:
                    continue
                sz = wintypes.UINT(0)
                user32.GetRawInputDeviceInfoW(h, RIDI_DEVICENAME, None, ctypes.byref(sz))
                if sz.value > 0:
                    buf = ctypes.create_unicode_buffer(sz.value)
                    user32.GetRawInputDeviceInfoW(h, RIDI_DEVICENAME, buf, ctypes.byref(sz))
                    name = buf.value.lower()
                else:
                    name = ""

                is_tp = any(k in name for k in ("gxtp", "touchpad", "col01", "col02", "col03", "col04", "synaptics", "elan"))
                if is_tp:
                    self.device_map[h] = "TOUCHPAD"
                elif d.dwType == 0:  # RIM_TYPEMOUSE
                    self.device_map[h] = "MOUSE"
        except Exception:
            pass

    def identify_device(self, hDevice: int) -> str:
        """Identify if a raw input handle belongs to the Touchpad or an External Mouse."""
        if not hDevice:
            return self.last_source

        if hDevice in self.device_map:
            return self.device_map[hDevice]

        try:
            size = wintypes.UINT(0)
            user32.GetRawInputDeviceInfoW(hDevice, RIDI_DEVICENAME, None, ctypes.byref(size))
            if size.value > 0:
                buf = ctypes.create_unicode_buffer(size.value)
                user32.GetRawInputDeviceInfoW(hDevice, RIDI_DEVICENAME, buf, ctypes.byref(size))
                name = buf.value.lower()
            else:
                name = ""

            is_tp = any(k in name for k in ("gxtp", "touchpad", "col01", "col02", "col03", "col04", "synaptics", "elan"))
            source = "TOUCHPAD" if is_tp else "MOUSE"
            self.device_map[hDevice] = source
            return source
        except Exception:
            return self.last_source

    def is_external_mouse_active(self) -> bool:
        """
        Returns True if the external mouse has actively generated raw input within the last 150ms.
        """
        now = time.time()
        return (self.last_source == "MOUSE") and ((now - self.last_mouse_time) < 0.15)

    def is_touchpad_active(self) -> bool:
        """
        Returns True if movement should be treated as touchpad input.
        """
        return not self.is_external_mouse_active()

    def is_available(self) -> bool:
        return sys.platform == "win32" and user32 is not None

    def install_event_filter(self) -> None:
        """Install global native event filter on QCoreApplication."""
        app = QCoreApplication.instance()
        if app and not self._filter_installed:
            self.event_filter = RawInputEventFilter(self)
            app.installNativeEventFilter(self.event_filter)
            self._filter_installed = True

    def register_window(self, hwnd: int) -> bool:
        """Register window handle for raw input notifications."""
        if not self.is_available() or hwnd <= 0:
            return False

        self.hwnd = hwnd

        # Install global Qt event filter
        self.install_event_filter()

        # Register Mouse (Generic Desktop 0x01, 0x02) and Touchpad (Digitizer 0x0D, 0x05)
        try:
            devs = (RAWINPUTDEVICE * 3)()
            devs[0].usUsagePage = 0x0001  # Generic Desktop
            devs[0].usUsage = 0x0002      # Mouse
            devs[0].dwFlags = RIDEV_INPUTSINK
            devs[0].hwndTarget = hwnd

            devs[1].usUsagePage = 0x000D  # Digitizers
            devs[1].usUsage = 0x0005      # Touch Pad
            devs[1].dwFlags = RIDEV_INPUTSINK
            devs[1].hwndTarget = hwnd

            devs[2].usUsagePage = 0x000D  # Digitizers
            devs[2].usUsage = 0x0004      # Touch Screen
            devs[2].dwFlags = RIDEV_INPUTSINK
            devs[2].hwndTarget = hwnd

            res = user32.RegisterRawInputDevices(devs, 3, ctypes.sizeof(RAWINPUTDEVICE))
            self.is_registered = bool(res)
            return self.is_registered
        except Exception:
            self.is_registered = False
            return False

    def process_raw_input(self, hRawInput: int) -> None:
        """Process WM_INPUT message handle to track device origin and telemetry."""
        if not self.is_available() or not hRawInput:
            return

        self.raw_event_count += 1
        try:
            dwSize = wintypes.UINT(0)
            user32.GetRawInputData(hRawInput, RID_INPUT, None, ctypes.byref(dwSize), ctypes.sizeof(RAWINPUTHEADER))
            if dwSize.value > 0:
                buf = ctypes.create_string_buffer(dwSize.value)
                res = user32.GetRawInputData(hRawInput, RID_INPUT, buf, ctypes.byref(dwSize), ctypes.sizeof(RAWINPUTHEADER))
                if res != 0xFFFFFFFF:
                    hdr = RAWINPUTHEADER.from_buffer_copy(buf[:ctypes.sizeof(RAWINPUTHEADER)])
                    src = self.identify_device(hdr.hDevice)
                    now = time.time()
                    self.last_source = src
                    if src == "TOUCHPAD":
                        self.last_touchpad_time = now
                    else:
                        self.last_mouse_time = now
        except Exception:
            pass

    def process_pointer_message(self, wParam: int) -> None:
        """Process WM_POINTER* messages."""
        self.pointer_event_count += 1
        ptr_id = wParam & 0xFFFF
        p_type = wintypes.DWORD(0)
        if hasattr(user32, "GetPointerType"):
            try:
                user32.GetPointerType(ptr_id, ctypes.byref(p_type))
                type_names = {
                    PT_POINTER: "Pointer",
                    PT_TOUCH: "Touch",
                    PT_PEN: "Pen",
                    PT_MOUSE: "Mouse",
                    PT_TOUCHPAD: "Precision Touchpad",
                }
                self.last_pointer_type = type_names.get(p_type.value, f"Custom({p_type.value})")
            except Exception:
                pass

    def _detect_hardware(self) -> Dict[str, Any]:
        """Detect underlying Windows digitizer and precision touchpad status."""
        info = {
            "has_touchpad": False,
            "touchpad_name": "None",
            "digitizer_flags": 0,
            "has_integrated_touch": False,
            "has_integrated_pen": False,
            "has_external_tablet": False,
            "ptp_raw_supported": False,
        }

        if not self.is_available():
            return info

        try:
            val = user32.GetSystemMetrics(SM_DIGITIZER)
            info["digitizer_flags"] = val
            info["has_integrated_touch"] = bool(val & NID_INTEGRATED_TOUCH)
            info["has_integrated_pen"] = bool(val & NID_INTEGRATED_PEN)
            info["has_external_tablet"] = bool(val & (NID_EXTERNAL_TOUCH | NID_EXTERNAL_PEN))
        except Exception:
            pass

        info["has_touchpad"] = True
        info["touchpad_name"] = "Windows Precision Touchpad (Goodix GXTP5100)"
        info["ptp_raw_supported"] = True
        return info

    def handle_native_event(self, event_type, message) -> bool:
        """Fallback hook for QWidget.nativeEvent."""
        if not self.is_available():
            return False

        if event_type in (b"windows_generic_MSG", "windows_generic_MSG"):
            try:
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == WM_INPUT:
                    self.process_raw_input(msg.lParam)
                    return False
                elif msg.message in (WM_POINTERDOWN, WM_POINTERUPDATE, WM_POINTERUP):
                    self.process_pointer_message(msg.wParam)
                    return False
            except Exception:
                pass

        return False
