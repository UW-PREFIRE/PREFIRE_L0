#!/usr/bin/env bash

## IMPORTANT: Only run this script from the directory it resides in, i.e. with
##             ./run_m5.sh    OR    bash run_m5.sh

##===========================================================================##
## This script contains hardwired information necessary for this algorithm's
##  delivery to and testing within the SDPS (Science Data Processing System).
##
## ** In general, do not push changes to this file to its primary git
##     repository (exceptions include adding a new environment var for
##     algorithm config) **
##
## ++ Instead, make a LOCAL copy of this script (e.g., my_run_m5.sh; do not
##     push that local copy to the primary git repository either) and modify
##     and run that for general algorithm testing and development.
##===========================================================================##

absfpath() {
  # Generate absolute filepath from a relative (or even an absolute) filepath.
  #
  # Based on (circa Oct 2023) https://stackoverflow.com/questions/3915040/how-to-obtain-the-absolute-path-of-a-file-via-shell-bash-zsh-sh
  # 
  # $1     : a relative (or even an absolute) filepath
  # Returns the corresponding absolute filepath.
  if [ -d "$1" ]; then
    # dir
    (cd "$1"; pwd)
  elif [ -f "$1" ]; then
    # file
    if [[ $1 = /* ]]; then
      echo "$1"
    elif [[ $1 == */* ]]; then
      echo "$(cd "${1%/*}"; pwd)/${1##*/}"
    else
      echo "$(pwd)/$1"
    fi
  fi
}

activate_conda_env () {
  . "$1"/bin/activate;
}

deactivate_conda_env () {
  . "$1"/bin/deactivate;
}

#set -ve;  # Exit on the first error, and print out commands as we execute them
set -e;  # Exit on the first error

# Determine the absolute path of the current working directory:
#  (this is typically the package test/ directory)
readonly base_dir="$(absfpath ".")";

hn=`hostname -s`;  # Hostname

# NOTE: Set the input/output directories to absolute paths (relative to the
#        current working directory, 'base_dir').

non_SDPS_hostname="longwave";

L0_dir="${base_dir}/inputs";

L0ocs1="PREFIRE-SAT1,2024-10-17T03:00:00Z";
L0ocs2="PREFIRE-SAT1,2024-10-17T04:00:00Z";
L0ocs3="PREFIRE-SAT1,2024-10-17T05:00:00Z";
L0ocs4="PREFIRE-SAT1,2024-10-17T06:00:00Z";
L0ocs5="PREFIRE-SAT1,2024-10-17T07:00:00Z";
L0ocs6="PREFIRE-SAT1,2024-10-17T08:00:00Z";
L0ocs7="PREFIRE-SAT1,2024-10-17T09:00:00Z";
L0ocs8="PREFIRE-SAT1,2024-10-17T10:00:00Z";
L0ocs9="PREFIRE-SAT1,2024-10-17T11:00:00Z";
L0ocs10="PREFIRE-SAT1,2024-10-17T12:00:00Z";
L0ocs11="PREFIRE-SAT1,2024-10-17T13:00:00Z";
L0ocs12="PREFIRE-SAT1,2024-10-17T14:00:00Z";
L0ocs13="PREFIRE-SAT1,2024-10-17T15:00:00Z";
L0ocs14="PREFIRE-SAT1,2024-10-17T16:00:00Z";
L0ocs15="PREFIRE-SAT1,2024-10-17T17:00:00Z";
L0ocs16="PREFIRE-SAT1,2024-10-17T18:00:00Z";
L0ocs17="PREFIRE-SAT1,2024-10-17T19:00:00Z";
L0ocs18="PREFIRE-SAT1,2024-10-17T20:00:00Z";
L0ocs19="PREFIRE-SAT1,2024-10-17T21:00:00Z";

L0ocs20="PREFIRE-SAT2,2024-10-09T02:00:00Z";
L0ocs21="PREFIRE-SAT2,2024-10-09T03:00:00Z";
L0ocs22="PREFIRE-SAT2,2024-10-09T04:00:00Z";
L0ocs23="PREFIRE-SAT2,2024-10-09T05:00:00Z";
L0ocs24="PREFIRE-SAT2,2024-10-09T06:00:00Z";
L0ocs25="PREFIRE-SAT2,2024-10-09T07:00:00Z";
L0ocs26="PREFIRE-SAT2,2024-10-09T08:00:00Z";
L0ocs27="PREFIRE-SAT2,2024-10-09T09:00:00Z";
L0ocs28="PREFIRE-SAT2,2024-10-09T10:00:00Z";
L0ocs29="PREFIRE-SAT2,2024-10-09T11:00:00Z";
L0ocs30="PREFIRE-SAT2,2024-10-09T12:00:00Z";
L0ocs31="PREFIRE-SAT2,2024-10-09T13:00:00Z";
L0ocs32="PREFIRE-SAT2,2024-10-09T14:00:00Z";
L0ocs33="PREFIRE-SAT2,2024-10-09T15:00:00Z";
L0ocs34="PREFIRE-SAT2,2024-10-09T16:00:00Z";
L0ocs35="PREFIRE-SAT2,2024-10-09T17:00:00Z";
L0ocs36="PREFIRE-SAT2,2024-10-09T18:00:00Z";
L0ocs37="PREFIRE-SAT2,2024-10-09T19:00:00Z";
L0ocs38="PREFIRE-SAT2,2024-10-09T20:00:00Z";
L0ocs39="PREFIRE-SAT2,2024-10-09T21:00:00Z";


