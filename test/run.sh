#!/usr/bin/env bash

## IMPORTANT: Only run this script from the directory it resides in, i.e. with
##             ./run.sh    OR    bash run.sh

##===========================================================================##
## This script contains hardwired information necessary for this algorithm's
##  delivery to and testing within the SDPS (Science Data Processing System).
##
## ** In general, do not push changes to this file to its primary git
##     repository (exceptions include adding a new environment var for
##     algorithm config) **
##
## ++ Instead, make a LOCAL copy of this script (e.g., my_run_m4.sh; do not
##     push that local copy to the primary git repository either) and modify
##     and run that for general algorithm testing and development.
##===========================================================================##

set -ve;  # Exit on the first error, and print out commands as we execute them
#set -e;  # Exit on the first error

for script in run_m0.sh
do
  ./$script;
  if [ $? -ne 0 ]; then 
     echo "ERROR: $script exited with status code $?";
  fi
done
