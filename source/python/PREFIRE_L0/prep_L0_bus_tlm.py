"""
From a single Level-0 bus telemetry file, read in all bus telemetry entries,
and determine any PREFIRE granule boundaries within. Write the resulting
information to a NetCDF-format file.

Bus telemetry info from the BCT Command and Telemetry Handbook (c2023-01-13).

This program requires Python version 3.6 or later, and is importable as a
Python module.
"""

  # From the Python standard library:
import os
import sys
import datetime
import json

  # From other external Python packages:
import numpy as np
import pandas as pd
import netCDF4

  # Custom utilities:
import PREFIRE_tools.utils.unit_conv as uc
import PREFIRE_tools.utils.exceptions as exc
from PREFIRE_tools.utils.filesys import mkdir_p
from PREFIRE_tools.utils.time import ctime_to_UTC_DT, UTC_DT_to_ctime
from PREFIRE_PRD_GEN.file_creation import write_data_fromspec
import PREFIRE_L0.filepaths as L0_fpaths


rd_d = {"ECI_X": 0, "ECI_Y": 1, "ECI_Z": 2, "SUN": 3, "MAG": 4, "MOON": 5,
        "POS": 6, "VEL": 7, "TARG_ECI": 8, "TARG_ECEF": 9, "BEARING": 10,
        "HEADING": 11, "ORB_NORM": 12, "GCNADIR": 13, "GDNADIR": 14}

