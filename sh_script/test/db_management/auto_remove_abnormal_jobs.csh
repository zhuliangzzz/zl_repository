#! /bin/csh

setenv FRONTLINE_NO_LOGIN_SCREEN "/incam/server/site_data/scripts/db_management/"

cd /incam/release/bin
#./incam.csh -x -s/incam/server/site_data/scripts/hdi_scr/Sys/bak_jobs/clean_db.csh 
./incam.csh -x -s/incam/server/site_data/scripts/db_management/clean_db.csh 

