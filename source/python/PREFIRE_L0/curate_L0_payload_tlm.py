"""
Read TIRS science packets (only) from raw sample Level-0 payload telemetry
file(s), create a curated version (i.e., packets with incorrect timestamps
removed, and all the packets chronologically ordered) of all packets within a
single (UTC) day, and write a curated raw L0-payload telemetry file.

This program requires python version 3.7 or later, and is importable as a 
python module.
"""

  # From the Python standard library:
import os
import datetime
import itertools

  # From other external Python packages:
import numpy as np

  # Custom utilities:
import PREFIRE_tools.TIRS.TIRS_packet as TIRSp
import PREFIRE_tools.utils.CCSDS_packet_header as Cph
from PREFIRE_tools.utils.time import ctime_to_UTC_DT, UTC_DT_to_ctime


#--------------------------------------------------------------------------
def proc_raw_payload_tlm(input_fpath, leap_s_info, bytesize_of_CCSDS_hdr,
                         payload_scipkt_buffinfo, sensor_IDval):
    """Initial processing for a single raw payload telemetry file."""

    nonscipkt_log = []  # For logging non-science (and/or invalid) packets

    ctime_s = []             #
    scidat_A = []            # Initialize
    scidat_B = []            #
    PPS_ctime_mismatch = []  #

    in_f = open(input_fpath, "rb")

    while True:
        scipkt_data_t = TIRSp.read_one_scipkt(in_f, bytesize_of_CCSDS_hdr,
                                              payload_scipkt_buffinfo,
                                              nonscipkt_log, leap_s_info)

        if scipkt_data_t[0] is None:
            print("Input file appears to not have any more packets.")
            break

        ctime_s.append(scipkt_data_t[3])
        scidat_A.append(scipkt_data_t[0])
        scidat_B.append(scipkt_data_t[1])
        PPS_ctime_mismatch.append(scipkt_data_t[4])

    in_f.close()

    answer = ({"scidat_A": scidat_A, "scidat_B": scidat_B,
               "ctime_s": ctime_s, "nonscipkt_log": nonscipkt_log,
               "PPS_ctime_mismatch": PPS_ctime_mismatch})

    return answer


#--------------------------------------------------------------------------
def curate_L0_payload_tlm(leap_s_info, dict_cfg=None, debug=False):
    """Driver routine."""

    #-- Input parameter(s):
    # leap_s_info : dict
    #      leap-second reference dictionary
    # dict_cfg : dict (optional)
    #      dictionary containing configuration information (overrides all/any
    #      configuration information conveyed via environment variables)
    #
    #-- Output:
    # * Writes a binary stream of curated science packet data to a file.
    # * If dict_cfg is not None, returns the output filepath string.

    # Some useful information about a CCSDS header (in general):
    bytesize_of_CCSDS_hdr = Cph.CCSDS_header_specs()
    
    # Some useful information about a TIRS science packet (in general):
    payload_scipkt_buffinfo = TIRSp.get_scipkt_bytebuffer_indices(
                                                         bytesize_of_CCSDS_hdr)

    # Determine input filepaths and other info:
    #  input_fpaths : list of input filepaths
    #  tmp_dtrange_str : string specifying the datetime range to curate, should
    #                    either be a UTC datetime range specified as
    #      "2022-09-29T00:00:00.000->2022-09-29T23:59:59.999"
    #    -OR-
    #      "USE_DETECTED_BOUNDS" (which uses +/-30 days of the median datetime)
    try:
        input_fpaths = sorted(dict_cfg["tgt_L0_pld_fpaths"])  # list or tuple
        tmp_dtrange_str = dict_cfg["tgt_L0_pld_dtrange"]
        output_dir = dict_cfg["output_dir"]
        output_fn_prefix = dict_cfg["output_fn_prefix"]
    except:
        tmp_in_fpaths, tmp_dtrange_str = (
                           os.environ["TGT_L0_PLD_FPATHS_DTRANGE"].split("||"))
        input_fpaths = sorted([x.strip() for x in tmp_in_fpaths.split(',')])
        output_dir = os.environ["OUTPUT_DIR"]
        output_fn_prefix = ''

    # Set sensor and spacecraft ID values and string representations:
    #  Expects input filename to be like
    #     prefire_01_payload_tlm_2022_09_26_19_06_58.bin
    chk_l = [(x[-7] == '_') for x in input_fpaths]
    if not all(chk_l):
        raise ValueError("All input filenames must have the (uncurated) form "
                         "'prefire_0*_payload_tlm_YYYY_MM_DD_hh_mm_ss.bin'")
    tmp = os.path.basename(input_fpaths[0]).split("_payload")
    val_str = tmp[0].split('_')[-1]
    spacecraft_ID = "PREFIRE{}".format(val_str)
    sensor_IDval = int(val_str)-1
    sensor_ID = "TIRS{}".format(val_str)

    # Initial packet processing for all given input files:
    res_dl = []
    for i_f in range(len(input_fpaths)):
        res_dl.append(proc_raw_payload_tlm(input_fpaths[i_f], leap_s_info,
                 bytesize_of_CCSDS_hdr, payload_scipkt_buffinfo, sensor_IDval))

    # Construct a composite time-series of ctime values in the input files, then
    #  sort it by ascending time order:
    ctime_s_raw = np.array(list(itertools.chain.from_iterable(res["ctime_s"]
                                                           for res in res_dl)))