dfcol_ref = {"REFS_REFS_VALID": ("na_boolean", "REFS_is_valid", None),
             "REFS_ESM_VALID": ("na_boolean", "REFS_ESM_is_valid", None),
             "REFS_BETA_ANGLE": ("numeric1", "beta_angle", "rad_to_deg"),
             "REFS_SUN_ECLIPSE_EARTH_PENUMBRA_FLAG": ("boolean",
                                                 "SC_in_Earth_penumbra", None),
             "REFS_SUN_ECLIPSE_EARTH_UMBRA_FLAG": ("boolean",
                                                   "SC_in_Earth_umbra", None),
             "REFS_SUN_ECLIPSE_MOON_PENUMBRA_FLAG": ("boolean",
                                                  "SC_in_moon_penumbra", None),
             "REFS_SUN_ECLIPSE_MOON_UMBRA_FLAG": ("boolean",
                                                  "SC_in_moon_umbra", None),
             "REFS_POSITION_WRT_ECI1": ("numeric2", "position_wrt_ECI_1", None),
             "REFS_POSITION_WRT_ECI2": ("numeric2", "position_wrt_ECI_2", None),
             "REFS_POSITION_WRT_ECI3": ("numeric2", "position_wrt_ECI_3", None),
             "REFS_VELOCITY_WRT_ECI1": ("numeric1", "velocity_wrt_ECI_1", None),
             "REFS_VELOCITY_WRT_ECI2": ("numeric1", "velocity_wrt_ECI_2", None),
             "REFS_VELOCITY_WRT_ECI3": ("numeric1", "velocity_wrt_ECI_3", None),
             "REFS_ALTITUDE": ("numeric1", "ref_altitude", None),
             "REFS_LATITUDE": ("numeric1", "ref_latitude", "rad_to_deg"),
             "REFS_LONGITUDE": ("numeric1", "ref_longitude", "rad_to_deg"),
             "REFS_MODELED_SUN_VECTOR_BODY1": ("numeric1",
                                             "mod_SC_sun_vec_wrt_SBF_1", None),
             "REFS_MODELED_SUN_VECTOR_BODY2": ("numeric1",
                                             "mod_SC_sun_vec_wrt_SBF_2", None),
             "REFS_MODELED_SUN_VECTOR_BODY3": ("numeric1",
                                             "mod_SC_sun_vec_wrt_SBF_3", None),
             "REFS_SUN_MODEL_VECTOR_ECI1": ("numeric2",
                                            "mod_SC_sun_vec_wrt_ECI_1", None),
             "REFS_SUN_MODEL_VECTOR_ECI2": ("numeric2",
                                            "mod_SC_sun_vec_wrt_ECI_2", None),
             "REFS_SUN_MODEL_VECTOR_ECI3": ("numeric2",
                                            "mod_SC_sun_vec_wrt_ECI_3", None),
             "REFS_MOON_VECTOR_BODY1": ("numeric1",
                                        "mod_SC_moon_vec_wrt_SBF_1", None),
             "REFS_MOON_VECTOR_BODY2": ("numeric1",
                                        "mod_SC_moon_vec_wrt_SBF_2", None),
             "REFS_MOON_VECTOR_BODY3": ("numeric1",
                                        "mod_SC_moon_vec_wrt_SBF_3", None),
             "REFS_MOON_MODEL_VECTOR_ECI1": ("numeric2",
                                             "mod_SC_moon_vec_wrt_ECI_1", None),
             "REFS_MOON_MODEL_VECTOR_ECI2": ("numeric2",
                                             "mod_SC_moon_vec_wrt_ECI_2", None),
             "REFS_MOON_MODEL_VECTOR_ECI3": ("numeric2",
                                             "mod_SC_moon_vec_wrt_ECI_3", None),
             "REFS_NADIR_VECTOR_BODY1": ("numeric1", "nadir_vec_wrt_SBF_1",
                                         None),
             "REFS_NADIR_VECTOR_BODY2": ("numeric1", "nadir_vec_wrt_SBF_2",
                                         None),
             "REFS_NADIR_VECTOR_BODY3": ("numeric1", "nadir_vec_wrt_SBF_3",
                                         None),
             "ATT_DET_Q_BODY_WRT_ECI1": ("numeric1", "q_scbody_wrt_ECI_1",
                                         None),
             "ATT_DET_Q_BODY_WRT_ECI2": ("numeric1", "q_scbody_wrt_ECI_2",
                                         None),
             "ATT_DET_Q_BODY_WRT_ECI3": ("numeric1", "q_scbody_wrt_ECI_3",
                                         None),
             "ATT_DET_Q_BODY_WRT_ECI4": ("numeric1", "q_scbody_wrt_ECI_4",
                                         None),
             "ATT_DET_ATTITUDE_VALID": ("na_boolean", "ATT_DET_is_valid", None),
             "ATT_CMD_PRI_REF_DIR": ("rd_string", "pri_cmd_ref_dir", None),
             "ATT_CMD_PRI_CMD_VEC_BODY1": ("numeric1", "pri_cmd_vec_wrt_SBF_1",
                                           None),
             "ATT_CMD_PRI_CMD_VEC_BODY2": ("numeric1", "pri_cmd_vec_wrt_SBF_2",
                                           None),
             "ATT_CMD_PRI_CMD_VEC_BODY3": ("numeric1", "pri_cmd_vec_wrt_SBF_3",
                                           None),
             "ATT_CMD_SEC_REF_DIR": ("rd_string", "sec_cmd_ref_dir", None),
             "ATT_CMD_SEC_CMD_VEC_BODY1": ("numeric1", "sec_cmd_vec_wrt_SBF_1",
                                           None),
             "ATT_CMD_SEC_CMD_VEC_BODY2": ("numeric1", "sec_cmd_vec_wrt_SBF_2",
                                           None),
             "ATT_CMD_SEC_CMD_VEC_BODY3": ("numeric1", "sec_cmd_vec_wrt_SBF_3",
                                           None),
             "ATT_CMD_CMD_TARGET1": ("numeric2", "cmd_tgt_vec_1", None),
             "ATT_CMD_CMD_TARGET2": ("numeric2", "cmd_tgt_vec_2", None),
             "ATT_CMD_CMD_TARGET3": ("numeric2", "cmd_tgt_vec_3", None),
             "ATT_CMD_CMD_Q_BODY_WRT_ECI1": ("numeric1",
                                             "cmd_q_scbody_wrt_ECI_1", None),
             "ATT_CMD_CMD_Q_BODY_WRT_ECI2": ("numeric1",
                                             "cmd_q_scbody_wrt_ECI_2", None),
             "ATT_CMD_CMD_Q_BODY_WRT_ECI3": ("numeric1",
                                             "cmd_q_scbody_wrt_ECI_3", None),
             "ATT_CMD_CMD_Q_BODY_WRT_ECI4": ("numeric1",
                                             "cmd_q_scbody_wrt_ECI_4", None),
             "RADIO_SDR_TX": ("boolean", "radio_is_tx", None),
             "RADIO_SDR_RX_LOCK": ("boolean", "radio_rx_lock", None),
             "RADIO_SDR_TEMP": ("numeric1", "radio_T", "degC_to_K"),
             "POWER_IO5_PAYLOAD_PWR": ("boolean1", "payload_is_on", None),
             "ANALOGS_PL_TIRS_TEMP1": ("numeric1", "pladj_T_1", "degC_to_K"),
             "ANALOGS_PL_TIRS_TEMP2": ("numeric1", "pladj_T_2", "degC_to_K"),
             "ANALOGS_BUS_TEMP": ("numeric1", "bus_T", "degC_to_K"),
             "ANALOGS_IMU_TEMP": ("numeric1", "IMU_T", "degC_to_K"),
             "ANALOGS_PL_COMMAND_TEMP": ("numeric1", "plcmd_T", "degC_to_K"),
             "ANALOGS_PL_POWER_TEMP": ("numeric1", "plpwr_T", "degC_to_K"),
             "ANALOGS_BATTERY1_TEMP": ("numeric1", "battery_T", "degC_to_K"),
             "ANALOGS_BATTERY_VOLTAGE": ("numeric1", "battery_V", None),
             "ANALOGS_BATTERY_1_CURRENT": ("numeric1", "battery_I", None),
             "GPS_GPS_VALID": ("boolean", "GPS_is_valid", None),
             "GPS_MSG_TRACKED_SATELLITES": ("numeric12", "GPS_sats_tracked",
                                            None),
             "CSS_RAW_SUN_SENSOR_DATA12": ("numeric11", "raw_photodiode_space",
                                           None),
             "CSS_RAW_SUN_SENSOR_DATA15": ("numeric11", "raw_photodiode_nadir",
                                           None),
             "ATT_CTRL_SUN_AVOID_FLAG": ("boolean", "MSA_action_occurring",
                                         None)
             }

