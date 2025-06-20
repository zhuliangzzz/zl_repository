#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:demo5.py
   @author:zl
   @time: 2025/4/21 17:13
   @software:PyCharm
   @desc:
"""
import torch
import matplotlib.pyplot as plt

n_samples = 100

data = torch.randn(n_samples, 2)
print(data)
labels = (data[:,0]**2 + data[:,1]**2 < 1).float().unsqueeze(1)
print(labels)
# 可视化数据
plt.scatter(data[:, 0], data[:, 1], c=labels.squeeze(), cmap='coolwarm')
plt.title("Generated Data")
plt.xlabel("Feature 1")
plt.ylabel("Feature 2")
plt.show()



