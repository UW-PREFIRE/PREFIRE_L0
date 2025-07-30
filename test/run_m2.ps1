## IMPORTANT: Only run this script from the directory it resides in, i.e. with
##             .\run_m2.ps1

##===========================================================================##
## This script contains hardwired information necessary for this algorithm's
##  delivery to and testing within the SDPS (Science Data Processing System).
##
## ** In general, do not push changes to this file to its primary git
##     repository (exceptions include adding a new environment var for
##     algorithm config) **
##
## ++ Instead, make a LOCAL copy of this script (e.g., my_run_m2.ps1; do not
##     push that local copy to the primary git repository either) and modify
##     and run that for general algorithm testing and development.
##===========================================================================##

# Determine the absolute path of the current working directory:
#  (this is typically the package test/ directory)
$base_dir = $pwd

# NOTE: Set the input/output directories to absolute paths (relative to the
#        current working directory, 'base_dir').

$L0_dir = "$base_dir\inputs"

$L0bcs1 = "$L0_dir\prefire_01_bus_tlm_20241017030000_20241017035959_20241017081059.csv"
$L0bcs2 = "$L0_dir\prefire_01_bus_tlm_20241017040000_20241017045959_20241017161401.csv"
$L0bcs3 = "$L0_dir\prefire_01_bus_tlm_20241017050000_20241017055959_20241017161401.csv"
$L0bcs4 = "$L0_dir\prefire_01_bus_tlm_20241017060000_20241017065959_20241017161401.csv"
$L0bcs5 = "$L0_dir\prefire_01_bus_tlm_20241017070000_20241017075959_20241017161422.csv"
$L0bcs6 = "$L0_dir\prefire_01_bus_tlm_20241017080000_20241017085959_20241017161422.csv"
$L0bcs7 = "$L0_dir\prefire_01_bus_tlm_20241017090000_20241017095959_20241017161422.csv"
$L0bcs8 = "$L0_dir\prefire_01_bus_tlm_20241017100000_20241017105959_20241017161422.csv"
$L0bcs9 = "$L0_dir\prefire_01_bus_tlm_20241017110000_20241017115959_20241017161422.csv"
$L0bcs10 = "$L0_dir\prefire_01_bus_tlm_20241017120000_20241017125959_20241017161422.csv"
$L0bcs11 = "$L0_dir\prefire_01_bus_tlm_20241017130000_20241017135959_20241017201328.csv"
$L0bcs12 = "$L0_dir\prefire_01_bus_tlm_20241017140000_20241017145959_20241017201328.csv"
$L0bcs13 = "$L0_dir\prefire_01_bus_tlm_20241017150000_20241017155959_20241017201328.csv"
$L0bcs14 = "$L0_dir\prefire_01_bus_tlm_20241017160000_20241017165959_20241017201328.csv"
$L0bcs15 = "$L0_dir\prefire_01_bus_tlm_20241017170000_20241017175959_20241018121014.csv"
$L0bcs16 = "$L0_dir\prefire_01_bus_tlm_20241017180000_20241017185959_20241018121014.csv"
$L0bcs17 = "$L0_dir\prefire_01_bus_tlm_20241017190000_20241017195959_20241018121014.csv"
$L0bcs18 = "$L0_dir\prefire_01_bus_tlm_20241017200000_20241017205959_20241018121014.csv"
$L0bcs19 = "$L0_dir\prefire_01_bus_tlm_20241017210000_20241017215959_20241018121014.csv"

