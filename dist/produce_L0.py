"""
PROC_MODE = 0: Process one or more (possibly anachronistic)
                'raw L0 payload telemetry' files, producing (for the specified
                UTC-datetime range)
                * Binary-format 'curated raw L0 payload telemetry' file (*.bin;
                  data volume <= raw input)

This program requires python version 3.6 or later, and is importable as a 
python module.
"""

  # From the Python standard library:
from pathlib import Path
import os
import sys
import argparse
import subprocess

  # From other external Python packages:

  # Custom utilities:


#--------------------------------------------------------------------------
def main(use_saved_exe, interactive_MatLab):
    """Driver routine."""

    package_top_Path = Path(os.environ["PACKAGE_TOP_DIR"])

    sys.path.append(str(package_top_Path / "source" / "python"))
    from PREFIRE_L0.curate_L0_payload_tlm import curate_L0_payload_tlm
    from PREFIRE_tools.utils.time import init_leap_s_for_ctimeRefEpoch

    this_environ = os.environ.copy()

    proc_mode = int(this_environ["PROC_MODE"])

    if proc_mode == 0:
        leap_s_info = init_leap_s_for_ctimeRefEpoch([2000, 1, 1, 0, 0 ,0],
                                             epoch_for_ctime_is_actual_UTC=True)
        curate_L0_payload_tlm(leap_s_info)


if __name__ == "__main__":
    # Process arguments:
    arg_description = ("PROC_MODE = 0: Curate 1+ 'raw L0 payload "
                       "telemetry' file(s)")
    arg_parser = argparse.ArgumentParser(description=arg_description)
    arg_parser.add_argument("-s", "--use_saved_exe", action="store_true",
                            help="Use the MatLab Runtime to execute routines "
                                 "stored in a Matlab executable file.")
    arg_parser.add_argument("-i", "--interactive-no_display",
                            dest="interactive", action="store_true",
                            help="Set environment, then run MatLab in "
                               "interactive mode (but with no fancy display).") 

    args = arg_parser.parse_args()

    # Check for argument sanity:
    if args.use_saved_exe and args.interactive:
        raise ValueError("Arguments -s and -i cannot be used together.")

    # Run driver:
    main(args.use_saved_exe, args.interactive)
