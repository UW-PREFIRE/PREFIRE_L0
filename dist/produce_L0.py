"""
PROC_MODE = 0: Process one or more (possibly anachronistic)
                'raw L0 payload telemetry' files, producing (for the specified
                UTC-datetime range)
                * Binary-format 'curated raw L0 payload telemetry' file (*.bin;
                  data volume <= raw input)
PROC_MODE = 1: Process a single 'raw L0 payload telemetry' (per-downlink or
                curated) file, producing
                * NetCDF-format 'prepped L0-payload' file (*.nc; data volume:
                  less than raw input)
PROC_MODE = 2: Process a single 'raw L0 bus telemetry' file, producing
                * NetCDF-format 'prepped L0-bus' file (data volume: less than
                  raw input)
PROC_MODE = 5: Over a 1-hour time period, reconstruct orbit state vectors and
                related information at 1 Hz, and determine any PREFIRE granule
                boundaries and IDs within, producing
                * NetCDF-format 'prepped L0-orbit' file (data volume: small)
PROC_MODE = 51: Creates simulated PREFIRE L0 payload look-type timing and
                 writes it to "prototelemetry" files (which are nominally
                 distributed throughout an entire year)
PROC_MODE = 52: Creates simulated PREFIRE raw L0 bus telemetry files, nominally
                 distributed throughout an entire year. (uses MatLab)

This program requires python version 3.6 or later, and is importable as a 
python module.
"""

  # From the Python standard library:
from pathlib import Path
import os
import sys
import argparse
import subprocess
import datetime

  # From other external Python packages:

  # Custom utilities:


