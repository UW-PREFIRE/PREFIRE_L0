"""
From a single Level-0 payload telemetry file, read in all payload telemetry
packets.  Write the resulting information (partly-raw, partly-expanded) to a
NetCDF-format file.

This program requires Python version 3.6 or later, and is importable as a
Python module.
"""

  # From the Python standard library:
import os
import datetime

  # From other external Python packages:
import numpy as np
import netCDF4

  # Custom utilities:
import PREFIRE_tools.TIRS.TIRS_packet as TIRSp
import PREFIRE_tools.utils.CCSDS_packet_header as Cph
import PREFIRE_tools.utils.unit_conv as uc
from PREFIRE_tools.utils.filesys import mkdir_p
from PREFIRE_tools.utils.time import ctime_to_UTC_DT, ctimeN_to_ctime
from PREFIRE_PRD_GEN.file_creation import write_data_fromspec
import PREFIRE_L0.filepaths as L0_fpaths
from PREFIRE_L0.curate_L0_payload_tlm import curate_L0_payload_tlm


#--------------------------------------------------------------------------
def _process_scibuff_set(scidat_set, payload_scipkt_buffinfo, o_data):
    """Process a set of science packet buffers/info, augmenting 'o_data'."""

    n_looks = len(scidat_set)
    if n_looks == 0:
        return (n_looks, -9999., -9999.)  # Nothing more to do here
    
    ctime_s = np.array([xdat[3] for xdat in scidat_set], dtype="float64")
    encpos = np.array([xdat[2] for xdat in scidat_set], dtype="uint16")
    sci_buffer_l = [xdat[1] for xdat in scidat_set]

    scibuff_t = TIRSp.extract_from_sci_buffer(sci_buffer_l,
                                              payload_scipkt_buffinfo)

    o_data["ctime"] = ctime_s
    o_data["CDH_T"] = scibuff_t[3]
    o_data["ROIC_T"] = scibuff_t[4]
    o_data["TIRS_T"] = scibuff_t[5]
    o_data["MoE_T"] = scibuff_t[6]
    o_data["PDU_12V_I"] = scibuff_t[7]
    o_data["PDU_SCBATT_I"] = scibuff_t[8]
    o_data["MoE_12V_I"] = scibuff_t[9]
    o_data["encoder_pos"] = encpos
    o_data["engdata_tlm"] = scibuff_t[0]
    o_data["misc_tlm"] = scibuff_t[1]
    o_data["adj_srd_DN"] = scibuff_t[2]

    return (n_looks, ctime_s[0], ctime_s[-1])


#--------------------------------------------------------------------------
def _process_other_set(scidat_set, o_data):
    """Process a set of non-science (and/or invalid) packet info, augmenting
        'o_data'.
    """

    n_looks = len(scidat_set)
    if n_looks == 0:
        return n_looks  # Nothing more to do here
    
    APID = np.empty((n_looks,), dtype="uint16")
    byte_startpos = np.empty((n_looks,), dtype="int32")
    nom_bytesize = np.empty((n_looks,), dtype="uint16")
    info_flag = np.empty((n_looks,), dtype="int8")

    i = 0
    for apid_p, bsp, nbs, ef in scidat_set:
        APID[i] = apid_p
        byte_startpos[i] = bsp
        nom_bytesize[i] = nbs
        info_flag[i] = ef
        i += 1

    o_data["otherpkt_APID"] = APID
    o_data["otherpkt_byte_startpos"] = byte_startpos
    o_data["otherpkt_nom_bytesize"] = nom_bytesize
    o_data["otherpkt_info_flag"] = info_flag

    return n_looks


#--------------------------------------------------------------------------
def proc_raw_payload_tlm(input_fpath, leap_s_info, bytesize_of_CCSDS_hdr,
                         payload_scipkt_buffinfo, sensor_IDval):
    """Initial processing for a single raw payload telemetry file."""

    nonscipkt_log = []  # For logging non-science (and/or invalid) packets
    scidat = []  # Initialize science packet data list

    in_f = open(input_fpath, "rb")

    scipkt_cnt = -1
    while True:
        scipkt_data_t = TIRSp.read_one_scipkt(in_f, bytesize_of_CCSDS_hdr,
                                              payload_scipkt_buffinfo,
                                              nonscipkt_log, leap_s_info)

        if scipkt_data_t[0] is None:
            print("Input file appears to not have any more packets.")
            break

        scipkt_cnt += 1
        scidat.append((scipkt_cnt, scipkt_data_t[1], scipkt_data_t[2],
                       scipkt_data_t[3]))

    in_f.close()

    answer = ({"scipkt_cnt": scipkt_cnt,
               "scidat": scidat,
               "nonscipkt_log": nonscipkt_log})

    return answer


