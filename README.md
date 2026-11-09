# ![logo](resources/logo.png) 音标抄手 · IPA+ Wonton

轻量级音标符号（国际音标及更多）悬浮输入面板。目前仅适用于 Windows 系统。

名字是一个双关：“抄手”既可以理解为抄录者（即，输入法），也可以是一种馄饨，而“馄饨”是音标抄手开发者 unt 的一个昵称。

## 安装

建议建立一个独立的 Python 环境，然后执行 `pip install PySide6`，即完成配置。（注意 `PySide6` 包不能通过 `conda-forge` 安装，不然会安不完整）

## 启动

`python main.py` 为正常启动。`python main.py --hidden` 为静默启动（启动时不显示面板）。

可以建立一个快捷方式，目标设为 `"[环境下 Python 的位置]\pythonw.exe" "[本 repo 路径]\main.py" --hidden`，然后将这个快捷方式放在“启动”文件夹中（资源管理器或 `Win+R` 进入 `shell:startup` 路径，即为“启动”文件夹），即可让音标抄手开机自启。

## 功能

按 `Ctrl+Win+W` 可以呼出音标抄手面板，或隐藏面板。（`W` 可理解为“Wonton”的首字母）

面板显示时，按 `Shift` 和 `Ctrl` 可实现面板上相应按钮的功能，方便输入。

## 待完成

- [ ] 关于音标字体的说明
- [ ] 预组字符的输入
- [ ] 区分字符是否属于国际音标或过时国际音标
