# PREFIRE_L0

Package (written primarily in Python) to curate/process/produce the PREFIRE Level-0 products. These products provide raw or nearly-raw payload and spacecraft-bus telemetry information.

This code is released under the terms of this [LICENSE](LICENSE).  The version of this package can be found in [VERSION.txt](VERSION.txt).

# Installation

## Requirements

Python version 3.8+ is required, along with the following third-party Python packages: numpy, netcdf4, pandas, skyfield

The associated (Python-based) git repository ['PREFIRE_tools'](https://github.com/UW-PREFIRE/PREFIRE_tools) is also required for the proper operation of this package.

## Python Environment Setup

It is recommended to install the above Python packages in a dedicated conda environment (or something similar).  The packages used (and their versions) can be found in [conda_env.list](dist/conda_env.list).

For example, using conda (and specifying Python 3.10.x from the conda-forge channel):

```
conda create --name for_PREFIRE_L0 -c conda-forge python=3.10;
conda activate for_PREFIRE_L0;
conda install -c conda-forge numpy netcdf4 pandas skyfield;
```

The location of 'PREFIRE_tools' depends on the value of the user's PYTHONPATH and/or sys.path -- for example, one could simply add each of those git repositories' local root Python source code directory to PYTHONPATH. Operationally, however, this package uses symbolic links to those git repositories' local root Python source code directories (or full copies of the same) in the source/ directory.

## Environment Variables

### Each job (executing this science algorithm package) is configured via information contained within environment variables.

### To specify that numpy, pandas, et cetera used by this algorithm should not use more than one thread or process, the below environment variables are expected to be set:

```
MKL_NUM_THREADS=1
NUMEXPR_NUM_THREADS=1
OMP_NUM_THREADS=1
VECLIB_MAXIMUM_THREADS=1
OPENBLAS_NUM_THREADS=1
```

### Some environment variables are always required to be set (also see test/run_m*.sh or test/run_m*.ps1):

PACKAGE_TOP_DIR  :  the top-level directory (i.e., the one that contains dist/, test/, etc.) of this package

ANCILLARY_DATA_DIR  :  the package's ancillary data directory (should be an absolute path)

OUTPUT_DIR  :  the directory in which all meaningful output will be written (should be an absolute path)

PRODUCT_FULLVER  :  the full product processing/revision version string (e.g., "P01_R02").  Only increment 'Rxx' when the resulting products will be DAAC-ingested.  Whenever incrementing 'Rxx', reset 'Pyy' to 'P01'.

PROC_MODE  :  the processing mode (operationally-valid values: 0, 1, 2, 5; see below for more details)

ORBSIM_VERSION  :  orbit simulation version (" " operationally)

### This science algorithm package has 4 different operational modes, specified by the current value of the PROC_MODE environment variable (see above).  Each mode has a set of mode-specific environment variables.  More information about the values of each of these can be found in the `test/run_m\*.sh` scripts.

_PROC_MODE = 0  (process raw flat-binary per-downlink L0-payload telemetry file(s) to a curated UTC-daily flat-binary L0-payload telemetry file)_

TGT_L0_PLD_FPATHS_DTRANGE  :  filepath(s) of the raw L0-payload telemetry file(s) plus the target (UTC) date to curate

_PROC_MODE = 1  (process a raw flat-binary L0-payload telemetry file, per-downlink or curated, to a "prepped" NetCDF-format L0-payload file)_

SRF_NEDR_VERSION  :  string specifying which SRF/NEdR file version was used to create the input data (" " operationally)

TGT_L0_PAYLOAD_FPATH  :  filepath of the raw L0-payload telemetry file

_PROC_MODE = 2  (process a raw text-csv L0-bus telemetry file to a "prepped" NetCDF-format L0-bus file, and write orbit reconstruction info to a "prepped" NetCDF-format L0-orbit file)_

TGT_L0_BUS_FPATH  :  filepath of the raw L0-bus telemetry file

FPATH_WITH_ELSETS  :  provides orbit element sets (ELSETs) for reconstructing the orbit -- set to either " " (in which case archived ELSETs will be used) -OR- a
 filepath that contains text ELSETs (*.3le or *.tle format; in which case archived ELSETs will only be used if the provided ones are outside the target time range)

_PROC_MODE = 5  (produce and write orbit reconstruction information to a "prepped" NetCDF-format L0-orbit file)_

START_UTC  :  the UTC datetime to start the orbit reconstruction at, represented as a formatted string (e.g., "2024-07-25T09:00:00Z")

SAT_ID  :  CubeSat ID (i.e., "PREFIRE-SAT1" or "PREFIRE-SAT2")

FPATH_WITH_ELSETS  :  provides orbit element sets (ELSETs) for reconstructing the orbit -- set to either " " (in which case archived ELSETs will be used) -OR- a
 filepath that contains text ELSETs (*.3le or *.tle format; in which case archived ELSETs will only be used if the provided ones are outside the target time range)

# Running the test script(s)

## Obtain and unpack any ancillary data and/or test data

None (for this version).

## Prepare the output directory:

`cd test;`

On Linux/UNIX systems, possibly create a useful symbolic link to the test input data (if needed):

`ln -s WHEREEVER_THE_DATA_IS/inputs inputs;`

Prepare the output directory (Linux/UNIX example):

`mkdir -p outputs;`

_OR_ perhaps something like

`ln -s /data/users/myuser/data-PREFIRE_L0/outputs outputs;`

## Run the L0 package

### A Linux/UNIX example

`cp run_m0.sh my-run_m0.sh;`

Edit `my-run_m0.sh` as needed (e.g., change input file names)

`./my-run_m0.sh`

The output file(s) will be in subdirectories of `test/outputs/` (e.g., `m0/`)

## _The creation of this code was supported by NASA, as part of the PREFIRE (Polar Radiant Energy in the Far-InfraRed Experiment) CubeSat mission._
