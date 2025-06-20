#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:RoutSort.py
   @author:zl
   @time: 2024/12/10 9:24
   @software:PyCharm
   @desc:
"""
import math
import os
import sys
from typing import List, Tuple

import qtawesome
from PyQt5.QtWidgets import QWidget, QApplication, QAbstractItemView, QMessageBox
from PyQt5.QtGui import QIcon
import RoutSortUI as ui
import res_rc
import genClasses as gen


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """计算两点间的欧几里得距离"""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


class RoutSort(QWidget, ui.Ui_Form):
    def __init__(self):
        super(RoutSort, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        rout_list = job.matrix.returnRows('board', 'rout')
        self.label.setText('Job:%s Step:%s' % (jobname, stepname))
        self.listWidget.addItems(rout_list)
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.comboBox_sort_way.addItems(['S型', '最近'])
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.setStyleSheet(
            '''
            QListWidget::Item{height:26px;border-radius:1.5px;} QMessageBox{font-size:10pt;} QListWidget::Item:selected{background:#459B81;color:white;}
            QPushButton{font:10pt;background-color:#459B81;color:white;} QPushButton:hover{background:#333;}''')

    def exec(self):
        rout_layers = [item.text() for item in self.listWidget.selectedItems()]
        if not rout_layers:
            QMessageBox.warning(None, 'tips', '请选择层')
            return
        sort_index = self.comboBox_sort_way.currentIndex()
        step = gen.Step(job, stepname)
        step.initStep()
        step.affect('a')
        step.selectAll()
        layerObj = gen.Layer(step, 'a')
        feats = layerObj.featout_dic_Index(options="select+feat_index", units='mm')
        segments = []
        for t in feats:
            if t == 'lines':
                for feat in feats.get(t):
                        segments.append(((feat.xs, feat.ys), (feat.xe, feat.ye)))
        if sort_index == 0:
            sorted_segments = self.snake_sort_segments(segments)
        else:
            sorted_segments = self.find_shortest_path(segments)
        print(sorted_segments)
        step.unaffectAll()
        step.removeLayer('b')
        step.createLayer('b')
        step.affect('b')
        i = 1
        for segment in sorted_segments:
            step.addText((segment[0][0] + segment[1][0]) / 2, (segment[0][1] + segment[1][1]) / 2, i, 0.5,0.5, 0.2)
            i += 1

    @classmethod
    def find_shortest_path(cls, segments: List[Tuple[Tuple[float, float], Tuple[float, float]]]) -> List[
        Tuple[Tuple[float, float], Tuple[float, float]]]:
        """找出线段的最短连接路径"""
        if not segments:
            return []

        # 复制输入列表，避免修改原始数据
        remaining = segments.copy()
        path = []

        # 选择第一个线段作为起点
        current = remaining.pop(0)
        path.append(current)
        current_end = current[1]

        while remaining:
            min_distance = float('inf')
            next_segment = None
            should_flip = False

            # 遍历剩余线段，找到最近的下一段
            for segment in remaining:
                # 检查连接到起点的距离
                dist_to_start = distance(current_end, segment[0])
                dist_to_end = distance(current_end, segment[1])

                # 选择较短的连接方式
                if dist_to_start < min_distance:
                    min_distance = dist_to_start
                    next_segment = segment
                    should_flip = False

                if dist_to_end < min_distance:
                    min_distance = dist_to_end
                    next_segment = segment
                    should_flip = True

            # 添加找到的最近线段
            if should_flip:
                # 如果需要翻转线段
                path.append((next_segment[1], next_segment[0]))
                current_end = next_segment[0]
            else:
                path.append(next_segment)
                current_end = next_segment[1]

            remaining.remove(next_segment)

        return path

    # @classmethod
    # def snake_sort(cls, coordinates):
    #     if not coordinates:
    #         return []
    #
    #     # 1. 按y坐标分组
    #     y_groups = {}
    #     for x, y in coordinates:
    #         y_groups.setdefault(y, []).append(x)
    #
    #     # 2. 对y坐标排序
    #     sorted_y = sorted(y_groups.keys())
    #
    #     # 3. 按S型路径排序
    #     result = []
    #     for i, y in enumerate(sorted_y):
    #         x_coords = y_groups[y]
    #         # 偶数行从左到右，奇数行从右到左
    #         if i % 2 == 0:
    #             x_coords.sort()
    #         else:
    #             x_coords.sort(reverse=True)
    #
    #         # 将排序后的坐标加入结果
    #         for x in x_coords:
    #             result.append((x, y))
    #
    #     return result

    @classmethod
    def snake_sort_segments(cls, segments):
        # Sort segments by the y-coordinate of the starting point, then by x-coordinate
        segments.sort(key=lambda s: (s[0][1], s[0][0]))

        # Determine the maximum y-coordinate to know the number of rows
        max_y = max(segments, key=lambda s: s[0][1])[0][1]

        # Create a dictionary to hold segments by row
        rows = {}
        for segment in segments:
            y = segment[0][1]
            if y not in rows:
                rows[y] = []
            rows[y].append(segment)

        # Sort each row in snake order
        sorted_segments = []
        for y in sorted(rows.keys()):
            if int(y) % 2 == 0:
                # Even row: left to right
                sorted_segments.extend(sorted(rows[y], key=lambda s: s[0][0]))
            else:
                # Odd row: right to left
                sorted_segments.extend(sorted(rows[y], key=lambda s: s[0][0], reverse=True))

        return sorted_segments



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    jobname = os.environ.get('JOB')
    if not jobname:
        QMessageBox.warning(None, 'tips', '请打开料号！')
        sys.exit()
    job = gen.Job(jobname)
    stepname = 'set'
    if stepname not in job.steps:
        QMessageBox.warning(None, 'tips', '没有set！')
        sys.exit()
    routSort = RoutSort()
    routSort.show()
    sys.exit(app.exec_())
