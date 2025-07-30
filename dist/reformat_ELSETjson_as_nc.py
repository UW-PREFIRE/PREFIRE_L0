"""
This program requires python version 3.6 or later, and is importable as a 
python module.
"""

  # From the Python standard library:
import os
import sys
import datetime
import json
import argparse

  # From other external Python packages:
import numpy as np
import netCDF4

  # Custom utilities:
# Additional imports in main()


#-----------------------------------------------------------------------------
def main(cfg_d):

    # Augment sys.path, and then import custom utilities:

       #== Location of a clone of the PREFIRE_tools repo:
    PREFIRE_tools_path = os.path.join(cfg_d["common_path"], "PREFIRE_tools")
    sys.path.append(os.path.join(PREFIRE_tools_path, "source", "python"))
       #== Location of a clone of the PREFIRE_PRD_GEN repo:
    PREFIRE_PRD_GEN_path = os.path.join(cfg_d["common_path"], "PREFIRE_PRD_GEN")
    sys.path.append(os.path.join(PREFIRE_PRD_GEN_path, "source"))

    from PREFIRE_tools.utils.time import init_leap_s_for_ctimeRefEpoch, \
                                         UTC_DT_to_ctime
    from PREFIRE_tools.utils.unit_conv import minute_to_s
    from PREFIRE_PRD_GEN.file_creation import write_data_fromspec
    
 # NOTE: This code expects raw JSON-format input as formatted by
 #        Space-Track (https://www.space-track.org).  A one element-set example
 #        of that particular JSON formatting is provided below.
 #
 #       This code would likely need to be modified to properly use JSON-format
 #        input from another source (e.g., Celestrak).
 #
 # [{"CCSDS_OMM_VERS":"2.0","COMMENT":"GENERATED VIA SPACE-TRACK.ORG API","CREATION_DATE":"2024-06-01T19:30:34","ORIGINATOR":"18 SPCS","OBJECT_NAME":"PREFIRE-1","OBJECT_ID":"2024-099A","CENTER_NAME":"EARTH","REF_FRAME":"TEME","TIME_SYSTEM":"UTC","MEAN_ELEMENT_THEORY":"SGP4","EPOCH":"2024-06-01T07:09:58.519872","MEAN_MOTION":"15.11864619","ECCENTRICITY":"0.00128560","INCLINATION":"97.4987","RA_OF_ASC_NODE":"11.0288","ARG_OF_PERICENTER":"280.0775","MEAN_ANOMALY":"79.9005","EPHEMERIS_TYPE":"0","CLASSIFICATION_TYPE":"U","NORAD_CAT_ID":"59881","ELEMENT_SET_NO":"999","REV_AT_EPOCH":"105","BSTAR":"0.00025830000000","MEAN_MOTION_DOT":"0.00004362","MEAN_MOTION_DDOT":"0.0000000000000","SEMIMAJOR_AXIS":"6908.651","PERIOD":"95.247","APOAPSIS":"539.398","PERIAPSIS":"521.634","OBJECT_TYPE":"PAYLOAD","RCS_SIZE":null,"COUNTRY_CODE":"US","LAUNCH_DATE":"2024-05-25","SITE":"RLLC","DECAY_DATE":null,"FILE":"4333553","GP_ID":"258578461","TLE_LINE0":"0 PREFIRE-1","TLE_LINE1":"1 59881U 24099A   24153.29859398  .00004362  00000-0  25830-3 0  9999","TLE_LINE2":"2 59881  97.4987  11.0288 0012856 280.0775  79.9005 15.11864619  1056"}]

    with open(cfg_d["input_fpath"], 'r') as json_ds:
        json_data = json.load(json_ds)

    output = {}
    o_data = {}

    outp_nc_fn = os.path.basename(cfg_d["input_fpath"])[:-4]+"nc"

    now_UTC_DT = datetime.datetime.now(datetime.timezone.utc)
    now_UTC_strrep = now_UTC_DT.strftime("%Y-%m-%dT%H:%M:%S.%f")

    elset_epoch_UTC_strrep = [elset["EPOCH"] for elset in json_data]
    elset_epoch_UTC_DT = [datetime.datetime.fromisoformat(x+"+00:00") for x in
           elset_epoch_UTC_strrep]
    tmp_eUdr = [int(x.strftime("%Y%m%d%H%M%S%f")[:-3]) for x in
                                                            elset_epoch_UTC_DT]
    n_raw_elset = len(tmp_eUdr)

    # Determine de-duplication guide array:
    unique = []
    is_part = np.full((n_raw_elset,), False)
    for i in range(n_raw_elset-1, -1, -1):
        item = tmp_eUdr[i]
        if item not in unique:
            unique.append(item)
            is_part[i] = True
    
    o_data["epoch_UTC_datetime_repr"] = np.array([tmp_eUdr[i] for i in
                                             range(n_raw_elset) if is_part[i]])
    eeUDT = np.array([elset_epoch_UTC_DT[i] for i in
                                             range(n_raw_elset) if is_part[i]])

    leap_s_info = init_leap_s_for_ctimeRefEpoch([2000, 1, 1, 0, 0, 0],
                                            epoch_for_ctime_is_actual_UTC=True)
    o_data["epoch_ctime"], _ = UTC_DT_to_ctime(eeUDT, 's', leap_s_info)

    output["Global_Attributes"] = ({
                  "object_name": json_data[-1]["OBJECT_NAME"],
                  "object_ID": json_data[-1]["OBJECT_ID"],
                  "NORAD_cat_ID": json_data[-1]["NORAD_CAT_ID"],
                  "launch_date": json_data[-1]["LAUNCH_DATE"],
                  "file_name": outp_nc_fn,
                  "UTC_of_file_creation": now_UTC_strrep,
                  "ctime_coverage_start_s": o_data["epoch_ctime"][0],
                  "ctime_coverage_end_s": o_data["epoch_ctime"][-1],
                  "UTC_coverage_start": eeUDT[0].strftime(
                                                       "%Y-%m-%dT%H:%M:%S.%f"),
                  "UTC_coverage_end": eeUDT[-1].strftime(
                                                       "%Y-%m-%dT%H:%M:%S.%f"),
                  "netCDF_lib_version": netCDF4.getlibversion().split()[0] })

    o_data["mean_motion"] = np.array([float(json_data[i]["MEAN_MOTION"])
                   for i in range(n_raw_elset) if is_part[i]])  # [orbits day-1]
    o_data["eccentricity"] = np.array([float(json_data[i]["ECCENTRICITY"])
                              for i in range(n_raw_elset) if is_part[i]])  # [-]
    o_data["inclination"] = np.array([float(json_data[i]["INCLINATION"])
                        for i in range(n_raw_elset) if is_part[i]])  # [degrees]
    o_data["RA_of_asc_node"] = np.array([float(json_data[i]["RA_OF_ASC_NODE"])
                        for i in range(n_raw_elset) if is_part[i]])  # [degrees]
    o_data["arg_of_pericenter"] = np.array(
                                  [float(json_data[i]["ARG_OF_PERICENTER"])
                        for i in range(n_raw_elset) if is_part[i]])  # [degrees]
    o_data["mean_anomaly"] = np.array([float(json_data[i]["MEAN_ANOMALY"])
                        for i in range(n_raw_elset) if is_part[i]])  # [degrees]
    o_data["rev_at_epoch"] = np.array([int(json_data[i]["REV_AT_EPOCH"])
                              for i in range(n_raw_elset) if is_part[i]])  # [-]
    o_data["bstar"] = np.array([float(json_data[i]["BSTAR"])
                      for i in range(n_raw_elset) if is_part[i]])  # [1/r_Earth]
    o_data["mean_motion_dot"] = np.array(
                          [float(json_data[i]["MEAN_MOTION_DOT"])
                   for i in range(n_raw_elset) if is_part[i]])  # [orbits day-2]
    o_data["semimajor_axis"] = np.array([float(json_data[i]["SEMIMAJOR_AXIS"])
                             for i in range(n_raw_elset) if is_part[i]])  # [km]
    o_data["period"] = np.array([float(json_data[i]["PERIOD"])*minute_to_s
                              for i in range(n_raw_elset) if is_part[i]])  # [s]
    o_data["apoapsis"] = np.array([float(json_data[i]["APOAPSIS"])
                             for i in range(n_raw_elset) if is_part[i]])  # [km]
    o_data["periapsis"] = np.array([float(json_data[i]["PERIAPSIS"])
                             for i in range(n_raw_elset) if is_part[i]])  # [km]
    o_data["TLE_line1"] = np.array([json_data[i]["TLE_LINE1"]
                                    for i in range(n_raw_elset) if is_part[i]])
    o_data["TLE_line2"] = np.array([json_data[i]["TLE_LINE2"]
                                    for i in range(n_raw_elset) if is_part[i]])

    output["Data"] = o_data

    outp_nc_fpath = os.path.join(cfg_d["output_path"], outp_nc_fn)
    write_data_fromspec(output, outp_nc_fpath, cfg_d["output_filespecs_fpath"],
                        verbose=True)
        

#-----------------------------------------------------------------------------
if __name__ == "__main__":
   # Process arguments:
    arg_description = ("Reformat an ELSET (element set) JSON-format file into "
                       "a NetCDF-format file.")
    arg_parser = argparse.ArgumentParser(description=arg_description)
    arg_parser.add_argument("common_path",
                            help="Absolute path of the parent directory "
                                 "beneath which clones of the PREFIRE_tools "
                                 "and PREFIRE_PRD_GEN repos are located.")
    arg_parser.add_argument("input_fpath",
                            help="Absolute or relative filepath of the input "
                                 "JSON-format ELSET file.")

    args = arg_parser.parse_args()

    cfg_d = {}
    cfg_d["common_path"] = args.common_path
    cfg_d["input_fpath"] = args.input_fpath

    cfg_d["output_path"] = '.'
    cfg_d["output_filespecs_fpath"] = "ELSET_filespecs.json"

    main(cfg_d)
