#! /bin/csh

set perl_path = '/opt/ActivePerl-5.14/bin/perl'
if (-e "/opt/ActivePerl-5.14_bak") then
   set perl_path = '/opt/ActivePerl-5.14_bak/bin/perl'
endif
$perl_path /incam/server/site_data/scripts/sh_script/LayerNetCompare/NetlistCompare.pl -run ipc -steps orig -input_group

# /id/server/site_data/scripts/Input_Guide/RunExe.cshrc $InputGuidePath/NetlistCompare.Neo -run ipc -steps orig -input_group
