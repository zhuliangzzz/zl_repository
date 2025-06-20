#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:snake_rout.py
   @author:zl
   @time: 2024/12/10 9:10
   @software:PyCharm
   @desc:
"""


def snake_sort(coordinates):
    if not coordinates:
        return []

    # 1. 按y坐标分组
    y_groups = {}
    for x, y in coordinates:
        y_groups.setdefault(y, []).append(x)

    # 2. 对y坐标排序
    sorted_y = sorted(y_groups.keys())

    # 3. 按S型路径排序
    result = []
    for i, y in enumerate(sorted_y):
        x_coords = y_groups[y]
        # 偶数行从左到右，奇数行从右到左
        if i % 2 == 0:
            x_coords.sort()
        else:
            x_coords.sort(reverse=True)

        # 将排序后的坐标加入结果
        for x in x_coords:
            result.append((x, y))

    return result


# 测试代码
coordinates = [((14.75, 11.7), (12.5, 11.7)), ((12.5, 11.7), (12.5, 26.7)), ((18.25, 11.7), (22.75, 11.7)),
               ((22.75, 11.7), (20.5, 11.7)), ((20.5, 11.7), (20.5, 26.7))]
sorted_coords = snake_sort(coordinates)
print("S型排序结果:", sorted_coords)