dfcol_converter = {
     "numeric1": lambda x: x if not (isinstance(x, np.ndarray) or
                                     isinstance(x, str)) else -9.999e3,
     "numeric2": lambda x: x if not (isinstance(x, np.ndarray) or
                                     isinstance(x, str)) else -9.999e4,
     "numeric11": lambda x: x if not (isinstance(x, np.ndarray) or
                                      isinstance(x, str)) else -9999,
     "numeric12": lambda x: x if not (isinstance(x, np.ndarray) or
                                      isinstance(x, str)) else -99,
     "string": lambda x: x if isinstance(x, str) else np.nan,
     "rd_string": lambda x: -99 if not isinstance(x, str) else (rd_d[x] if not x.isnumeric() else -99),
     "na_boolean": lambda x: ( x == "YES" ) if isinstance(x, str) else np.nan,
     "boolean": lambda x: ( x == "YES" ) if isinstance(x, str) else -99,
     "boolean1": lambda x: ( x == "ON" ) if isinstance(x, str) else -99}


#--------------------------------------------------------------------------
def _get_bus_tlm_fields(df, leap_s_info, ofspecs):
    """Get all relevant bus telemetry fields."""

    fs = ofspecs["SCbus_L0_Data"]

    o_data = {}

    # Original input field "ft" is now the DatetimeIndex of this DataFrame.
    #  Recast its datetimes as formatted integers:
    vn = "UTC_datetime_repr"
    np_str_a = np.array([x.strftime("%Y%m%d%H%M%S%f") for x in
                                                            df.index.tolist()])
    np_str_at = np.empty((len(np_str_a),), dtype='<U17')  # Init 17-char array
    np_str_at[:] = np_str_a[:]  # Truncate strings to 17 chars
    all_UTC_datetime_int = np_str_at.astype(fs[vn]["np_dtype"])  # str -> dtype

    all_n_SCbus_tlm_entries = len(all_UTC_datetime_int)

    # Input field "TIME_RTC_TAI_SECOND": continuous_time referenced to
    #  a naive, "faux-UTC" epoch (ctimeN; [seconds since 2000-01-01T00:00:00])
    #  *** Appears to be unreliable, use UTC time ***
#    tmp_field1 = df["TIME_RTC_TAI_SECOND"].to_numpy(dtype="int64")
    # Input field "TIME_RTC_TAI_SUBSEC": indicator of continuous_time subsecond
    #  fraction:  *** Appears to be unreliable, use UTC fractional seconds ***