#%    ctime_misma_raw = np.array(list(itertools.chain.from_iterable(
#%                                 res["PPS_ctime_mismatch"] for res in res_dl)))
    sorted_inds_full = np.argsort(ctime_s_raw)
    raw_ctime_sorted = ctime_s_raw[sorted_inds_full]
#%    raw_ctime_misma_sorted = ctime_misma_raw[sorted_inds_full]

    # Detect and remove any duplicates:
    dedup_threshold_t = (2.e-5, 1.e-5)
    dcheck = np.append(np.array(dedup_threshold_t[0]),
                       np.diff(raw_ctime_sorted))
    dcheck_bool = (dcheck > dedup_threshold_t[1])  # Is this element unique?
    ctime_s_unique = np.compress(dcheck_bool, raw_ctime_sorted, axis=0)
#%    ctime_misma_unique = np.compress(dcheck_bool, raw_ctime_misma_sorted,
#%                                     axis=0)
    if debug:
        for i in range(len(ctime_s_unique)-1):
            if (ctime_s_unique[i+1]-ctime_s_unique[i] > TIRSp.ROIC_tau*1.01 or
                  ctime_s_unique[i+1]-ctime_s_unique[i] < TIRSp.ROIC_tau*0.99):
                print("unusual packet delta-t", i,
                      ctime_s_unique[i+1]-ctime_s_unique[i],
                      ctime_s_unique[i], ctime_s_unique[i+1])
    print("{} duplicate packets were detected (all: {}, unique: {})".format(
              len(raw_ctime_sorted)-len(ctime_s_unique), len(raw_ctime_sorted),
                                                          len(ctime_s_unique)))

    if tmp_dtrange_str == "USE_DETECTED_BOUNDS":
        ctime_s_mid = ctime_s_unique[len(ctime_s_unique)//2]
        reasonable_time_margin_s = 30.*86400.  # [s] 30 days
        tgt_ctime_s_bounds = [ctime_s_mid-reasonable_time_margin_s,
                              ctime_s_mid+reasonable_time_margin_s]  # [s]
    else:
        tmp_l = tmp_dtrange_str.strip().split("->")
        tgt_UTC_DT_bounds = [datetime.datetime.fromisoformat(tmp_l[0]+"+00:00"),
                             datetime.datetime.fromisoformat(tmp_l[1]+"+00:00")]
        tgt_ctime_s_bounds = UTC_DT_to_ctime(tgt_UTC_DT_bounds, 's',
                                             leap_s_info)[0]  # [s]

    # Subset the data to within the target date (also removes any
    #  spuriously-datestamped packets):
    ib = np.searchsorted(ctime_s_unique, tgt_ctime_s_bounds[0], side="left")
    ie = np.searchsorted(ctime_s_unique, tgt_ctime_s_bounds[1],
                         side="left")  # NumPy indexing
    dcheck_bool_subset = dcheck_bool.copy()
    dcheck_bool_subset[:ib] = False  # Not part of desired subset
    dcheck_bool_subset[ie:] = False  #

    ctime_s = ctime_s_unique[ib:ie]
    scidat_A_raw = np.array(list(itertools.chain.from_iterable(res["scidat_A"]
                                           for res in res_dl)), dtype="object")
    scidat_A_sorted = scidat_A_raw[sorted_inds_full]
    scidat_A = np.compress(dcheck_bool_subset, scidat_A_sorted, axis=0)
    scidat_B_raw = np.array(list(itertools.chain.from_iterable(res["scidat_B"]
                                           for res in res_dl)), dtype="object")
    scidat_B_sorted = scidat_B_raw[sorted_inds_full]
    scidat_B = np.compress(dcheck_bool_subset, scidat_B_sorted, axis=0)

    # Construct output filepath:
    input_fn = os.path.basename(input_fpaths[0])
    tmp_fn_parts = input_fn.split('_')
    outp_fn_body = '_'.join(tmp_fn_parts[0:4])
    ctime_coverage = np.array([ctime_s[0], ctime_s[-1]])  # [s]
    UTC_DT, _ = ctime_to_UTC_DT(ctime_coverage, 's', leap_s_info)
    now_UTC_DT = datetime.datetime.now(datetime.timezone.utc)
    now_UTC_strrep = now_UTC_DT.strftime("%Y-%m-%dT%H:%M:%S.%f")
    outp_fn_suffix = \
         f"_{UTC_DT[0]:%Y%m%d%H%M%S}_{UTC_DT[1]:%Y%m%d%H%M%S}_{now_UTC_DT:%Y%m%d%H%M%S}.bin"
    outp_fn = output_fn_prefix+outp_fn_body+outp_fn_suffix
    outp_fpath = os.path.join(output_dir, outp_fn)
    print(f"output fpath: {outp_fpath}")

    # Write curated stream of packets to an output file:
    with open(outp_fpath, "wb") as out_f:
        for i in range(len(scidat_A)):
            out_f.write(scidat_A[i])  # Write CCSDS header bytes
            out_f.write(scidat_B[i])  # Write remaining bytes of sci packet

    if dict_cfg is not None:
        if "output_nonscipkt_log" in dict_cfg:
            if len(res_dl) == 1:
                otmp = res_dl[0]["nonscipkt_log"]
            else:
                otmp = [res["nonscipkt_log"] for res in res_dl]
            return (outp_fpath, otmp)
        else:
            return outp_fpath
