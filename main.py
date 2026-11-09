import sys
import argparse
from pathlib import Path
from PySide6.QtWidgets import QApplication

from modules.app import IPAWontonApp


def main():
    parser = argparse.ArgumentParser(description='音标抄手 · IPA+ Wonton')
    parser.add_argument('--hidden', action='store_true', help='启动时隐藏窗口')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName('IPA+ Wonton')
    app.setApplicationDisplayName('音标抄手 · IPA+ Wonton')
    app.setQuitOnLastWindowClosed(False)

    controller = IPAWontonApp(app, Path(__file__).parent)
    controller.start(not args.hidden)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