#    tmp_field2 = (np.mod(df["TIME_RTC_TAI_SUBSEC"].to_numpy(dtype="int8"), 5)*
#                  0.2).astype("float64")  # [s]
#    ctimeN_s = tmp_field1+tmp_field2  # [s]
    tmp_field1 = np.array([x.to_pydatetime() for x in df.index.tolist()])

    # Continuous_time referenced to an actual-UTC epoch
    #  [seconds since 2000-01-01T00:00:00 UTC]:
#    all_ctime_s = ctimeN_to_ctime(ctimeN_s, 's', leap_s_info)
    all_ctime_s, _ = UTC_DT_to_ctime(tmp_field1, 's', leap_s_info)

    n_SCbus_tlm_entries = all_n_SCbus_tlm_entries

    # Store output time fields:
    o_data["UTC_datetime_repr"] = all_UTC_datetime_int[:]
    o_data["ctime"] = all_ctime_s[:]  # [s since 2000-01-01T00:00:00 UTC]

    for tlm_mnk in dfcol_ref:
        _, vn, proc_type = dfcol_ref[tlm_mnk]
        if proc_type == "rad_to_deg":  # [radians] -> [deg
            a_tmp = (df[tlm_mnk].to_numpy(dtype=fs[vn]["np_dtype"],
                                       na_value=fs[vn]["fill_value"])[:])
            o_data[vn] = np.where(a_tmp > fs[vn]["fill_value"],
                                  np.rad2deg(a_tmp), a_tmp)  # [degrees]
        elif proc_type == "degC_to_K":  # [deg_C] -> [K]
            a_tmp = (df[tlm_mnk].to_numpy(dtype=fs[vn]["np_dtype"],
                                       na_value=fs[vn]["fill_value"])[:])
            o_data[vn] = np.where(a_tmp > fs[vn]["fill_value"],
                                  a_tmp+273.15, a_tmp)  # [K]
        else:
            o_data[vn] = (df[tlm_mnk].to_numpy(dtype=fs[vn]["np_dtype"],
                                       na_value=fs[vn]["fill_value"])[:])

    return (n_SCbus_tlm_entries, o_data)


#--------------------------------------------------------------------------
def proc_raw_bus_tlm(input_fpath0, leap_s_info, ofspecs, output_dir):
    """General processing for a single raw bus telemetry file."""

    #== Read in all bus telemetry entries, put them in a pandas.DataFrame:
     # Read in raw bus telemetry entries, then "massage" them into a
     #  more-usable format:
    input_fpath = input_fpath0
       # The pandas .agg() will not work with an input file that has any missing
       #  columns in the first data row.  Check for this, and mitigate it if
       #  possible:
    with open(input_fpath, "rt") as f:
        header = f.readline()  # Read header
        test_line = f.readline()
        needs_repaired = (",," in test_line)
        fixable = True  # Default assumption
        while ",," in test_line:
            try:
                test_line = f.readline()
            except:
                fixable = False
                break  # The file does not appear to be fixable
        if needs_repaired and fixable:
            # Write and use a "repaired" file:
            tmp_fpath = os.path.join(output_dir,
                                     "tmp-"+os.path.basename(input_fpath))
            with open(tmp_fpath, "wt") as tf:
                tf.write(header)
                tf.write(test_line)
                tf.writelines(f.readlines())
            input_fpath = tmp_fpath
    df_tmp = pd.read_csv(input_fpath, parse_dates=["ft"])  # pandas DataFrame
    if len(df_tmp.index) == 0:
        raise exc.NoValidInputData
    df = df_tmp.groupby(df_tmp["ft"]).agg(lambda x: x.dropna()) # new DataFrame

    for tlm_mnk in dfcol_ref:
        t, _, _ = dfcol_ref[tlm_mnk]
        if tlm_mnk in df.columns:
            df[tlm_mnk] = df[tlm_mnk].apply(dfcol_converter[t])

    # Attempt to drop any rows that have obvious formatting issues:
    df = df.dropna(subset=["REFS_REFS_VALID", "REFS_ESM_VALID",
                           "ATT_DET_ATTITUDE_VALID"])

    #== Get number of bus telemetry entries, and get selected fields:
    n_SCbus_tlm_entries, o_data = _get_bus_tlm_fields(df, leap_s_info, ofspecs)

    answer = ({"o_data": o_data})

    return answer