$L0bcs20 = "$L0_dir\prefire_02_bus_tlm_20241009020000_20241009025959_20241009080503.csv"
$L0bcs21 = "$L0_dir\prefire_02_bus_tlm_20241009030000_20241009035959_20241009080503.csv"
$L0bcs22 = "$L0_dir\prefire_02_bus_tlm_20241009040000_20241009045959_20241009080503.csv"
$L0bcs23 = "$L0_dir\prefire_02_bus_tlm_20241009050000_20241009055959_20241009080503.csv"
$L0bcs24 = "$L0_dir\prefire_02_bus_tlm_20241009060000_20241009065959_20241009120446.csv"
$L0bcs25 = "$L0_dir\prefire_02_bus_tlm_20241009070000_20241009075959_20241009120446.csv"
$L0bcs26 = "$L0_dir\prefire_02_bus_tlm_20241009080000_20241009085959_20241010000530.csv"
$L0bcs27 = "$L0_dir\prefire_02_bus_tlm_20241009090000_20241009095959_20241010000530.csv"
$L0bcs28 = "$L0_dir\prefire_02_bus_tlm_20241009100000_20241009105959_20241010000530.csv"
$L0bcs29 = "$L0_dir\prefire_02_bus_tlm_20241009110000_20241009115959_20241010000530.csv"
$L0bcs30 = "$L0_dir\prefire_02_bus_tlm_20241009120000_20241009125959_20241010000530.csv"
$L0bcs31 = "$L0_dir\prefire_02_bus_tlm_20241009130000_20241009135959_20241010000530.csv"
$L0bcs32 = "$L0_dir\prefire_02_bus_tlm_20241009140000_20241009145959_20241010000530.csv"
$L0bcs33 = "$L0_dir\prefire_02_bus_tlm_20241009150000_20241009155959_20241010000544.csv"
$L0bcs34 = "$L0_dir\prefire_02_bus_tlm_20241009160000_20241009165959_20241010000544.csv"
$L0bcs35 = "$L0_dir\prefire_02_bus_tlm_20241009170000_20241009175959_20241010000544.csv"
$L0bcs36 = "$L0_dir\prefire_02_bus_tlm_20241009180000_20241009185959_20241010120534.csv"
$L0bcs37 = "$L0_dir\prefire_02_bus_tlm_20241009190000_20241009195959_20241010120534.csv"
$L0bcs38 = "$L0_dir\prefire_02_bus_tlm_20241009200000_20241009205959_20241010120534.csv"
$L0bcs39 = "$L0_dir\prefire_02_bus_tlm_20241009210000_20241009215959_20241010120534.csv"


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

$env:OUTPUT_DIR = "$base_dir\outputs\m2"

$env:PROC_MODE = '2'

$env:PRODUCT_FULLVER = "P01_R00"  # Stored in global attributes, not filename
$env:ORBSIM_VERSION = " "  # Set to " " if this is not part of an orbital sim

#$env:FPATH_WITH_ELSETS = " "
$env:FPATH_WITH_ELSETS = "$base_dir\inputs\input_ELSETs.3le"

#= Processing mode #2: Process a single 'raw L0 bus telemetry' file,
#                      producing a NetCDF 'L0-bus' file (data volume is
#                      less than raw input), and produce a orbit reconstruction
#                      info NetCDF 'L0-orbit' file (data volume is less than raw
#                      input).

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

$items = @($L0bcs1, $L0bcs2, $L0bcs3, $L0bcs4, $L0bcs5, $L0bcs6, $L0bcs7, $L0bcs8, $L0bcs9, $L0bcs10, $L0bcs11, $L0bcs12, $L0bcs13, $L0bcs14, $L0bcs15, $L0bcs16, $L0bcs17, $L0bcs18, $L0bcs19, $L0bcs20, $L0bcs21, $L0bcs22, $L0bcs23, $L0bcs24, $L0bcs25, $L0bcs26, $L0bcs27, $L0bcs28, $L0bcs29, $L0bcs30, $L0bcs31, $L0bcs32, $L0bcs33, $L0bcs34, $L0bcs35, $L0bcs36, $L0bcs37, $L0bcs38, $L0bcs39)
foreach ($cfg_str in $items) {
  $env:TGT_L0_BUS_FPATH = $cfg_str

  # Execute primary driver:
  #python "$this_top_dir\dist\produce_L0.py" -i
  python "$this_top_dir\dist\produce_L0.py"
}
