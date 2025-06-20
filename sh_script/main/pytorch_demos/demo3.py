#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:demo3.py
   @author:zl
   @time: 2025/4/14 14:57
   @software:PyCharm
   @desc:
"""
# 定义一个简单的神经网络模型
import torch
import torch.nn as nn
class SimpleNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(2,2)
        self.fc2 = nn.Linear(2, 1)

    def forward(self, x):
        # 向前传播
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

model = SimpleNN()
print(model)