from pathlib import Path
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap, QMouseEvent
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy, QWidget, QLabel, QCheckBox, QTabWidget, QPushButton, QButtonGroup, QRadioButton

from .input import send_unicode_text, set_window_no_activate

BUTTON_WIDTH = 24
BUTTON_HEIGHT = 32
FONT_SIZE = 18
FONT_SIZE_MID = 21
FONT_SIZE_BIG = 24
SIL_FONTS = ['Doulos SIL', 'Doulos Unt', 'Times New Roman',
             'Cambria', 'Unifont', 'Unifont Upper', 'serif']
UNT_FONTS = ['Doulos Unt', 'Doulos SIL', 'Times New Roman',
             'Cambria', 'Unifont', 'Unifont Upper', 'serif']
UNT_SYMBOLS = {
    'ˁ', 'ˀ', '0̸',
    'ˤ',
}
FUNC_KEY_FLAGS = {
    'Shift':       'Shift\n字母上标\n符号居上',
    'Ctrl':        'Ctrl\n小型大写\n符号居下',
}
LETTER_FLAGS = {
    'capital':     '大写',
    'subscript':   '下标',
}
MODIFIER_FLAGS = {
    'combining':   '附加',
    'spacing':     '独立',
    'precomposed': '预组',
}
FLAG_TO_KEY1 = {
    True: {  # letter
        'Shift': 'superscript',
        'subscript': 'subscript',
    },
    False: {  # modifier
        'combining': 'combining',
        'spacing': 'spacing',
        'precomposed': 'precomposed',
    },
}
FLAG_TO_KEY2 = {
    True: {  # letter
        'capital': 'capital',
        'Ctrl': 'small_capital',
    },
    False: {  # modifier
        'Shift': 'high',
        'Ctrl': 'low',
    },
}


class DummyButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet('''
            QPushButton {
                border: none;
            }
        ''')
        self.setDisabled(True)


class SymbolButton(QPushButton):
    def __init__(self, type: str, info: dict, panel: QWidget, parent=None):
        super().__init__(parent)
        self.is_letter = type == 'letter'
        self.info = info
        self.panel = panel
        self.setStyleSheet('''
            QPushButton {
                font-size: 0;
                color: transparent;
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #dbeeff;
                border-color: #6aa9e9;
            }
            QPushButton:pressed {
                background-color: #bcdcff;
            }
        ''')
        self.update_label()
        self.setFocusPolicy(Qt.NoFocus)
        self.clicked.connect(self.insert_symbol)

    def update_label(self):
        self.label = None  # 显示的字符
        self.value = None  # 实际插入的字符
        self.variant_fallback = False

        k1 = 'normal'
        for flag, v in self.panel.variant_flags.items():
            if v and flag in FLAG_TO_KEY1[self.is_letter]:
                k1 = FLAG_TO_KEY1[self.is_letter][flag]
                break

        k2 = 'default'
        for flag, v in self.panel.variant_flags.items():
            if v and flag in FLAG_TO_KEY2[self.is_letter]:
                k2 = FLAG_TO_KEY2[self.is_letter][flag]
                break

        self.label = self.info.get(k1, {}).get(k2)
        if not self.label and not self.is_letter:
            for k1 in self.info:
                if self.info.get(k1, {}).get(k2):
                    self.label = self.info.get(k1, {}).get(k2)
                    self.variant_fallback = True
                    break
        if self.label:
            self.value = self.label if self.is_letter else \
                self.label.replace('◌', '')
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.label:
            return
        painter = QPainter(self)
        is_normal = self.is_letter and not (
            self.panel.variant_flags['Shift'] or  # superscript
            self.panel.variant_flags['subscript'])
        is_big = '◌' in self.label

        rect = self.rect()
        rect = rect.adjusted(0, -1, 0, -1)

        font = QFont()
        font_size = FONT_SIZE if is_normal else FONT_SIZE_MID
        font_families = UNT_FONTS if self.label in UNT_SYMBOLS else SIL_FONTS
        if is_big:
            rect = rect.adjusted(0, -2, 0, -2)
            font_size = FONT_SIZE_BIG
        font.setPixelSize(font_size)
        font.setFamilies(font_families)
        painter.setFont(font)

        # 为了使 Doulos SIL 的笔画更清晰，先绘制一层浅色字符，再叠加一层深色字符
        for color in [
            (173, 200, 224), (134, 180, 218),
        ] if self.variant_fallback else [
            (204, 204, 204), (0, 0, 0),
        ]:
            painter.setPen(QColor(*color))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.label)
        painter.end()

    def insert_symbol(self):
        if not self.value:
            return
        send_unicode_text(self.value)

        # 如果选中未锁定，那么键入一次后就取消选中
        for button in self.panel.option_buttons.values():
            if isinstance(button, QCheckBox) and button.checkState() == Qt.CheckState.PartiallyChecked:
                button.setCheckState(Qt.CheckState.Unchecked)


