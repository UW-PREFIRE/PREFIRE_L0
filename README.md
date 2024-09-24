# PREFIRE_L0

Package (written primarily in Python) to curate the raw PREFIRE Level-0 payload telemetry information.

This code is released under the terms of this [LICENSE](LICENSE).  The version of this package can be found in [VERSION.txt](VERSION.txt).

# Installation

## Requirements

Python version 3.8+ is required, along with the following third-party Python packages: numpy

The associated (Python-based) git repository 'PREFIRE_tools' is also required for the proper operation of this package.

## Python Environment Setup

It is recommended to install the above Python packages in a dedicated conda environment (or something similar).  The packages used (and their versions) can be found in [conda_env.list](conda_env.list).

For example, using conda (and specifying Python 3.10.x from the conda-forge channel):

conda create --name for_PREFIRE_L0 -c conda-forge python=3.10;
conda activate for_PREFIRE_L0;
conda install -c conda-forge numpy;

The location of 'PREFIRE_tools' depends on the value of the user's PYTHONPATH and/or sys.path -- for example, one could simply add each of those git repositories' local root Python source code directory to PYTHONPATH. Operationally, however, this package uses symbolic links to those git repositories' local root Python source code directories (or full copies of the same) in the source/ directory.

## Environment Variables

### Each job (executing this science algorithm package) is configured via information contained within environment variables.

### To specify that numpy, scipy, et cetera used by this algorithm should not use more than one thread or process, the below environment variables are expected to be set:

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

PROC_MODE  :  the processing mode (operationally-valid values: 0, 1, 2; see below for more details)

# Running the test script(s)

## Obtain and unpack any ancillary data and/or test data

### None (for this version)

## Prepare the output directory:

`cd test;`

On Linux/UNIX systems, possibly create a useful symbolic link to the test input data (if needed):

`ln -s WHEREEVER_THE_DATA_IS/inputs inputs;`

Prepare the output directory (Linux/UNIX example):

`mkdir -p outputs;`

OR perhaps something like

`ln -s /data/users/myuser/data-PREFIRE_L0/outputs outputs;`

## Run the L0 package

### A Linux/UNIX example

`cp run_m0.sh my-run_m0.sh;`

Edit `my-run_m0.sh` as needed (e.g., change input file names)

`./my-run_m0.sh`

### The output file(s) will be in subdirectories of `test/outputs/` (e.g., `m0/`)

## _The creation of this code was supported by NASA, as part of the PREFIRE (Polar Radiant Energy in the Far-InfraRed Experiment) CubeSat mission._
