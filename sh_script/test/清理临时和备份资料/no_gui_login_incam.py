#!/usr/bin/env python
# -*- coding: utf-8 -*-

# write by LYH 20191025
__author__  = "luthersy"
__date__ = "20191025"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""无界面登录incam"""

import sys
import os
os.environ["FRONTLINE_NO_LOGIN_SCREEN"] = "/incam/server/site_data/scripts/db_management"
try:
    os.unlink("/incam/server/site_data/scripts/db_management/login.enc")
except:
    pass

for arg in sys.argv[1:]:    
    if os.environ.get("GEN_LOGIN_USER_{0}".format(arg.upper()), None):
        os.environ["FRONTLINE_NO_LOGIN_SCREEN"] = "/tmp/{0}/.genesis".format(os.environ["GEN_LOGIN_USER_{0}".format(arg.upper())])

try:
    scripts_path = sys.argv[1:]
except:
    # 测试
    scripts_path = ["W:/genesis/sys/scripts/suntak/auto_tools/Check_Area/Auto_Check_Exposed_Area_lyh_incam.pl"]

# setenv NCC_SMART_SNAP_OFF; setenv INCAM_LANG c
os.environ["NCC_SMART_SNAP_OFF"] = ""
os.environ["INCAM_LANG"] = "c"

if "no_gui" in scripts_path:    
    # 无界面登录
    cmd = "/frontline/incampro_output/release/bin" + "/incampro.csh" + \
        " -x -s" + " ".join(scripts_path)
    if os.environ.get("INCAM_PRODUCT"):
        cmd = "{0}/bin".format(os.environ.get("INCAM_PRODUCT")) + "/incampro.csh" + \
            " -x -s" + " ".join(scripts_path)        
else:    
    # 有界面登录
    cmd = "/frontline/incampro_output/release/bin" + "/incampro.csh" + \
        " -s" + " ".join(scripts_path)
    if os.environ.get("INCAM_PRODUCT"):
        cmd = "{0}/bin".format(os.environ.get("INCAM_PRODUCT")) + "/incampro.csh" + \
            " -s" + " ".join(scripts_path)      
    
if os.path.exists(scripts_path[0]):
    if os.environ.get("VNCDISP", None):
        os.system("vnc.so "+cmd.replace("incampro.csh", "incampro2.csh"))
    else:
        os.system(cmd)
else:
    print("{0} not exists!".format(scripts_path))