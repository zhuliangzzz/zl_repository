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

from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage, QIcon, QIntValidator, QCursor, QFont
from PyQt5.QtWidgets import *
from PIL import Image, ImageFilter, ImageEnhance
import qtawesome
# from qtawesome import icon_browser
import PictureOptUI as ui
import res_rc


class PictureOpt(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.image_ = None
        self.filepath = None
        self.pushButton_select_pic.setIcon(qtawesome.icon('fa.folder-open', color='white'))
        self.pushButton_opt.setIcon(qtawesome.icon('mdi.google-photos', color='white'))
        # self.pushButton_opt.setIcon(qtawesome.icon('ei.idea-alt', color='white'))
        self.pushButton_brightness.setIcon(qtawesome.icon('ph.sun-light', color='white'))
        self.pushButton_save.setIcon(qtawesome.icon('fa.save', color='white'))
        self.pushButton_contrast.setIcon(qtawesome.icon('ri.contrast-line', color='white'))
        self.pushButton_union.setIcon(qtawesome.icon('mdi.vector-union', color='white'))
        self.pushButton_blend.setIcon(qtawesome.icon('mdi.source-merge', color='white'))
        self.pushButton_select_pic.clicked.connect(self.select_pic)
        self.lineEdit_rotate.setPlaceholderText('输入旋转角度')
        self.lineEdit_rotate.setValidator(QIntValidator())
        ways = ('不加', '模糊', '平滑', '平滑+', '锐化', '浮雕', '素描', '细节', '边缘突出', '边缘增强', '边缘增强+')
        self.comboBox_opt_way.addItems(ways)
        transposes = ('不翻转', '上下', '左右')
        self.comboBox_transpose.addItems(transposes)
        self.pushButton_opt.clicked.connect(self.opt_)
        self.lineEdit_save_path.setText('./images/generate')
        self.pushButton_save.clicked.connect(self.save_pic)
        # 亮度/对比度 默认是10  对应为1
        self.pushButton_brightness.clicked.connect(lambda: self.horizontalSlider_brightness.setValue(10))
        self.pushButton_contrast.clicked.connect(lambda: self.horizontalSlider_contrast.setValue(10))
        self.horizontalSlider_brightness.valueChanged.connect(self.showBrightness)
        self.horizontalSlider_contrast.valueChanged.connect(self.showContrast)
        # 拼接/融合
        self.pushButton_union.clicked.connect(lambda: self.toggle_clicked('union'))
        self.pushButton_blend.clicked.connect(lambda: self.toggle_clicked('blend'))
        self.setStyleSheet('''QPushButton{font:10pt;background-color:#459B81;color:white;} QPushButton:hover{background:#333;}
        QSlider::groove:horizontal {
        border: 1px solid #bbb;
        background: white;
        height: 10px;
        border-radius: 4px;
         }
    
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1: 0, y1: 0,    x2: 1, y2: 0,
                                        stop: 0 #66e, stop: 1 #bbf);
            background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
                                        stop: 0 #bbf, stop: 1 #55f);
            border: 1px solid #777;
            height: 10px;
            border-radius: 4px;
        }
        
        QSlider::add-page:horizontal {
            background: #fff;
            border: 1px solid #777;
            height: 10px;
            border-radius: 4px;
        }
        
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop:0 #eee, stop:1 #ccc);
            border: 1px solid #777;
            width: 13px;
            margin-top: -2px;
            margin-bottom: -2px;
            border-radius: 4px;
        }
        
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop:0 #fff, stop:1 #ddd);
            border: 1px solid #444;
            border-radius: 4px;
        }
        ''')

    # def run(self):

    def select_pic(self):
        filepath, _ = QFileDialog.getOpenFileName(self, '选择图片', 'images', '*.png *.jpg *.jepg')
        # print(filepath)
        if filepath:
            self.filepath = filepath
            pixmap = QPixmap(filepath)
            scaled_pixmap = pixmap.scaled(
                self.label_origin_pic.width(), self.label_origin_pic.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label_origin_pic.setPixmap(scaled_pixmap)

    def opt_(self):
        self.opt()
        self.render_opt_pic()

    def opt(self):
        if not self.filepath:
            return
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
        # self.render_opt_pic()

    def save_pic(self):
        if self.image_:
            save_path = self.lineEdit_save_path.text()
            filename = os.path.basename(self.filepath)
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            # print(os.path.join(save_path, filename))
            try:
                self.image_.save(os.path.join(save_path, filename))
            except Exception as e:
                QMessageBox.warning(self, '保存失败', str(e))
            else:
                QMessageBox.information(self, 'tips', '保存成功!')

    def showBrightness(self, value):
        # print(value)
        brightness = value / 10
        self.label_brightness.setText(str(brightness))
        if not self.image_:
            return
        self.opt()
        self.image_ = ImageEnhance.Brightness(self.image_)
        self.image_ = self.image_.enhance(brightness)
        contrast = float(self.label_contrast.text())
        if contrast != 1:
            self.image_ = ImageEnhance.Contrast(self.image_)
            self.image_ = self.image_.enhance(contrast)
        self.render_opt_pic()

    def showContrast(self, value):
        contrast = value / 10
        self.label_contrast.setText(str(contrast))
        if not self.image_:
            return
        self.opt()
        self.image_ = ImageEnhance.Contrast(self.image_)
        self.image_ = self.image_.enhance(contrast)
        brightness = float(self.label_brightness.text())
        if brightness != 1:
            self.image_ = ImageEnhance.Brightness(self.image_)
            self.image_ = self.image_.enhance(brightness)
        self.render_opt_pic()

    def render_opt_pic(self):
        if not self.image_:
            return
        self.pushButton_opt.setEnabled(False)
        self.pushButton_opt.setText('优化中...')
        self.processor = ImageProcessor(
            image=self.image_,
            target_size=(self.label_opt_pic.width(), self.label_opt_pic.height())
        )
        self.processor.image_ready.connect(self.update_image)
        self.processor.finished.connect(lambda: self.pushButton_opt.setEnabled(True))
        self.processor.start()

        # self.label_opt_pic.update()
        # app.processEvents()

    def update_image(self, pixmap):
        self.label_opt_pic.setPixmap(pixmap)
        self.pushButton_opt.setText('优化')

    def toggle_clicked(self, t):
        window = select_pic_window(self, t)
        if t == 'union':
            window.signal_to_parent.connect(self.unionPic)
        else:
            window.signal_to_parent.connect(self.blendPic)
        window.exec_()

    def unionPic(self, pics):
        print(pics)
        ims, filenames = [], []
        for pic in pics:
            filenames.append(os.path.basename(pic))
            im = Image.open(pic)
            ims.append(im)
        width = max([im.width for im in ims])
        union_pics = []
        for im in ims:
            if im.width != width:
                im = im.resize((width, int(im.height * width / im.width)))
            union_pics.append(im)
        height = sum([pic.height for pic in union_pics])
        new_im = Image.new('RGB', (width, height))
        h_position = 0
        for union_pic in union_pics:
            new_im.paste(union_pic, (0, h_position))
            h_position += union_pic.height
        save_path = self.lineEdit_save_path.text()
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        filename = '_'.join([name.rsplit('.')[0].replace('.', '') for name in filenames]) + '.png'
        try:
            new_im.save(os.path.join(save_path, filename))
        except Exception as e:
            QMessageBox.warning(self, '保存失败', str(e))
        else:
            QMessageBox.information(self, 'tips', '保存成功!')

    def blendPic(self, args):
        print('blend', args)
        ims, filenames = [], []
        pics, alpha = args[0], args[-1]
        for pic in pics:
            filenames.append(os.path.basename(pic))
            im = Image.open(pic).convert('RGBA')
            ims.append(im)
        width = max([im.width for im in ims])
        blend_pics = []
        for im in ims:
            if im.width != width:
                im = im.resize((width, int(im.height * width / im.width)))
            blend_pics.append(im)
        result = blend_pics[0]
        # 逐张混合剩余图片
        for i in range(1, len(blend_pics)):
            img = blend_pics[i]
            result = Image.blend(result, img, alpha)
        save_path = self.lineEdit_save_path.text()
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        filename = '_'.join([name.rsplit('.')[0].replace('.', '') for name in filenames]) + '.png'
        try:
            result.save(os.path.join(save_path, filename))
        except Exception as e:
            QMessageBox.warning(self, '保存失败', str(e))
        else:
            QMessageBox.information(self, 'tips', '保存成功!')


class select_pic_window(QDialog):
    # 定义自定义信号，带一个str类型参数
    signal_to_parent = pyqtSignal(list)

    def __init__(self, parent, type):
        super().__init__(parent)
        self.type = type
        self.render()

    def render(self):
        self.setWindowTitle('Select Pictures')
        self.resize(340, 300)
        layout = QVBoxLayout(self)
        # combo = QComboBox(self)
        # self.label = QLabel('Selected Picture(s):')
        self.line_input = QPushButton('选择图片')
        self.line_input.setCursor(QCursor(Qt.PointingHandCursor))
        self.line_input.clicked.connect(self.select_pic)
        self.listWidget = QListWidget()
        self.listWidget.setAcceptDrops(True)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setDragDropMode(QAbstractItemView.DragDrop)
        # self.listWidget.setSelectionMode(QHeaderView.NoSelection)
        # self.listWidget1.setSelectionMode(QAbstractItemView.ExtendedSelection)  # 不设置拖多个 容易出错
        self.listWidget.setDefaultDropAction(Qt.MoveAction)
        #
        h_box = QHBoxLayout()
        self.label = QLabel('混合程度:')
        # 创建 QSpinBox 实例
        self.spin_box = QDoubleSpinBox()
        # 设置范围和精度
        self.spin_box.setMinimum(0)  # 最小值 0
        self.spin_box.setMaximum(1)  # 最大值 1
        self.spin_box.setValue(0.5)
        self.spin_box.setSingleStep(0.1)  # 单步增量（可按需调整，如 0.01）
        self.spin_box.setDecimals(1)
        h_box.addWidget(self.label)
        h_box.addWidget(self.spin_box)
        #
        layout.addWidget(self.line_input)
        layout.addWidget(self.listWidget)
        if self.type == 'blend':
            layout.addLayout(h_box)
        btn_box = QHBoxLayout()
        ok = QPushButton()
        ok.setText('OK')
        ok.setStyleSheet('background-color:#459B81;color:white;')
        ok.setObjectName('dialog_ok')
        ok.setMaximumSize(QSize(50, 16777215))
        ok.setCursor(QCursor(Qt.PointingHandCursor))
        ok.clicked.connect(self.set_select_value)
        close = QPushButton()
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white;')
        close.setObjectName('dialog_close')
        close.setMaximumSize(QSize(50, 16777215))
        close.setCursor(QCursor(Qt.PointingHandCursor))
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addLayout(btn_box)
        self.setStyleSheet('''*{font-family:微软雅黑;font-size:10pt;}
        QListWidget::Item{height:22px;} QListWidget::Item:selected{background-color:#459B81;}
        ''')

    def select_pic(self):
        filepath, _ = QFileDialog.getOpenFileNames(self, '选择图片', 'images', '*.png *.jpg *.jepg')
        if filepath:
            self.listWidget.addItems(filepath)

    def set_select_value(self):
        # print(self.listWidget.count())
        select_pic_list = []
        if self.listWidget.count():
            select_pic_list = [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
            if self.type == 'union':
                self.signal_to_parent.emit(select_pic_list)
            else:
                self.signal_to_parent.emit([select_pic_list, self.spin_box.value()])
        else:
            return
        self.close()


# 图片生成
class ImageProcessor(QThread):
    """后台处理图像的线程"""
    image_ready = pyqtSignal(QPixmap)  # 处理完成后发送的信号

    def __init__(self, image, target_size=None):
        super().__init__()
        self.opt_image = QImage().convertToFormat(QImage.Format_RGB32)
        self.image = image
        self.target_size = target_size

    def run(self):
        """线程执行的主要逻辑"""
        try:
            pixmap = self.pil_to_qpixmap(self.image)
            scaled_pixmap = pixmap.scaled(
                *self.target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            # 转换为QPixmap并发送信号
            # pixmap = QPixmap.fromImage(scaled_pixmap)
            self.image_ready.emit(scaled_pixmap)

        except Exception as e:
            print(f"图像处理错误: {e}")

    def pil_to_qpixmap(self, pil_img):
        """将PIL Image转换为QPixmap"""
        # 创建内存缓冲区
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        buffer.seek(0)
        # 从缓冲区加载数据到QImage
        self.opt_image.loadFromData(buffer.read())
        # 转换为QPixmap
        return QPixmap.fromImage(self.opt_image)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':res/demo.png'))
    app.setStyle('fusion')
    picture_opt = PictureOpt()
    picture_opt.show()
    sys.exit(app.exec_())