#--------------------------------------------------------------------------
def prep_L0_bus_tlm(leap_s_info, L0_orbit_fpath):
    """Driver routine."""

    ### Needs to be able to handle a file with a single telemetry line, in
    ###  addition to the typical multi-line files.

    input_fpath = os.environ["TGT_L0_BUS_FPATH"].strip()

    # Determine some other input filepaths:
    anc_data_dir = os.environ["ANCILLARY_DATA_DIR"]
    filespecs_fpath = os.path.join(anc_data_dir, "bus_tlm_filespecs.json")

    # Load the output filespecs:
    with open(filespecs_fpath, 'r') as f:
        ofspecs = json.load(f)

    # Set spacecraft ID value and string representation:
    #  Expects filename to be like
    #     prefire_01_bus_tlm_20220928200813_20220929002748_20230330143233.csv
    tmp = os.path.basename(input_fpath.split("_bus")[0])
    val_str = tmp.split('_')[-1]
    spacecraft_ID = "PREFIRE{}".format(val_str)

    output_dir = os.environ["OUTPUT_DIR"]

    # Now the target input file can be processed:
    input_fn = os.path.basename(input_fpath)
    res_d = proc_raw_bus_tlm(input_fpath, leap_s_info, ofspecs, output_dir)

    o_data = res_d["o_data"]

    # Read in selected fields from the L0-orbit file:
    input_product_fn_l = [os.path.basename(input_fpath)]
    input_product_fn_l.append(os.path.basename(L0_orbit_fpath))

    with netCDF4.Dataset(L0_orbit_fpath, 'r') as ds:
        o_data["granule_edge_ctime"] = (ds.groups["Orbit_L0_Data"].
                                           variables["granule_edge_ctime"][...])
        o_data["granule_ID"] = (ds.groups["Orbit_L0_Data"].
                                                   variables["granule_ID"][...])

    #== Determine output filepaths:

    outp_nc_fn = input_fn.replace(".csv", ".nc")
    outp_nc_fpath = os.path.join(output_dir, outp_nc_fn)

    #== Determine/set some global/group attribute values:

    product_full_version = os.environ["PRODUCT_FULLVER"].strip()

    orbit_sim_version = os.environ["ORBSIM_VERSION"].strip()
    if len(orbit_sim_version) == 0:
        orbit_sim_version = ' '

    ctime_coverage = np.array([o_data["ctime"][0], o_data["ctime"][-1]])  # [s]
    UTC_DT, _ = ctime_to_UTC_DT(ctime_coverage, 's', leap_s_info)
    UTC_coverage = ([UTC_DT[0].strftime("%Y-%m-%dT%H:%M:%S.%f"),
                     UTC_DT[1].strftime("%Y-%m-%dT%H:%M:%S.%f")])

    now_UTC_DT = datetime.datetime.now(datetime.timezone.utc)
    now_UTC_strrep = now_UTC_DT.strftime("%Y-%m-%dT%H:%M:%S.%f")

    with open(L0_fpaths.scipkg_prdgitv_fpaths[2], 'r') as in_f:
        line_parts = in_f.readline().split('(', maxsplit=1)
        this_pkg_provenance = "{}{} ( {}".format(line_parts[0],
                                                 product_full_version,
                                                 line_parts[1].strip())

    with open(L0_fpaths.scipkg_version_fpath, 'r') as in_f:
        proc_algID = in_f.readline().strip()

    #== Write to NetCDF-format file:

    output = {}
    output["Global_Attributes"] = ({
                   "full_versionID": os.environ["PRODUCT_FULLVER"],
                   "granule_type": "0-BUS-TLM",
                   "granule_ID": ' ',
                   "provenance": this_pkg_provenance,
                   "file_name": os.path.basename(outp_nc_fpath),
                   "input_product_files": ', '.join(input_product_fn_l),
                   "processing_algorithmID": proc_algID,
                   "UTC_of_file_creation": now_UTC_strrep,
                   "spacecraft_ID": spacecraft_ID,
                   "ctime_coverage_start_s": ctime_coverage[0],
                   "ctime_coverage_end_s": ctime_coverage[1],
                   "UTC_coverage_start": UTC_coverage[0],
                   "UTC_coverage_end": UTC_coverage[1],
                   "netCDF_lib_version": netCDF4.getlibversion().split()[0],
                   "orbit_sim_version": orbit_sim_version })
    output["SCbus_L0_Data"] = o_data
    
    mkdir_p(os.path.dirname(outp_nc_fpath))

    write_data_fromspec(output, outp_nc_fpath, filespecs_fpath, verbose=True)
