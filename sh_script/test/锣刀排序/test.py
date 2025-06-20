#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py
   @author:zl
   @time: 2024/12/9 19:03
   @software:PyCharm
   @desc:
"""
import math
from typing import List, Tuple


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """计算两点间的欧几里得距离"""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def find_shortest_path(segments: List[Tuple[Tuple[float, float], Tuple[float, float]]]) -> List[
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


# 测试代码
def main():
    # 示例线段
    # segments = [
    #     ((0, 0), (1, 1)),
    #     ((3, 3), (4, 4)),
    #     ((1, 1), (2, 2)),
    #     ((2, 2), (3, 3))
    # ]
    segments = [((14.75, 11.7), (12.5, 11.7)), ((12.5, 11.7), (12.5, 26.7)), ((18.25, 11.7), (22.75, 11.7)),
                ((22.75, 11.7), (20.5, 11.7)), ((20.5, 11.7), (20.5, 26.7))]

    sorted_segments = find_shortest_path(segments)

    print("原始线段序列:")
    for seg in segments:
        print(f"{seg}")

    print("\n按最短路径排序后的序列:")
    total_distance = 0
    for i, seg in enumerate(sorted_segments):
        print(f"段 {i + 1}: {seg}")
        if i > 0:
            # 计算相邻线段间的连接距离
            prev_end = sorted_segments[i - 1][1]
            curr_start = seg[0]
            segment_distance = distance(prev_end, curr_start)
            total_distance += segment_distance

    print(f"\n总连接距离: {total_distance:.2f}")


if __name__ == "__main__":
    main()
