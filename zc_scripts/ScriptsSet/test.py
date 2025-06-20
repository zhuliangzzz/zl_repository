#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:test.py.py
   @author:zl
   @time:2024/6/27 9:23
   @software:PyCharm
   @desc:
"""
from lxml import etree

script_map = {}
with open('cam_config.xml', encoding='utf-8') as r:
    content = r.read()
xml_parser = etree.XMLParser()
fromstring = etree.fromstring(content, parser=xml_parser)
for record in fromstring.findall('RECORD'):
    module = record.find('module_name').text
    name = record.find('script_name').text
    path = record.find('script_path').text
    if not script_map.get(module):
        script_map[module] = []
    script_map[module].append((name, path))

print(script_map)