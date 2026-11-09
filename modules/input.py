import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
ULONG_PTR = ctypes.c_void_p


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD),
    ]


class INPUTUNION(ctypes.Union):
    _fields_ = [
        ('ki', KEYBDINPUT),
        ('mi', MOUSEINPUT),
        ('hi', HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ('u',)
    _fields_ = [
        ('type', wintypes.DWORD),
        ('u', INPUTUNION),
    ]


user32.SendInput.argtypes = [
    wintypes.UINT,
    ctypes.POINTER(INPUT),
    ctypes.c_int,
]
user32.SendInput.restype = wintypes.UINT


def send_unicode_text(text: str) -> None:
    if not text:
        return
    raw = text.encode('utf-16-le', 'surrogatepass')
    units = [int.from_bytes(raw[i:i + 2], 'little')
             for i in range(0, len(raw), 2)]

    inputs = []
    for unit in units:
        for dwFlags in (
            KEYEVENTF_UNICODE,  # key down
            KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,  # key up
        ):
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.ki = KEYBDINPUT(
                wVk=0,
                wScan=unit,
                dwFlags=dwFlags,
                time=0,
                dwExtraInfo=0,
            )
            inputs.append(inp)
    if not inputs:
        return
    count = len(inputs)
    array_type = INPUT * count
    input_array = array_type(*inputs)
    sent = user32.SendInput(count, input_array, ctypes.sizeof(INPUT))
    if sent != count:
        raise ctypes.WinError()


def set_window_no_activate(hwnd: int) -> None:
    GWL_EXSTYLE = -20
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_TOOLWINDOW = 0x00000080
    user32.GetWindowLongPtrW.argtypes = [
        wintypes.HWND,
        ctypes.c_int,
    ]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.SetWindowLongPtrW.argtypes = [
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_ssize_t,
    ]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
    style = style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
    user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
