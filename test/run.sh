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
## ++ Instead, make a LOCAL copy of this script (e.g., my_run.sh; do not
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

#set -ve;  # Exit on the first error, and print out commands as we execute them
set -e;  # Exit on the first error

# Determine the absolute path of the current working directory:
#  (this is typically the package test/ directory)
readonly base_dir="$(absfpath ".")";

this_top_dir="$(absfpath "${base_dir}/..")";

# Change dir to the 'test/' directory:
test_path="${this_top_dir}/test";
cd "$test_path";

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

# Remove old renamed L0 output files (intended for L1 input):
mnk="mL1";
outputs_for_L1_path="$test_path"/outputs/$mnk;
rm -rf "$outputs_for_L1_path";
mkdir -p "$outputs_for_L1_path";

# Remove old payload tlm output files, create new ones, then rename/copy them
#  to the token L1 input directory:
mnk="m1";
outputs_path="$test_path"/outputs/$mnk;
rm -rf "$outputs_path";
mkdir -p "$outputs_path";
./run_$mnk.sh;
cp "$outputs_path"/prefire_01_payload_tlm_202410170*.nc "$outputs_for_L1_path"/prefire_01_payload_tlm_20241017000000_20241017235959_20241210183433.nc;
cp "$outputs_path"/prefire_02_payload_tlm_202410090*.nc "$outputs_for_L1_path"/prefire_02_payload_tlm_20241009000000_20241009235959_20241210183452.nc;

# Remove old bus tlm output files, create new ones, then rename/copy them
#  to the token L1 input directory:
mnk="m2";
outputs_path="$test_path"/outputs/$mnk;
rm -rf "$outputs_path";
mkdir -p "$outputs_path";
./run_$mnk.sh;
cp "$outputs_path"/prefire_01_bus_tlm_2024101703*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017030000_20241017035959_20241017081059.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101704*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017040000_20241017045959_20241017161401.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101705*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017050000_20241017055959_20241017161401.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101706*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017060000_20241017065959_20241017161401.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101707*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017070000_20241017075959_20241017161422.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101708*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017080000_20241017085959_20241017161422.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101709*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017090000_20241017095959_20241017161422.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101710*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017100000_20241017105959_20241017161422.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101711*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017110000_20241017115959_20241017161422.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101712*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017120000_20241017125959_20241017161422.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101713*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017130000_20241017135959_20241017201328.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101714*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017140000_20241017145959_20241017201328.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101715*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017150000_20241017155959_20241017201328.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101716*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017160000_20241017165959_20241017201328.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101717*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017170000_20241017175959_20241018121014.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101718*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017180000_20241017185959_20241018121014.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101719*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017190000_20241017195959_20241018121014.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101720*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017200000_20241017205959_20241018121014.nc;
cp "$outputs_path"/prefire_01_bus_tlm_2024101721*.nc "$outputs_for_L1_path"/prefire_01_bus_tlm_20241017210000_20241017215959_20241018121014.nc;

cp "$outputs_path"/prefire_02_bus_tlm_2024100902*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009020000_20241009025959_20241009080503.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100903*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009030000_20241009035959_20241009080503.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100904*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009040000_20241009045959_20241009080503.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100905*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009050000_20241009055959_20241009080503.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100906*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009060000_20241009065959_20241009120446.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100907*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009070000_20241009075959_20241009120446.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100908*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009080000_20241009085959_20241010000530.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100909*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009090000_20241009095959_20241010000530.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100910*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009100000_20241009105959_20241010000530.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100911*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009110000_20241009115959_20241010000530.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100912*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009120000_20241009125959_20241010000530.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100913*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009130000_20241009135959_20241010000530.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100914*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009140000_20241009145959_20241010000530.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100915*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009150000_20241009155959_20241010000544.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100916*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009160000_20241009165959_20241010000544.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100917*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009170000_20241009175959_20241010000544.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100918*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009180000_20241009185959_20241010120534.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100919*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009190000_20241009195959_20241010120534.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100920*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009200000_20241009205959_20241010120534.nc;
cp "$outputs_path"/prefire_02_bus_tlm_2024100921*.nc "$outputs_for_L1_path"/prefire_02_bus_tlm_20241009210000_20241009215959_20241010120534.nc;

# Remove old orbit reconstruction output files, create new ones, then
#  rename/copy them to the token L1 input directory:
mnk="m5";
outputs_path="$test_path"/outputs/$mnk;
rm -rf "$outputs_path";
mkdir -p "$outputs_path";
./run_$mnk.sh;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101703*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017030000_20241017035959_20241017081059.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101704*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017040000_20241017045959_20241017161401.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101705*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017050000_20241017055959_20241017161401.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101706*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017060000_20241017065959_20241017161401.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101707*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017070000_20241017075959_20241017161422.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101708*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017080000_20241017085959_20241017161422.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101709*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017090000_20241017095959_20241017161422.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101710*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017100000_20241017105959_20241017161422.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101711*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017110000_20241017115959_20241017161422.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101712*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017120000_20241017125959_20241017161422.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101713*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017130000_20241017135959_20241017201328.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101714*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017140000_20241017145959_20241017201328.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101715*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017150000_20241017155959_20241017201328.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101716*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017160000_20241017165959_20241017201328.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101717*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017170000_20241017175959_20241018121014.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101718*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017180000_20241017185959_20241018121014.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101719*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017190000_20241017195959_20241018121014.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101720*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017200000_20241017205959_20241018121014.nc;
cp "$outputs_path"/prefire_01_orbit_reconst_2024101721*.nc "$outputs_for_L1_path"/prefire_01_orbit_reconst_20241017210000_20241017215959_20241018121014.nc;

cp "$outputs_path"/prefire_02_orbit_reconst_2024100902*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009020000_20241009025959_20241009080503.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100903*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009030000_20241009035959_20241009080503.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100904*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009040000_20241009045959_20241009080503.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100905*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009050000_20241009055959_20241009080503.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100906*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009060000_20241009065959_20241009120446.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100907*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009070000_20241009075959_20241009120446.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100908*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009080000_20241009085959_20241010000530.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100909*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009090000_20241009095959_20241010000530.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100910*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009100000_20241009105959_20241010000530.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100911*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009110000_20241009115959_20241010000530.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100912*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009120000_20241009125959_20241010000530.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100913*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009130000_20241009135959_20241010000530.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100914*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009140000_20241009145959_20241010000530.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100915*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009150000_20241009155959_20241010000544.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100916*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009160000_20241009165959_20241010000544.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100917*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009170000_20241009175959_20241010000544.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100918*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009180000_20241009185959_20241010120534.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100919*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009190000_20241009195959_20241010120534.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100920*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009200000_20241009205959_20241010120534.nc;
cp "$outputs_path"/prefire_02_orbit_reconst_2024100921*.nc "$outputs_for_L1_path"/prefire_02_orbit_reconst_20241009210000_20241009215959_20241010120534.nc;

