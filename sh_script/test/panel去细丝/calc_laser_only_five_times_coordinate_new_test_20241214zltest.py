#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20240104"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""计算镭射分割坐标以及打五遍 """

import sys
import os
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")    
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import re
from genesisPackages import job
from create_ui_model import showMessageInfo 

filepath_write, filepath_fg, five_str = sys.argv[1:]


five_drill_size = []
if str(five_str) != 'no':
    five_drill_size = ['%.3f' % (float(i)/1000) for i in str(five_str).split('_')]

print str(five_str)
print five_drill_size
print ">>>>>>>>>>>>>>>>>>>"

class modify_fg_laser_drill(object):
    
    def __init__(self):
        pass

    def rewrite_five_times_info(self):
        """打五遍的信息"""
        
        header_info = []
        
        # lines_fg = file(filepath_fg).readlines()
        # job.PAUSE(filepath_write)
        lines_write = file(filepath_write).readlines()
        headerIndex = lines_write.index('%\n')
        Holes_size_write = {}
        for i in range(headerIndex):
            if re.match('^T.*', lines_write[i]):
                result = re.findall("(^T\d+)C(.*)", lines_write[i])
                if result:
                    if round(float(result[0][1])*1000, 1) in Holes_size_write.keys():
                        # T23 跟板内孔一致是 先加大5000
                        Holes_size_write[round(float(result[0][1])*1000, 1)+5000] = [result[0][0], result[0][0]]
                        lines_write[i] = result[0][0] + "C{0}\n".format(5+float(result[0][1]))
                    else:
                        Holes_size_write[round(float(result[0][1])*1000, 1)] = [result[0][0], result[0][0]]                   

        dic_t_header_index = {}
        new_array_t_header = []
        for i, line in enumerate(lines_write):
            if re.match('^T.*', line) and i <= headerIndex:
                result = re.findall("^T(\d+)C(.*)", line)
                if float(result[0][1]) in (0.203, 0.204, 0.229, 0.230, 0.241, 0.242, 0.216, 0.217):
                    if result[0][1] in five_drill_size:
                        run_num = 5
                    else:
                        run_num = 1
                    print
                    print run_num
                    print "kkkkkkkkkkkkkkkkkk"
                    for num in range(run_num):
                        header_size = float(result[0][1]) + 0.001 * num
                        # t_num = int(result[0][0]) + num
                        # 按新工艺文件要求 8mil孔固定5-9 20240116 by lyh
                        t_num = 5 + num
                        
                        new_t_header = "T{0}C{1}".format(str(t_num).rjust(2, "0"), header_size)
                        dic_t_header_index[new_t_header] = t_num
                        header_info.append(new_t_header+"\n")
                        
                        new_array_t_header.append("T{0}".format(str(t_num).rjust(2, "0")))                            
                        Holes_size_write[round(float(header_size)*1000, 1)] = ["T{0}".format(str(t_num).rjust(2, "0")), "T" + result[0][0]]
                        
                elif float(result[0][1]) in (0.254, 0.255):
                    if result[0][1] in five_drill_size:
                        run_num = 5
                    else:
                        run_num = 1

                    for num in range(run_num):
                        header_size = float(result[0][1]) + 0.001 * num
                        # 按新工艺文件要求 10mil孔固定15-19 20240111 by lyh
                        # if int(hole_size_num) >= 2:                                
                        t_num = 15 + num
                        #else:
                            #t_num = int(result[0][0]) + num
                            
                        new_t_header = "T{0}C{1}".format(str(t_num).rjust(2, "0"), header_size)
                        dic_t_header_index[new_t_header] = t_num
                        header_info.append(new_t_header+"\n")
                        
                        new_array_t_header.append("T{0}".format(str(t_num).rjust(2, "0")))
                        Holes_size_write[round(float(header_size)*1000, 1)] = ["T{0}".format(str(t_num).rjust(2, "0")), "T" + result[0][0]]
                        
                else:
                    # print(result)
                    # print(header_info)
                    # print(dic_t_header_index)
                    # print(result[0][0])
                    # print(header_info)
                    if "T{0}C".format(result[0][0]) in "".join(header_info):
                        header_size = float(result[0][1])
                        # print(dic_t_header_index)
                        # print("key", header_info[-1].strip())
                        # t_num = dic_t_header_index[header_info[-1].strip()] + 1
                        t_num = 11  # 20241214 写死固定11
                        new_t_header = "T{0}C{1}".format(str(t_num).rjust(2, "0"), header_size-5 if  header_size > 5 else header_size)
                        dic_t_header_index[new_t_header] = t_num
                        header_info.append(new_t_header+"\n")
                        
                        new_array_t_header.append("T{0}".format(str(t_num).rjust(2, "0")))                     
                        Holes_size_write[round(float(header_size)*1000, 1)] = ["T{0}".format(str(t_num).rjust(2, "0")), "T" + result[0][0]]
                        
                    else:
                        header_size = float(result[0][1])
                        new_t_header = "T{0}C{1}".format(result[0][0], header_size-5 if  header_size > 5 else header_size)                        
                        header_info.append(new_t_header+"\n")
                        
                        new_array_t_header.append("T{0}".format(result[0][0]))
                    # print(new_array_t_header)
                    # print(header_info)
            else:
                if i <= headerIndex:
                    header_info.append(line)
                    
            if len(new_array_t_header) != len(set(new_array_t_header)):
                os.unlink(filepath_fg)
                showMessageInfo(u"打五遍排刀异常，请反馈程序工程师处理：", *[x.decode("utf8") for x in header_info])
                # os.rename(filepath_fg, filepath_fg+"_new")                
                sys.exit()
                
        headerIndex = lines_write.index('%\n')
        Holes_T = []
        Holes_size = {}
        for i in range(headerIndex):
            if re.match('^T.*', lines_write[i]):
                result = re.findall("(^T\d+)C(.*)", lines_write[i])
                if result:
                    Holes_T.append(result[0][0])
                    Holes_size[result[0][0]] = round(float(result[0][1]) *1000, 1)
                   
        Holes_T_body = {}
        for i, line in enumerate(lines_write):
            if i >= headerIndex:
                if line == '%\n':
                    key = "T01"
                elif line.strip() in Holes_T:
                    key = line.strip()
                if line == 'M30\n':
                    break
                
                if key:                    
                    if Holes_T_body.has_key(key):
                        Holes_T_body[key].append(line)
                    else:
                        Holes_T_body[key] = []        
        
        print Holes_size
        print Holes_size_write
        print Holes_T_body.keys()
        print(header_info)
        arraylist_body = []
        for key in new_array_t_header:            
            for size,values in Holes_size_write.iteritems():                
                t_header,body_header = Holes_size_write[size]
                if t_header == key:                    
                    print(t_header,body_header)
                    values = Holes_T_body[body_header] 
                    if t_header <> "T01":                    
                        arraylist_body.append(t_header+"\n")
                        
                    arraylist_body += values
                
        with open(filepath_write, "w") as f:
            f.write("".join(header_info))
            f.write("".join(arraylist_body))
            f.write("M30\n")
                       
        # os.rename(filepath_fg, filepath_fg+"_new")
        # os.unlink(filepath_fg)
        # sys.exit(5)
            
if __name__ == '__main__':    
    main = modify_fg_laser_drill()
    main.rewrite_five_times_info()

