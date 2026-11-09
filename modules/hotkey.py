import ctypes
from ctypes import wintypes
from PySide6.QtCore import QAbstractNativeEventFilter

user32 = ctypes.WinDLL('user32', use_last_error=True)

WM_HOTKEY = 0x0312
HOTKEY_ID = int.from_bytes(b'IPA+')  # 定义一个本程序独有的 ID
MOD_CONTROL = 0x0002
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
VK_W = 0x57  # `W` key


class GlobalHotkey(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.registered = False

    def register(self):
        success = user32.RegisterHotKey(
            None,
            HOTKEY_ID,
            MOD_CONTROL | MOD_WIN | MOD_NOREPEAT,
            VK_W,
        )
        if not success:
            raise RuntimeError('无法注册 Shift+Win+W')

    def unregister(self):
        user32.UnregisterHotKey(None, HOTKEY_ID)

    def nativeEventFilter(self, eventType, message):
        if eventType in ('windows_generic_MSG', 'windows_dispatcher_MSG'):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.callback()
                return True, 0
        return False, 0