#--------------------------------------------------------------------------
def prep_L0_payload_tlm(leap_s_info):
    """Driver routine."""

    # Some useful information about a CCSDS header (in general):
    bytesize_of_CCSDS_hdr = Cph.CCSDS_header_specs()

    # Some useful information about a TIRS science packet (in general):
    payload_scipkt_buffinfo = TIRSp.get_scipkt_bytebuffer_indices(
                                                         bytesize_of_CCSDS_hdr)

   #== Read in all payload telemetry science packets and separate them into two
   #==  categories: science and other

    input_fpath = os.environ["TGT_L0_PAYLOAD_FPATH"].strip()

    #== Partly-determine output filepaths:
    input_fn = os.path.basename(input_fpath)
    outp_nc_fn = input_fn.replace(".bin", ".nc")
    tmp_fn_parts = input_fn.split('_')
    outp_fn_body = '_'.join(tmp_fn_parts[0:4])
    output_dir = os.environ["OUTPUT_DIR"]

    uncurated_input = (len(os.path.basename(input_fpath)) == 46)

    rec_input_fn = os.path.basename(input_fpath)

    # Set sensor and spacecraft ID values and string representations:
    #
    #  Expects input filename to be like
    #   prefire_01_payload_tlm_2022_09_26_19_06_58.bin
    #    -or-
    #   prefire_02_payload_tlm_20221029000000_20221029235958_20240320203522.bin
    tmp = rec_input_fn.split("_payload")
    val_str = tmp[0].split('_')[-1]
    spacecraft_ID = "PREFIRE{}".format(val_str)
    sensor_IDval = int(val_str)-1
    sensor_ID = "TIRS{}".format(val_str)

    nonscipkt_log = []
    if uncurated_input:
        # Create and write an (intermediate) curated form of the input file's
        #  data, then replace 'input_fpath' with the filepath of the curated
        #  data:
        cfg = {}
        cfg["tgt_L0_pld_fpaths"] = [input_fpath]
        cfg["tgt_L0_pld_dtrange"] = "USE_DETECTED_BOUNDS"
        cfg["output_dir"] = output_dir
        cfg["output_fn_prefix"] = "tmp_curated-"
        cfg["output_nonscipkt_log"] = True
        input_fpath, nonscipkt_log = curate_L0_payload_tlm(leap_s_info,
                                                           dict_cfg=cfg)

    # Now the target input file can be processed:
    res_d = proc_raw_payload_tlm(input_fpath, leap_s_info,
                  bytesize_of_CCSDS_hdr, payload_scipkt_buffinfo, sensor_IDval)
    if res_d["scipkt_cnt"] == -1:
        raise RuntimeError("No valid science data packets were found.")

    scidat = res_d["scidat"]
    o_data = {}

    # Process science packet buffer data:
    n_looks, ctime_s_b, ctime_s_e = _process_scibuff_set(scidat,
                                               payload_scipkt_buffinfo, o_data)

    # Process log of non-science (or invalid) packets:
    n_other = _process_other_set(nonscipkt_log, o_data)

    #== Obtain some other filepaths:

    anc_data_dir = os.environ["ANCILLARY_DATA_DIR"]
    filespecs_fpath = os.path.join(anc_data_dir, "payload_tlm_filespecs.json")

    #== Determine/set some global/group attribute values:

    product_full_version = os.environ["PRODUCT_FULLVER"].strip()

    xt = np.array([ctime_s_b, ctime_s_e])  # [s]
    x = np.ma.masked_where(xt <= 0., xt)  # [s]
    ctime_coverage = np.array([np.amin(x), np.amax(x)])  # [s]
    UTC_DT, _ = ctime_to_UTC_DT(ctime_coverage, 's', leap_s_info)
    UTC_coverage = ([UTC_DT[0].strftime("%Y-%m-%dT%H:%M:%S.%f"),
                     UTC_DT[1].strftime("%Y-%m-%dT%H:%M:%S.%f")])

      # Finish output filepaths:
    now_UTC_DT = datetime.datetime.now(datetime.timezone.utc)
    now_UTC_strrep = now_UTC_DT.strftime("%Y-%m-%dT%H:%M:%S.%f")
    outp_fn_suffix = \
         f"_{UTC_DT[0]:%Y%m%d%H%M%S}_{UTC_DT[1]:%Y%m%d%H%M%S}_{now_UTC_DT:%Y%m%d%H%M%S}.nc"
    outp_nc_fn = outp_fn_body+outp_fn_suffix
    outp_nc_fpath = os.path.join(output_dir, outp_nc_fn)

    with open(L0_fpaths.scipkg_prdgitv_fpaths[1], 'r') as in_f:
        line_parts = in_f.readline().split('(', maxsplit=1)
        this_pkg_provenance = "{}{} ( {}".format(line_parts[0],
                                                 product_full_version,
                                                 line_parts[1].strip())

    with open(L0_fpaths.scipkg_version_fpath, 'r') as in_f:
        proc_algID = in_f.readline().strip()

    #== Write to NetCDF-format file:

    orbit_sim_version = os.environ["ORBSIM_VERSION"].strip()
    SRF_NEdR_version = os.environ["SRF_NEDR_VERSION"].strip()
    if len(orbit_sim_version) == 0:
        orbit_sim_version, SRF_NEdR_version = (' ', ' ')

    output = {}
    output["Global_Attributes"] = ({
                   "full_versionID": product_full_version,
                   "granule_type": "0-PAYLOAD-TLM",
                   "granule_ID": ' ',
                   "provenance": this_pkg_provenance,
                   "file_name": os.path.basename(outp_nc_fpath),
                   "input_product_files": rec_input_fn,
                   "processing_algorithmID": proc_algID,
                   "UTC_of_file_creation": now_UTC_strrep,
                   "spacecraft_ID": spacecraft_ID,
                   "sensor_ID": sensor_ID,
                   "ctime_coverage_start_s": ctime_coverage[0],
                   "ctime_coverage_end_s": ctime_coverage[1],
                   "UTC_coverage_start": UTC_coverage[0],
                   "UTC_coverage_end": UTC_coverage[1],
                   "netCDF_lib_version": netCDF4.getlibversion().split()[0],
                   "orbit_sim_version": orbit_sim_version,
                   "SRF_NEdR_version": SRF_NEdR_version })
    output["TIRS_L0_Data"] = o_data
    
    mkdir_p(os.path.dirname(outp_nc_fpath))

    write_data_fromspec(output, outp_nc_fpath, filespecs_fpath, verbose=True)
