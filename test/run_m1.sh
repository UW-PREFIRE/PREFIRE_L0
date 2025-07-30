#!/usr/bin/env bash

## IMPORTANT: Only run this script from the directory it resides in, i.e. with
##             ./run_m1.sh    OR    bash run_m1.sh

##===========================================================================##
## This script contains hardwired information necessary for this algorithm's
##  delivery to and testing within the SDPS (Science Data Processing System).
##
## ** In general, do not push changes to this file to its primary git
##     repository (exceptions include adding a new environment var for
##     algorithm config) **
##
## ++ Instead, make a LOCAL copy of this script (e.g., my_run_m1.sh; do not
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

L0_pld_cfg_str1="${L0_dir}/prefire_01_payload_tlm_2024_10_17_17_39_04.bin";
L0_pld_cfg_str2="${L0_dir}/prefire_01_payload_tlm_20241017000000_20241017235959_20241210183209.bin";

L0_pld_cfg_str3="${L0_dir}/prefire_02_payload_tlm_2024_10_10_08_37_32.bin";
L0_pld_cfg_str4="${L0_dir}/prefire_02_payload_tlm_20241009000000_20241009235959_20241210183215.bin";


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

OUTPUT_DIR="${base_dir}/outputs/m1";

PROC_MODE=1;

PRODUCT_FULLVER="P01_R00";  # Stored in global attributes, not filename
ORBSIM_VERSION=" ";  # Set to " " if this is not part of an orbital sim
SRF_NEDR_VERSION=" ";  # Set to " " if this is not part of an orbital sim

export PACKAGE_TOP_DIR ANCILLARY_DATA_DIR;
export OUTPUT_DIR PROC_MODE PRODUCT_FULLVER ORBSIM_VERSION SRF_NEDR_VERSION;

#= Processing mode #1: Process a single (per-downlink or curated)
#                      'raw L0 payload telemetry' file, producing a NetCDF
#                      'L0-payload' file (data volume is less than raw input).

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

for cfg_str in ${L0_pld_cfg_str1} ${L0_pld_cfg_str2} ${L0_pld_cfg_str3} ${L0_pld_cfg_str4}
do
   TGT_L0_PAYLOAD_FPATH=${cfg_str};

   export TGT_L0_PAYLOAD_FPATH;

   # Execute primary driver:
   if [ "x$1" = "x-i" ]; then
      python "${this_top_dir}/dist/produce_L0.py" -i;
   else
      python "${this_top_dir}/dist/produce_L0.py";
   fi
done

# If custom conda environment files exist, DEactivate that conda environment:
if [ -d "$conda_env_dir" ]; then
   deactivate_conda_env "${conda_env_dir}";
fi