class IPAPanel(QWidget):
    def __init__(self, data: dict, root: Path, parent=None):
        super().__init__(parent)
        self.data = data
        self.root = root
        self.option_buttons = {}
        self.symbol_buttons = []
        self.variant_flags = {
            k: False for k in [*FUNC_KEY_FLAGS, *LETTER_FLAGS, *MODIFIER_FLAGS]}
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self._build_ui()
        set_window_no_activate(int(self.winId()))
        self._has_position = False

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)

        self.header_logo = QLabel(self)
        self.header_logo.setPixmap(QPixmap(str(self.root / 'resources' / 'logo.png')).scaled(
            48, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.header_logo.adjustSize()
        # 留待 show_panel() 中再设置位置，不然无法得知坐标

        header = QHBoxLayout()
        outer.addLayout(header)
        header.addStretch()
        # 为 logo 预留空间
        header.addItem(QSpacerItem(
            56, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.header_title = QLabel('音标抄手 · IPA+ Wonton')
        self.header_title.setStyleSheet('font-size: 16px; font-weight: 600;')
        header.addWidget(
            self.header_title, alignment=Qt.AlignmentFlag.AlignCenter)
        header.addStretch()

        inner = QHBoxLayout()
        inner_l = QVBoxLayout()
        inner_r = QGridLayout()
        outer.addLayout(inner)
        inner.addLayout(inner_l)
        inner.addLayout(inner_r)

        inner_l.setSpacing(12)
        inner_l.addStretch()
        for i, (k, label) in enumerate(FUNC_KEY_FLAGS.items()):
            checkbox = QCheckBox(label)
            checkbox.k = k
            checkbox.setTristate(True)
            checkbox.checkStateChanged.connect(self.on_option_changed)
            self.option_buttons[k] = checkbox
            inner_l.addWidget(checkbox)
        inner_l.addStretch()

        tabs_style = '''
            QTabWidget::pane {
                background: #ffffff;
                border: 1px solid #ffffff;
                border-radius: 10px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background: #f0f0f0;
                color: #000000;
                border: 1px solid #cccccc;
                %s
            }
            QTabBar::tab:selected {
                background: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background: #e0e0e0;
            }
        '''
        self.letter_tabs = QTabWidget()
        self.letter_tabs.setStyleSheet(tabs_style % '''
                padding: 4px 8px 2px;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
        ''')
        self.modifier_tabs = QTabWidget()
        self.modifier_tabs.setTabPosition(QTabWidget.TabPosition.South)
        self.modifier_tabs.setStyleSheet(tabs_style % '''
                padding: 2px 8px 4px;
                border-top: none;
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
        ''')
        for row, (k, tabs) in enumerate([
            ('letter_tabs', self.letter_tabs),
            ('modifier_tabs', self.modifier_tabs),
        ]):
            button_type = k.split('_')[0]
            tabs.setFocusPolicy(Qt.NoFocus)
            inner_r.addWidget(tabs, row, 0)
            for tab in self.data[k]:
                page = QWidget()
                tabs.addTab(page, tab['label'])
                grid = QGridLayout(page)
                grid.setContentsMargins(6, 6, 2, 4)
                grid.setHorizontalSpacing(4)
                grid.setVerticalSpacing(4)
                for y, column in enumerate(tab['buttons']):
                    for x, button_info in enumerate(column):
                        if button_info is None:
                            button = DummyButton()
                        else:
                            button = SymbolButton(
                                button_type, button_info, self)
                            self.symbol_buttons.append(button)
                        button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
                        grid.addWidget(button, x, y)

        layout = QVBoxLayout()
        inner_r.addLayout(layout, 0, 1)
        layout.setContentsMargins(0, 20, 20, 0)
        layout.setSpacing(0)
        layout.addStretch()
        for i, (k, label) in enumerate(LETTER_FLAGS.items()):
            checkbox = QCheckBox(label)
            checkbox.k = k
            checkbox.setTristate(True)
            checkbox.checkStateChanged.connect(self.on_option_changed)
            self.option_buttons[k] = checkbox
            layout.addWidget(checkbox)
        layout.addStretch()

        layout = QVBoxLayout()
        inner_r.addLayout(layout, 1, 1)
        layout.setContentsMargins(0, 0, 20, 20)
        layout.setSpacing(0)
        radio_group = QButtonGroup(self)
        radio_group.buttonClicked.connect(self.on_option_changed)
        layout.addStretch()
        for i, (k, label) in enumerate(MODIFIER_FLAGS.items()):
            rb = QRadioButton(label)
            rb.k = k
            if label == '预组':
                rb.setDisabled(True)
            radio_group.addButton(rb, id=i)
            self.option_buttons[k] = rb
            layout.addWidget(rb)
        layout.addStretch()
        radio_group.buttons()[0].click()

        footer = QGridLayout()
        footer.setColumnStretch(0, 1)
        footer.setColumnStretch(1, 0)
        footer.setColumnStretch(2, 1)
        outer.addLayout(footer)
        hide_button = QPushButton('最小化')
        hide_button.setStyleSheet('background-color: #bcdcff;')
        hide_button.clicked.connect(self.hide_panel)
        footer.addWidget(hide_button, 0, 1)
        exit_button = QPushButton('退出')
        exit_button.setStyleSheet('background-color: #ffcacc;')
        exit_button.clicked.connect(self.quit_application)
        footer.addWidget(exit_button, 0, 2,
                         alignment=Qt.AlignmentFlag.AlignRight)

    def show_panel(self):
        self.show()

        x = self.header_title.mapTo(self, QPoint(0, 0)).x() - 56
        self.header_logo.move(x, 5)

        # 仅在第一次弹出时使用默认位置
        if not self._has_position:
            self._set_default_position()
            self._has_position = True
        for tab in (self.letter_tabs, self.modifier_tabs):
            if tab:
                tab.setCurrentIndex(0)

        self.raise_()
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        set_window_no_activate(int(self.winId()))

    def _set_default_position(self):
        screen = self.screen()
        if not screen:
            return
        geo = screen.availableGeometry()
        x = geo.left() + (geo.width() - self.width()) // 2
        y = geo.bottom() - self.height() - 40
        self.move(x, y)

    def quit_application(self):
        QApplication.instance().quit()

    def hide_panel(self):
        self.hide()

    def toggle(self):
        if self.isVisible():
            self.hide_panel()
        else:
            self.show_panel()

    def on_option_changed(self, state):
        sender = self.sender()
        is_checkbox = isinstance(sender, QCheckBox)
        value = state != Qt.CheckState.Unchecked
        if not is_checkbox:  # QButtonGroup
            for button in sender.buttons():
                if button.isChecked():
                    sender = button
                    break
            value = True
        prev_value = self.variant_flags[sender.k]

        for flags in (FUNC_KEY_FLAGS, LETTER_FLAGS, MODIFIER_FLAGS):
            if value and sender.k in flags:
                for k in flags:
                    if k != sender.k:
                        self.variant_flags[k] = False
                        if is_checkbox:
                            self.option_buttons[k].setCheckState(
                                Qt.CheckState.Unchecked)
        self.variant_flags[sender.k] = value
        if value == prev_value:
            return
        for button in self.symbol_buttons:
            button.update_label()

    def set_func_key_state(self, key_name, pressed: bool):
        if key_name not in self.option_buttons:
            return
        if (self.option_buttons[key_name].checkState() == Qt.CheckState.Checked) == pressed:
            return
        self.option_buttons[key_name].setCheckState(
            Qt.CheckState.Checked if pressed else Qt.CheckState.Unchecked)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
