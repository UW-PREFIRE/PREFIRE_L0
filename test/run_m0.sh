#!/usr/bin/env bash

## IMPORTANT: Only run this script from the directory it resides in, i.e. with
##             ./run_m0.sh    OR    bash run_m0.sh

##===========================================================================##
## This script contains hardwired information necessary for this algorithm's
##  delivery to and testing within the SDPS (Science Data Processing System).
##
## ** In general, do not push changes to this file to its primary git
##     repository (exceptions include adding a new environment var for
##     algorithm config) **
##
## ++ Instead, make a LOCAL copy of this script (e.g., my_run_m0.sh; do not
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

set -ve;  # Exit on the first error, and print out commands as we execute them
#set -e;  # Exit on the first error

# Determine the absolute path of the current working directory:
#  (this is typically the package test/ directory)
readonly base_dir="$(absfpath ".")";

hn=`hostname -s`;  # Hostname

# NOTE: Set the input/output directories to absolute paths (relative to the
#        current working directory, 'base_dir').

non_SDPS_hostname="longwave";

L0_dir="${base_dir}/inputs";

L0_pld_cfg_str1="${L0_dir}/prefire_01_payload_tlm_2024_07_25_03_28_07.bin,${L0_dir}/prefire_01_payload_tlm_2024_07_25_07_45_09.bin,${L0_dir}/prefire_01_payload_tlm_2024_07_25_16_37_45.bin,${L0_dir}/prefire_01_payload_tlm_2024_07_25_18_33_27.bin,${L0_dir}/prefire_01_payload_tlm_2024_07_26_03_18_11.bin||2024-07-25T00:00:00.000->2024-07-25T23:59:59.999";
L0_pld_cfg_str2="${L0_dir}/prefire_01_payload_tlm_2024_07_26_03_18_11.bin||USE_DETECTED_BOUNDS";
L0_pld_cfg_str3="${L0_dir}/prefire_02_payload_tlm_2024_07_06_00_33_51.bin,${L0_dir}/prefire_02_payload_tlm_2024_07_06_13_44_54.bin,${L0_dir}/prefire_02_payload_tlm_2024_07_06_15_08_02.bin,${L0_dir}/prefire_02_payload_tlm_2024_07_06_22_53_13.bin,${L0_dir}/prefire_02_payload_tlm_2024_07_07_00_23_20.bin||2024-07-06T00:00:00.000->2024-07-06T23:59:59.999";


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

OUTPUT_DIR="${base_dir}/outputs/m0";

PROC_MODE=0;

export PACKAGE_TOP_DIR ANCILLARY_DATA_DIR OUTPUT_DIR PROC_MODE;

#= Processing mode #0: Produce a curated 'raw L0 payload telemetry' file for
#                       the specified UTC-datetime range, given one or more raw
#                       L0-payload per-downlink files (possibly anachronistic).
#                       These inputs are all specified within the (string)
#                       value of TGT_L0_PLD_FPATHS_DTRANGE

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

for cfg_str in ${L0_pld_cfg_str1} ${L0_pld_cfg_str2} ${L0_pld_cfg_str3}
do
   TGT_L0_PLD_FPATHS_DTRANGE=${cfg_str};

   export TGT_L0_PLD_FPATHS_DTRANGE;

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
