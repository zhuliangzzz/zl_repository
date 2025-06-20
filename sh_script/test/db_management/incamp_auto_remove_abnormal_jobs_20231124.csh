#! /bin/csh

setenv FRONTLINE_NO_LOGIN_SCREEN "/incampro/server/site_data/scripts/db_management"

cd /frontline/incampro/release/bin
./incampro.csh -x -s/incampro/server/site_data/scripts/db_management/incamp_clean_db_20231124.csh 

