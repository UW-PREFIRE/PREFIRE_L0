#!/usr/bin/env bash

#  Usage example (to run an M-Script 'BRF_model_v6.m'):
#    bash run_matlab_script.sh ./BRF_model_v6
#       -OR-
#    bash run_matlab_script.sh /home/some_user/BRF_model_v6

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

#set -ve;  # Exit on the first error, and print out commands as we execute them
set -e;  # Exit on the first error

# Load any modules:
. /usr/share/lmod/lmod/init/bash;  # Init Lmod environment module system hooks
. ../../dist/perform_machine_setup.sh;

# Set up some needed path info and environment variables:
readonly base_dir="$(absfpath ".")";
package_top_dir="$(absfpath "${base_dir}/../..")";

export PROC_MODE="-1";  # Needed to trigger 'cfg_L0_toplevel_IO.m' env var block

MatLab_src_dir="$package_top_dir/source/matlab/functions";
tools_src_dir="$package_top_dir/source/matlab/PREFIRE_tools/functions";
tools_anc_dir0="$package_top_dir/source/matlab/PREFIRE_tools/../../dist/ancillary";
export TOOLS_ANC_DIR="$(absfpath "${tools_anc_dir0}")";

L0_src_dir="$package_top_dir/source/matlab/functions";

dist_dir="$package_top_dir/dist";

export MATLABPATH="${MatLab_src_dir}:${dist_dir}:${tools_src_dir}:${L0_src_dir}";
export MTLB_PATH_ALREADY_SET="yes";

tgt_dir="${1%/*}";
tgt_fn="${1##*/}";

# Run the given M-script:
cd "${tgt_dir}";
matlab -singleCompThread -nodisplay -batch "${tgt_fn}";
cd "${base_dir}";
