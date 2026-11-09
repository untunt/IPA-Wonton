import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)

WH_KEYBOARD_LL = 13  # low-level keyboard hook
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
key_code_to_name = {
    VK_LSHIFT: 'Shift',
    VK_RSHIFT: 'Shift',
    VK_LCONTROL: 'Ctrl',
    VK_RCONTROL: 'Ctrl',
}

ULONG_PTR = ctypes.c_void_p
LRESULT = ctypes.c_ssize_t


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ('vkCode', wintypes.DWORD),
        ('scanCode', wintypes.DWORD),
        ('flags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ULONG_PTR),
    ]


LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    LRESULT,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

user32.CallNextHookEx.argtypes = [
    wintypes.HHOOK,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.CallNextHookEx.restype = LRESULT


class KeyboardHook:
    def __init__(self, callback):
        self.callback = callback
        self.hook = None
        self.proc = LowLevelKeyboardProc(self._hook_proc)

    def install(self):
        self.hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self.proc, None, 0)
        if not self.hook:
            raise ctypes.WinError(ctypes.get_last_error())

    def uninstall(self):
        if self.hook:
            user32.UnhookWindowsHookEx(self.hook)
            self.hook = None

    def _hook_proc(self, nCode, wParam, lParam):
        if nCode >= 0:
            info = ctypes.cast(
                lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            key_name = key_code_to_name.get(info.vkCode)
            if key_name:
                if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    self.callback(key_name, True)
                elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                    self.callback(key_name, False)
        return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)
