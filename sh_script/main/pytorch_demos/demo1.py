#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:demo1.py
   @author:zl
   @time: 2025/4/12 13:55
   @software:PyCharm
   @desc:
"""
import torch

tensor_2d = torch.tensor([
    [-9, 4, 2, 5, 7],
    [3, 0, 12, 8, 6],
    [1, 23, -6, 45, 2],
    [22, 3, -1, 72, 6]
])

print('2D Tensor (Matrix):\n', tensor_2d)
print('Shape:', tensor_2d.shape)

tensor_3d = torch.stack([tensor_2d, tensor_2d + 10, tensor_2d - 5])
print('3D Tensor (Cube):\n', tensor_3d)
print('Shape:', tensor_3d.shape)
print('Size:', tensor_3d.size())
print('Type:', tensor_3d.dtype)
print(tensor_3d.device)
print(tensor_3d.numel())
print(tensor_3d.is_cuda)
print(tensor_3d.is_contiguous())
tensor = torch.tensor([[1, 2, 3], [4, 5, 6]], dtype=torch.float32)
single_value = torch.tensor(42)
print(single_value)
print(single_value.item())
tensor_t = tensor.T
print('Transposed Tensor (Tensor):\n', tensor_t)