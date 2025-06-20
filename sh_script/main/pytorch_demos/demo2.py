#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:demo2.py
   @author:zl
   @time: 2025/4/12 13:58
   @software:PyCharm
   @desc:
"""
import torch

tensor = torch.tensor([[1, 2, 3], [4, 5, 6]], dtype=torch.float32)
print('原始张量：\n', tensor)

print('\n【切片和索引】')
print('获取第一行：', tensor[0])
print('获取第一行第一列的元素：', tensor[0, 0])
print('获取第二列的所有元素：', tensor[:, 1])

print('\n【形状变换】')
reshaped = tensor.view(3, 2)
print('改变形状后的张量：\n', reshaped)
flattened = tensor.flatten()
print('展平后的张量：\n', flattened)

print('\n【数学运算】')
tensor_add = tensor + 10
print('张量加10：\n', tensor_add)
tensor_mul = tensor * 2
print('张量乘2：\n', tensor_mul)
tensor_sum = tensor.sum()
print('张量元素的和：', tensor_sum.item())

print('\n【与其他张量操作】')
tensor2 = torch.tensor([[1, 1, 1], [1, 1, 1]], dtype=torch.float32)
print('另一个张量：\n', tensor2)
tensor_dot = torch.matmul(tensor, tensor2.T)
print('张量乘法结果\n', tensor_dot)

print('\n【条件判断和筛选】')
mask = tensor > 3
print('大于3的元素的布尔掩码：\n', mask)
filtered_tensor = tensor[tensor > 3]
print('大于3的元素：\n', filtered_tensor)
print(torch.cuda.is_available())
device = torch.device('cuda')
x = torch.tensor([1.0, 2.0, 3.0], device=device)
print(x)