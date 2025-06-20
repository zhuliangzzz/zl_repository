#!/usr/bin/env python
# -*- coding: utf-8 -*-
__credits__ = u"""解锁料号V1.1.0 """

import re
import sys

jobname = sys.argv[1]

rcs_path = '/incampro/server/increment_config/rcs'
jobname = jobname.replace("+", "\+")
jobname = jobname.replace(".", "\.")
pattern = re.compile(
    "(RCS {\n    NAME=b%s\n    USER=\w+\n    MODE=\d\n    OUT_TIME=\d+\n    IN_TIME=0\n    IS_FROZEN=0\n    FREEZE_USER=\n}\n\n)" % jobname)
lines = file(rcs_path).readlines()
lines_string = "".join(lines)
result = re.findall(pattern, lines_string)

if result:
    print result
    lines_string_new = lines_string.replace(result[0], "")
    with open(rcs_path, "w") as f:
        f.write(lines_string_new)