#--------------------------------------------------------------------------
def main(use_saved_exe, interactive_MatLab):
    """Driver routine."""

    package_top_Path = Path(os.environ["PACKAGE_TOP_DIR"])

    sys.path.append(str(package_top_Path / "source" / "python"))
    from PREFIRE_L0.prep_L0_payload_tlm import prep_L0_payload_tlm
    from PREFIRE_L0.prep_L0_bus_tlm import prep_L0_bus_tlm
    from PREFIRE_L0.create_L0_orbit_reconst import create_L0_orbit_reconst
    from PREFIRE_L0.curate_L0_payload_tlm import curate_L0_payload_tlm
    from PREFIRE_L0.create_orbitsim_payload_info import create_orbitsim_payload_info
    from PREFIRE_tools.utils.time import init_leap_s_for_ctimeRefEpoch

    this_environ = os.environ.copy()

    proc_mode = int(this_environ["PROC_MODE"])

    if proc_mode == 0:
        leap_s_info = init_leap_s_for_ctimeRefEpoch([2000, 1, 1, 0, 0 ,0],
                                             epoch_for_ctime_is_actual_UTC=True)
        curate_L0_payload_tlm(leap_s_info)
    elif proc_mode == 1:
        leap_s_info = init_leap_s_for_ctimeRefEpoch([2000, 1, 1, 0, 0 ,0],
                                             epoch_for_ctime_is_actual_UTC=True)
        prep_L0_payload_tlm(leap_s_info)
    elif proc_mode == 2:
        leap_s_info = init_leap_s_for_ctimeRefEpoch([2000, 1, 1, 0, 0 ,0],
                                             epoch_for_ctime_is_actual_UTC=True)

        # First, reconstruct the orbit info:
        tgt_L0_bus_fpath = os.environ["TGT_L0_BUS_FPATH"].strip()
        if len(tgt_L0_bus_fpath) == 0:
            raise RuntimeError("TGT_L0_BUS_FPATH must not be empty")
        elif ',' in tgt_L0_bus_fpath:  # If still using old strategy
            tmp_l = tgt_L0_bus_fpath.split(',')
            print("WARNING: Only a single raw L0-bus input file is now needed.")
            tgt_L0_bus_fpath = tmp_l[-1].strip()
        input_fn = os.path.basename(tgt_L0_bus_fpath)
        tmp_l = input_fn.split('_')
        sat_IDnum = int(tmp_l[1][1])
        start_UTC_DT = datetime.datetime.strptime(tmp_l[4]+"+0000",
                                                               "%Y%m%d%H%M%S%z")
        start_UTC_dtrepr = start_UTC_DT.strftime("%Y-%m-%dT%H:%M:%SZ")
        L0_orbit_fpath = create_L0_orbit_reconst(leap_s_info, sat_IDnum,
                                                 start_UTC_dtrepr)

        # Now prep the bus telemetry data:
        prep_L0_bus_tlm(leap_s_info, L0_orbit_fpath)
    elif proc_mode == 5:
        leap_s_info = init_leap_s_for_ctimeRefEpoch([2000, 1, 1, 0, 0 ,0],
                                             epoch_for_ctime_is_actual_UTC=True)

        start_UTC_dtrepr = os.environ["START_UTC"]
        if len(start_UTC_dtrepr) == 0:
            raise RuntimeError("START_UTC must not be empty")
        tmp = os.environ["SAT_ID"]
        if len(tmp) == 0:
            raise RuntimeError("SAT_ID must not be empty")
        sat_IDnum = int(tmp[-1])
        if sat_IDnum <= 0 or sat_IDnum > 2:
            raise RuntimeError("last character of SAT_ID should be '1' or '2'")
        L0_orbit_fpath = create_L0_orbit_reconst(leap_s_info, sat_IDnum,
                                                 start_UTC_dtrepr)
    elif proc_mode == 51:
        leap_s_info = init_leap_s_for_ctimeRefEpoch([2000, 1, 1, 0, 0 ,0],
                                             epoch_for_ctime_is_actual_UTC=True)
        create_orbitsim_payload_info(leap_s_info)
    elif proc_mode == 61:
        leap_s_info = init_leap_s_for_ctimeRefEpoch([2000, 1, 1, 0, 0 ,0],
                                             epoch_for_ctime_is_actual_UTC=True)
        pass
    else:   # Requires MatLab

        OS_is_MSWin = ( not os.sep == '/' )
          # Determine separator for use in a search PATH:
        if OS_is_MSWin:
            Psep = ';'
        else:
            Psep = ':'

        MatLab_src_dir = str(package_top_Path / "source" / "matlab" /
                             "functions")
        tools_src_dir = str(package_top_Path / "source" / "matlab" /
                            "PREFIRE_tools"/ "functions")
        tools_anc_dir0 = str(package_top_Path / "source" / "matlab" /
                             "PREFIRE_tools" / ".." / ".." / "dist" /
                             "ancillary")
        this_environ["TOOLS_ANC_DIR"] = os.path.realpath(tools_anc_dir0)
        app_MatLab_prefix = "app_matlab"

        dist_Path = package_top_Path / "dist"

        if interactive_MatLab:
            this_environ["MATLABPATH"] = (
                     f"{MatLab_src_dir}{Psep}{dist_Path}{Psep}{tools_src_dir}")
            cmd = ["matlab", "-singleCompThread"]
        else:
            if use_saved_exe:
                cmd = [str(dist_Path / f"{app_MatLab_prefix}_run")]
            else:
                this_environ["MATLABPATH"] = (
                     f"{MatLab_src_dir}{Psep}{dist_Path}{Psep}{tools_src_dir}")
                if OS_is_MSWin:
                    cmd = ["matlab", "-singleCompThread", "-noFigureWindows", "-batch",
                           f"{app_MatLab_prefix}_run"]
                else:
                    cmd = ["matlab", "-singleCompThread", "-nodisplay", "-batch",
                           f"{app_MatLab_prefix}_run"]

        try:
            result = subprocess.run(cmd, env=this_environ, check=True)
        except subprocess.CalledProcessError as e:
            if use_saved_exe:  # Operational case
                raise e from None
            else:
                pass  # Error info should have been printed by MatLab app,
                      #  do not shut down the pipeline


if __name__ == "__main__":
    # Process arguments:
    arg_description = ("PROC_MODE = 0: Curate 1+ 'raw L0 payload "
                       "telemetry' file(s)\n"
                       "PROC_MODE = 1: Prep a 'raw L0 payload telemetry' file\n"
                       "PROC_MODE = 2: Prep a 'raw L0 bus telemetry' file\n"
                       "PROC_MODE = 5: Create a 'L0 orbit' file\n"
                       "PROC_MODE = 51: Create simulated payload info files\n"
                       "PROC_MODE = 52: Create simulated raw bus tlm files")
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
