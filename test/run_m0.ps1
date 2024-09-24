## IMPORTANT: Only run this script from the directory it resides in, i.e. with
##             .\run_m0.ps1

##===========================================================================##
## This script contains hardwired information necessary for this algorithm's
##  delivery to and testing within the SDPS (Science Data Processing System).
##
## ** In general, do not push changes to this file to its primary git
##     repository (exceptions include adding a new environment var for
##     algorithm config) **
##
## ++ Instead, make a LOCAL copy of this script (e.g., my_run_m0.ps1; do not
##     push that local copy to the primary git repository either) and modify
##     and run that for general algorithm testing and development.
##===========================================================================##

# Determine the absolute path of the current working directory:
#  (this is typically the package test/ directory)
$base_dir = $pwd

# NOTE: Set the input/output directories to absolute paths (relative to the
#        current working directory, 'base_dir').

$L0_dir = "$base_dir\inputs"

$L0_pld_cfg_str1 = "$L0_dir\prefire_01_payload_tlm_2024_07_25_03_28_07.bin,$L0_dir\prefire_01_payload_tlm_2024_07_25_07_45_09.bin,$L0_dir\prefire_01_payload_tlm_2024_07_25_16_37_45.bin,$L0_dir\prefire_01_payload_tlm_2024_07_25_18_33_27.bin,$L0_dir\prefire_01_payload_tlm_2024_07_26_03_18_11.bin||2024-07-25T00:00:00.000->2024-07-25T23:59:59.999"
$L0_pld_cfg_str2 = "$L0_dir\prefire_01_payload_tlm_2024_07_26_03_18_11.bin||USE_DETECTED_BOUNDS"
$L0_pld_cfg_str3 = "$L0_dir\prefire_02_payload_tlm_2024_07_06_00_33_51.bin,$L0_dir\prefire_02_payload_tlm_2024_07_06_13_44_54.bin,$L0_dir\prefire_02_payload_tlm_2024_07_06_15_08_02.bin,$L0_dir\prefire_02_payload_tlm_2024_07_06_22_53_13.bin,$L0_dir\prefire_02_payload_tlm_2024_07_07_00_23_20.bin||2024-07-06T00:00:00.000->2024-07-06T23:59:59.999"


# Specify that numpy, scipy, et cetera should not use more than one thread or
#  process):
$env:MKL_NUM_THREADS = '1'
$env:NUMEXPR_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:VECLIB_MAXIMUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'

# Some environment vars that convey configuration info to the algorithm:

$this_top_dir = [IO.Path]::GetFullPath("$base_dir\..")

$env:PACKAGE_TOP_DIR = "$this_top_dir"
$env:ANCILLARY_DATA_DIR = "$this_top_dir\dist\ancillary"

$env:OUTPUT_DIR = "$base_dir\outputs\m0"

$env:PROC_MODE = '0'

#= Processing mode #0: Produce a curated 'raw L0 payload telemetry' file for
#                       the specified UTC-datetime range, given one or more raw
#                       L0-payload per-downlink files (possibly anachronistic).
#                       These inputs are all specified within the (string)
#                       value of TGT_L0_PLD_FPATHS_DTRANGE

# Check if output file directory exists; if not, bail:
$tmpdir = "$env:OUTPUT_DIR"
If (-not (Test-Path -Path $tmpdir)) {
  throw "Output directory does not exist: $tmpdir"
}

# Execute script that writes a new 'prdgit_version.txt', which contains
#  product moniker(s) and current (latest) git hash(es) that are part of the
#  provenance of this package's product(s).
# *** This step should not be done within the SDPS, since that file is
#     created just before delivery to the SDPS.
If (-not (Test-Path -Path "$this_top_dir\dist\for_SDPS_delivery.txt")) {
  python "$this_top_dir\dist\determine_prdgit.py"
}

$items = @($L0_pld_cfg_str1, $L0_pld_cfg_str2, $L0_pld_cfg_str3)
foreach ($cfg_str in $items) {
  $env:TGT_L0_PLD_FPATHS_DTRANGE = $cfg_str

  # Execute primary driver:
  #python "$this_top_dir\dist\produce_L0.py" -i
  python "$this_top_dir\dist\produce_L0.py"
}
