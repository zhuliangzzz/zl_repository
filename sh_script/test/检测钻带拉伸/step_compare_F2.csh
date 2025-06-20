#!/bin/csh
#################################################
#scripts:scripts windows
#author: chris
#date:2015.08.18
#purpose:
#################################################
setenv GENESIS_DIR /incam/server
setenv GENESIS_EDIR /incam/release
perl $GENESIS_DIR/sys/scripts/sh_script/step_compare/step_compare_F2.pl
exit