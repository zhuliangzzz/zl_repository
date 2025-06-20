#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2025/5/29 17:12
   @software:PyCharm
   @desc:
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor


class CustomWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)  # 去除原生标题栏
        self.setGeometry(100, 100, 400, 300)

        # 创建自定义标题栏（一个普通控件，如 QWidget）
        title_bar = QWidget()
        title_bar.setFixedHeight(30)  # 设置标题栏高度

        # 使用 QPalette 设置标题栏背景色
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor("#4A6FA5"))  # 设置背景色
        title_bar.setPalette(palette)
        title_bar.setAutoFillBackground(True)  # 启用调色板背景填充

        # 添加标题文本
        title_label = QLabel("自定义标题栏")
        layout = QVBoxLayout(title_bar)
        layout.addWidget(title_label)

        # 将标题栏添加到窗口布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(title_bar)
        main_layout.addWidget(QLabel("窗口内容"))
        self.setCentralWidget(central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomWindow()
    window.show()
    sys.exit(app.exec_())