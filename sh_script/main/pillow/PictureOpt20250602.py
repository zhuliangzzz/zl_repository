#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:PictureOpt.py
   @author:zl
   @time: 2025/5/24 17:22
   @software:PyCharm
   @desc:
"""
import io
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QIcon, QIntValidator
from PyQt5.QtWidgets import *
from PIL import Image, ImageFilter
import qtawesome
from qtawesome import icon_browser
import PictureOptUI as ui
import res_rc

class PictureOpt(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.pushButton_select_pic.setIcon(qtawesome.icon('fa.folder-open', color='white'))
        self.pushButton_opt.setIcon(qtawesome.icon('ei.idea-alt', color='white'))
        self.pushButton_save.setIcon(qtawesome.icon('fa.save', color='white'))
        self.pushButton_select_pic.clicked.connect(self.select_pic)
        self.lineEdit_rotate.setPlaceholderText('输入旋转角度')
        self.lineEdit_rotate.setValidator(QIntValidator())
        ways = ('不加', '模糊', '平滑', '平滑+',  '锐化', '浮雕', '素描', '细节', '边缘突出', '边缘增强', '边缘增强+')
        self.comboBox_opt_way.addItems(ways)
        transposes = ('不翻转', '上下', '左右')
        self.comboBox_transpose.addItems(transposes)
        self.pushButton_opt.clicked.connect(self.opt)
        self.lineEdit_save_path.setText('./images/generate')
        self.pushButton_save.clicked.connect(self.save_pic)
        self.setStyleSheet('QPushButton{font:10pt;background-color:#459B81;color:white;} QPushButton:hover{background:#333;}')

    def select_pic(self):
        filepath, _ = QFileDialog.getOpenFileName(self, '选择图片', 'images', '*.png *.jpg *.jepg')
        print(filepath)
        if filepath:
            self.filepath = filepath
            pixmap = QPixmap(filepath)
            scaled_pixmap = pixmap.scaled(
                self.label_origin_pic.width(), self.label_origin_pic.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label_origin_pic.setPixmap(scaled_pixmap)

    def opt(self):
        self.image_ = Image.open(self.filepath)
        angle = self.lineEdit_rotate.text().strip()
        if angle:
            self.image_ = self.image_.rotate(int(angle))
        transpose_index = self.comboBox_transpose.currentIndex()
        if transpose_index == 1:
            self.image_ = self.image_.transpose(Image.FLIP_TOP_BOTTOM)
        elif transpose_index == 2:
            self.image_ = self.image_.transpose(Image.FLIP_LEFT_RIGHT)
        opt_way = self.comboBox_opt_way.currentIndex()
        if opt_way == 1:  # 模糊
            self.image_ = self.image_.filter(ImageFilter.BLUR)
        elif opt_way == 2:  # 平滑
            self.image_ = self.image_.filter(ImageFilter.SMOOTH)
        elif opt_way == 3:  # 平滑+
            self.image_ = self.image_.filter(ImageFilter.SMOOTH_MORE)
        elif opt_way == 4:  # 锐化
            self.image_ = self.image_.filter(ImageFilter.SHARPEN)
        elif opt_way == 5:  # 浮雕
            self.image_ = self.image_.filter(ImageFilter.EMBOSS)
        elif opt_way == 6:  # 素描
            self.image_ = self.image_.filter(ImageFilter.CONTOUR)
        elif opt_way == 7:  # 细节
            self.image_ = self.image_.filter(ImageFilter.DETAIL)
        elif opt_way == 8:  # 边缘突出
            self.image_ = self.image_.filter(ImageFilter.FIND_EDGES)
        elif opt_way == 9:  # 边缘增强
            self.image_ = self.image_.filter(ImageFilter.EDGE_ENHANCE)
        elif opt_way == 10:  # 边缘增强+
            self.image_ = self.image_.filter(ImageFilter.EDGE_ENHANCE_MORE)


        pixmap = self.pil_to_qpixmap(self.image_)
        scaled_pixmap = pixmap.scaled(
            self.label_opt_pic.width(), self.label_opt_pic.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.label_opt_pic.setPixmap(scaled_pixmap)

    def save_pic(self):
        save_path = self.lineEdit_save_path.text()
        filename = os.path.basename(self.filepath)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        print(os.path.join(save_path, filename))
        try:
            self.image_.save(os.path.join(save_path, filename))
        except Exception as e:
            QMessageBox.warning(self, '保存失败', str(e))
        else:
            QMessageBox.information(self, 'tips', '保存成功!')


    def pil_to_qpixmap(self, pil_img):
        """将PIL Image转换为QPixmap"""
        # 创建内存缓冲区
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        buffer.seek(0)

        # 从缓冲区加载数据到QImage
        qimg = QImage()
        qimg.loadFromData(buffer.read())

        # 转换为QPixmap
        return QPixmap.fromImage(qimg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':res/demo.png'))
    app.setStyle('fusion')
    picture_opt = PictureOpt()
    picture_opt.show()
    sys.exit(app.exec_())