# Specify that numpy, scipy, et cetera should not use more than one thread or
#  process):
MKL_NUM_THREADS=1;
NUMEXPR_NUM_THREADS=1;
OMP_NUM_THREADS=1;
VECLIB_MAXIMUM_THREADS=1;
OPENBLAS_NUM_THREADS=1;
export MKL_NUM_THREADS NUMEXPR_NUM_THREADS OMP_NUM_THREADS;
export VECLIB_MAXIMUM_THREADS OPENBLAS_NUM_THREADS;

# Some environment vars that convey configuration info to the algorithm:

this_top_dir="$(absfpath "${base_dir}/..")";

PACKAGE_TOP_DIR="${this_top_dir}";
ANCILLARY_DATA_DIR="${this_top_dir}/dist/ancillary";

OUTPUT_DIR="${base_dir}/outputs/m5";

PROC_MODE=5;

PRODUCT_FULLVER="P01_R00";  # Stored in global attributes, not filename
ORBSIM_VERSION=" ";  # Set to " " if this is not part of an orbital sim

#FPATH_WITH_ELSETS="";
FPATH_WITH_ELSETS="${base_dir}/inputs/input_ELSETs.3le";

export PACKAGE_TOP_DIR ANCILLARY_DATA_DIR FPATH_WITH_ELSETS;
export OUTPUT_DIR PROC_MODE PRODUCT_FULLVER ORBSIM_VERSION;

#= Processing mode #5: Over a 1-hour time period, reconstruct orbit state
#                       vectors and related information at 1 Hz, and determine
#                       any PREFIRE granule boundaries and IDs within, producing
#                       NetCDF-format 'L0-orbit' file (data volume: small).

# Check if output file directory exists; if not, bail:
tmpdir="${OUTPUT_DIR}";
test -d "${tmpdir}" || { echo "Output directory does not exist: ${tmpdir}"; exit 1; }

# If custom conda environment files exist, activate that conda environment:
conda_env_dir="${this_top_dir}/dist/c_env_for_PREFIRE_L0";
if [ -d "${conda_env_dir}" ]; then
   activate_conda_env "${conda_env_dir}";
fi

# Execute script that writes a new 'prdgit_version.txt', which contains
#  product moniker(s) and current (latest) git hash(es) that are part of the
#  provenance of this package's product(s).
# *** This step should not be done within the SDPS, since that file is
#     created just before delivery to the SDPS.
if [ ! -f "${this_top_dir}/dist/for_SDPS_delivery.txt" ]; then
   python "${this_top_dir}/dist/determine_prdgit.py";
fi

for cfg_str in ${L0ocs1} ${L0ocs2} ${L0ocs3} ${L0ocs4} ${L0ocs5} ${L0ocs6} ${L0ocs7} ${L0ocs8} ${L0ocs9} ${L0ocs10} ${L0ocs11} ${L0ocs12} ${L0ocs13} ${L0ocs14} ${L0ocs15} ${L0ocs16} ${L0ocs17} ${L0ocs18} ${L0ocs19} ${L0ocs20} ${L0ocs21} ${L0ocs22} ${L0ocs23} ${L0ocs24} ${L0ocs25} ${L0ocs26} ${L0ocs27} ${L0ocs28} ${L0ocs29} ${L0ocs30} ${L0ocs31} ${L0ocs32} ${L0ocs33} ${L0ocs34} ${L0ocs35} ${L0ocs36} ${L0ocs37} ${L0ocs38} ${L0ocs39}
do
   SAT_ID=${cfg_str%,*};
   START_UTC=${cfg_str##*,};

   export START_UTC SAT_ID;

   # Execute primary driver:
   if [ "x$1" = "x-i" ]; then
      python "${this_top_dir}/dist/produce_L0.py" -i;
   else
      python "${this_top_dir}/dist/produce_L0.py";
   fi
done

# If custom conda environment files exist, DEactivate that conda environment:
if [ -d "${conda_env_dir}" ]; then
   deactivate_conda_env "${conda_env_dir}";
fi
