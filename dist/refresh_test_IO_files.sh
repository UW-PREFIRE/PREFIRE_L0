#!/usr/bin/env bash

## IMPORTANT: Only run this script from the directory it resides in, i.e. with
##             ./refresh_test_IO_files.sh   OR   bash refresh_test_IO_files.sh

# Recreate/refresh all test input and output files for this science algorithm
#  package, EXCEPT for the test input files required to bootstrap the process. 

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

# Determine the absolute path of the current working directory:
#  (this is typically the package dist/ directory)
readonly base_dir="$(absfpath ".")";

this_top_dir="$(absfpath "${base_dir}/..")";

# Change dir to the 'test/' directory:
test_path="${this_top_dir}/test";
cd "$test_path";

# Run script to refresh test input:
./run.sh;

# Directory (or a symlink of the same name) 'test/inputs/' must already exist
#  (and contain raw L0 telemetry files) for this package:
inputs_path="$test_path"/inputs;

# Remove old curated payload tlm output files, create new ones, rename the
#  relevant new output files to what is expected by run_m1.sh, and then copy
#  them to inputs/:
mnk="m0";
outputs_path="$test_path"/outputs/$mnk;
rm -rf "$outputs_path";
mkdir -p "$outputs_path";
./run_$mnk.sh;
cp "$outputs_path"/prefire_01_payload_tlm_20241017*.bin "$inputs_path"/prefire_01_payload_tlm_20241017000000_20241017235959_20241210183209.bin;
cp "$outputs_path"/prefire_02_payload_tlm_20241009*.bin "$inputs_path"/prefire_02_payload_tlm_20241009000000_20241009235959_20241210183215.bin;

# Remove old payload tlm output files, create new ones:
mnk="m1";
outputs_path="$test_path"/outputs/$mnk;
rm -rf "$outputs_path";
mkdir -p "$outputs_path";
./run_$mnk.sh;

# Remove old bus tlm output files, create new ones:
mnk="m2";
outputs_path="$test_path"/outputs/$mnk;
rm -rf "$outputs_path";
mkdir -p "$outputs_path";
./run_$mnk.sh;

# Remove old orbit reconstruction output files, create new ones:
mnk="m5";
outputs_path="$test_path"/outputs/$mnk;
rm -rf "$outputs_path";
mkdir -p "$outputs_path";
./run_$mnk.sh;

echo "Finished refreshing test input.";
