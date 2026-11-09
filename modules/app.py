import json
from pathlib import Path
from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from .hotkey import GlobalHotkey
from .keyboard_hook import KeyboardHook
from .panel import IPAPanel


class IPAWontonApp(QObject):
    def __init__(self, qt_app, root: Path):
        super().__init__()
        self.qt_app = qt_app
        with open(root / 'data.json', encoding='utf-8') as f:
            data = json.load(f)
        self.panel = IPAPanel(data, root)

        tray = QSystemTrayIcon(self.qt_app)
        tray.setIcon(QIcon(str(root / 'resources' / 'icon.ico')))
        tray.setToolTip('音标抄手 · IPA+ Wonton')
        menu = QMenu()
        self.show_action = menu.addAction('')
        self.show_action.triggered.connect(self.toggle_panel)
        quit_action = menu.addAction('退出')
        quit_action.triggered.connect(self.qt_app.quit)
        tray.setContextMenu(menu)
        tray.show()
        tray.activated.connect(self.tray_activated)

        self.hotkey = GlobalHotkey(self.toggle_panel)
        self.keyboard_hook = KeyboardHook(self.panel.set_func_key_state)
        self.keyboard_hook.install()
        self.qt_app.installNativeEventFilter(self.hotkey)
        self.qt_app.aboutToQuit.connect(self.cleanup)

    def start(self, show_panel=True):
        self.hotkey.register()
        if show_panel:
            self.panel.show_panel()
            self.show_action.setText('隐藏')
        else:
            self.show_action.setText('显示')

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_panel()

    def toggle_panel(self):
        if self.panel.isVisible():
            self.panel.hide_panel()
            if self.show_action:
                self.show_action.setText('显示')
        else:
            self.panel.show_panel()
            if self.show_action:
                self.show_action.setText('隐藏')

    def cleanup(self):
        self.hotkey.unregister()
        self.keyboard_hook.uninstall()
