"""
Constructs a time series of payload info entries/looks over an orbital
 simulation, and writes that to file(s).

This program requires python version 3.6 or later, and is importable as a
python module.
"""

  # From the Python standard library:
import os
import sys
import glob
import datetime
import json

  # From other external Python packages:

import netCDF4
import numpy as np

  # Custom utilities:

from PREFIRE_tools.utils.time import ctime_to_UTC_DT, UTC_DT_to_ctime
import PREFIRE_L0.filepaths as L0_fpaths
from PREFIRE_PRD_GEN.file_creation import write_data_fromspec


#--------------------------------------------------------------------------
def create_orbitsim_payload_info(leap_s_info):
    """Driver routine."""

    # Load the given product file data specification(s):
    json_fpath = os.environ["ORBITSIM_CFG_FILE"]
    with open(json_fpath, 'r') as f:
        tmp_cfg = json.load(f)
        cfg = tmp_cfg["Config"]

    sat_num = cfg["sat_num"]

    sat_fpfx = f"prefire_{sat_num:02}_"

    base_output_path = os.path.abspath(cfg["base_output_dir"])
    input_pld_info_fpath = os.environ["PLDTLM_EXCERPT_FILE"]
    input_bus_summ_fpath = os.path.join(base_output_path,
                               f"index.PREFIRE_SAT{sat_num:d}_0-RawBusTlm.txt")

    product_full_version = os.environ["PRODUCT_FULLVER"].strip()
    with open(L0_fpaths.scipkg_prdgitv_fpaths[1], 'r') as in_f:
        line_parts = in_f.readline().split('(', maxsplit=1)
        this_pkg_provenance = "{}{} ( {}".format(line_parts[0],
                                                 product_full_version,
                                                 line_parts[1].strip())

    with open(L0_fpaths.scipkg_version_fpath, 'r') as in_f:
        proc_algID = in_f.readline().strip()

    # Read in raw bus telemetry index and determine file time range info:
    with open(input_bus_summ_fpath, "rt") as f:
        bus_tlm_fpaths = [x.strip() for x in f.readlines()]

        pld_info_paths = [os.path.dirname(x) for x in bus_tlm_fpaths]

        tokens = [os.path.basename(x).split('_') for x in bus_tlm_fpaths]
        pld_info_irepstr_beg = [x[4] for x in tokens]
        pld_info_irepstr_end = [x[5] for x in tokens]
        
        pld_info_DT_beg = []
        for dtstr in pld_info_irepstr_beg:
            parseable_isofmt = "{}-{}-{}T{}:{}:{}+00:00".format(dtstr[0:4],
                                           dtstr[4:6], dtstr[6:8], dtstr[8:10],
                                           dtstr[10:12], dtstr[12:14])
            pld_info_DT_beg.append(datetime.datetime.fromisoformat(
                                                             parseable_isofmt))
        pld_info_ctime_beg, _ = UTC_DT_to_ctime(np.array(pld_info_DT_beg), 's',
                                                leap_s_info)

        pld_info_DT_end = []
        for dtstr in pld_info_irepstr_end:
            parseable_isofmt = "{}-{}-{}T{}:{}:{}+00:00".format(dtstr[0:4],
                                           dtstr[4:6], dtstr[6:8], dtstr[8:10],
                                           dtstr[10:12], dtstr[12:14])
            pld_info_DT_end.append(datetime.datetime.fromisoformat(
                                                             parseable_isofmt))
        pld_info_ctime_end, _ = UTC_DT_to_ctime(np.array(pld_info_DT_end), 's',
                                                leap_s_info)

          # Maximum duration of orbit simulation payload info:
        pld_info_td_at_start = datetime.timedelta(
                              seconds=cfg["pld_start_tdelta_from_bustlm_in_s"])
        pld_info_maxorbsimlen_td = (pld_info_DT_end[-1]-pld_info_DT_beg[0]-
                                    pld_info_td_at_start)


    with netCDF4.Dataset(input_pld_info_fpath) as nc_f:
        # Read in payload info excerpt:
        excerpt_ctime_rel = nc_f.variables["ctime"][...]  # [s]
        n_excerpt_entries = len(excerpt_ctime_rel)
        excerpt_scipkt_icnt = nc_f.variables["scipkt_icnt"][...]
          # For now, force all looks to be obstgt looks, in order to have the
          #  capability to change the cadence, etc. of the calibration sequences
          #  at will during the TIRS inverse model processing *without* redoing
          #  the tedious AUX-MET- and PCRTM-related steps of the orbital sim.
          #  Use the approximate mean of the excerpt's obstgt encoder positions.
        excerpt_scipkt_type = nc_f.variables["scipkt_type"][...]
        excerpt_scipkt_encoder_pos = nc_f.variables["scipkt_encoder_pos"][...]
        tmp_mean = np.mean(np.ma.masked_where(excerpt_scipkt_type != 3,
                                              excerpt_scipkt_encoder_pos))
        excerpt_scipkt_type[:] = 3  # Force all looks to be obstgt looks
        excerpt_scipkt_encoder_pos[:] = int(round(tmp_mean)+1.e-3)  #

      #--- Construct a time series of payload info entries/looks over the
      #---  orbital sim:

        # Count total entries that will be created:
        n_pld_info_entries = 0
          # Add first sequence:
        beg_edge_ctime = (pld_info_ctime_beg[0]+
                               cfg["pld_start_tdelta_from_bustlm_in_s"])  # [s]
        ctime_seq = excerpt_ctime_rel+beg_edge_ctime  # [s]
        if ctime_seq[-1] > pld_info_ctime_end[-1]:
            it_end = np.searchsorted(ctime_seq, pld_info_ctime_end[-1],
                                     side="left")-1
            n_pld_info_entries += it_end+1
        else:
            n_pld_info_entries += len(ctime_seq)
            last_look_ctime = ctime_seq[-1]

            while True:
                beg_edge_ctime = last_look_ctime
                  # Omit 1st element of sequence, for correct tiling:
                ctime_seq = excerpt_ctime_rel[1:]+beg_edge_ctime
                if ctime_seq[-1] > pld_info_ctime_end[-1]:
                    it_end = np.searchsorted(ctime_seq, pld_info_ctime_end[-1],
                                             side="left")-1
                    n_pld_info_entries += it_end+1
                    last_look_ctime = ctime_seq[it_end]
                    break
                else:
                    n_pld_info_entries += len(ctime_seq)
                    last_look_ctime = ctime_seq[-1]

        # Produce full simulated series of payload info:
        pld_info_look_ctime = np.zeros((n_pld_info_entries,), dtype="float64")
        pld_info_look_type = np.zeros((n_pld_info_entries,), dtype="int8")
        pld_info_look_enpos = np.zeros((n_pld_info_entries,), dtype="uint16")
        curr_it_start = 0
          # Add first sequence:
        beg_edge_ctime = (pld_info_ctime_beg[0]+
                               cfg["pld_start_tdelta_from_bustlm_in_s"])  # [s]
        ctime_seq = excerpt_ctime_rel+beg_edge_ctime  # [s]
        type_seq = excerpt_scipkt_type
        enpos_seq = excerpt_scipkt_encoder_pos
        if ctime_seq[-1] > pld_info_ctime_end[-1]:
            it_end = np.searchsorted(ctime_seq, pld_info_ctime_end[-1],
                                     side="left")-1
            it_npb, it_npe = (curr_it_start, curr_it_start+it_end+1)
            pld_info_look_ctime[it_npb:it_npe] = ctime_seq[:it_end+1]
            pld_info_look_type[it_npb:it_npe] = type_seq[:it_end+1]
            pld_info_look_enpos[it_npb:it_npe] = enpos_seq[:it_end+1]
        else:
            it_npb, it_npe = (curr_it_start, curr_it_start+len(ctime_seq))
            pld_info_look_ctime[it_npb:it_npe] = ctime_seq[:]
            pld_info_look_type[it_npb:it_npe] = type_seq[:]
            pld_info_look_enpos[it_npb:it_npe] = enpos_seq[:]
            curr_it_start += len(ctime_seq)

         # Add additional copies of the sequence (full or partial), as needed:
            while True:
                beg_edge_ctime = pld_info_look_ctime[curr_it_start-1]
                  # Omit 1st element of sequence, for correct tiling:
                ctime_seq = excerpt_ctime_rel[1:]+beg_edge_ctime
                type_seq = excerpt_scipkt_type[1:]
                enpos_seq = excerpt_scipkt_encoder_pos[1:]
                if ctime_seq[-1] > pld_info_ctime_end[-1]:
                    it_end = np.searchsorted(ctime_seq, pld_info_ctime_end[-1],
                                             side="left")-1
                    it_npb, it_npe = (curr_it_start, curr_it_start+it_end+1)
                    pld_info_look_ctime[it_npb:it_npe] = ctime_seq[:it_end+1]
                    pld_info_look_type[it_npb:it_npe] = type_seq[:it_end+1]
                    pld_info_look_enpos[it_npb:it_npe] = enpos_seq[:it_end+1]
                    break
                else:
                    it_npb, it_npe = (curr_it_start,
                                      curr_it_start+len(ctime_seq))
                    pld_info_look_ctime[it_npb:it_npe] = ctime_seq[:]
                    pld_info_look_type[it_npb:it_npe] = type_seq[:]
                    pld_info_look_enpos[it_npb:it_npe] = enpos_seq[:]
                    curr_it_start += len(ctime_seq)

        # Write payload info into NetCDF-format files distributed throughout
        #  the orbital sim in a very similar fashion as the (input) simulated
        #  raw bus tlm files:

        anc_data_dir = os.environ["ANCILLARY_DATA_DIR"]
        filespecs_fpath = os.path.join(anc_data_dir,
                                       "payload_prototlm_filespecs.json")

        output_path = os.path.join(base_output_path,
                                   cfg["payload_prototlm_dirname"])
        os.makedirs(output_path, exist_ok=True)

        iof = 0
        it = 0
        beg_it = it
        while True:
            it_clipped = min(it, n_pld_info_entries-1)
            if (pld_info_look_ctime[it_clipped] > pld_info_ctime_end[iof] or
                                                     it == n_pld_info_entries):
                # Time to write a file:
                it_npb, it_npe = (beg_it, it)
                ctime_coverage = pld_info_look_ctime[[it_npb, it_npe-1]]
                UTC_DT_coverage, _ = ctime_to_UTC_DT(ctime_coverage, 's',
                                                     leap_s_info)
 
                now_UTC_DT = datetime.datetime.now(datetime.timezone.utc)
                tmp_fn = ("{}payload_prototlm_{:%Y%m%d%H%M%S}_{:%Y%m%d%H%M%S}_"
                          "{:%Y%m%d%H%M%S}.nc".format(
                                                  sat_fpfx, UTC_DT_coverage[0],
                                               UTC_DT_coverage[1], now_UTC_DT))
                outp_fpath = os.path.join(output_path, tmp_fn)
#                print ("Output payload prototlm file: "+outp_fpath)

                output = {}
                o_data = {}

                # Need this for L1A-GEOM processing:
                o_data["dummy_var_for_dims"] = np.zeros((64, 8), dtype="int8")

                # Set global attributes:
                output["Global_Attributes"] = {
                      "full_versionID": cfg["orbitsim_version_short"],
                      "granule_type": "0-PROTOPLD-TLM",
                      "granule_ID": ' ',
                      "provenance": this_pkg_provenance,
                      "file_name": tmp_fn,
                      "input_product_files": ' ',
                      "processing_algorithmID": proc_algID,
                      "UTC_of_file_creation": now_UTC_DT.strftime(
                                                       "%Y-%m-%dT%H:%M:%S.%f"),
                      "spacecraft_ID": f"PREFIRE{sat_num:02}",
                      "sensor_ID": f"TIRS{sat_num:02}",
                      "ctime_coverage_start_s": pld_info_look_ctime[it_npb],
                      "ctime_coverage_end_s": pld_info_look_ctime[it_npe-1],
                      "UTC_coverage_start": UTC_DT_coverage[0].strftime(
                                                       "%Y-%m-%dT%H:%M:%S.%f"),
                      "UTC_coverage_end": UTC_DT_coverage[1].strftime(
                                                       "%Y-%m-%dT%H:%M:%S.%f"),
                      "netCDF_lib_version": netCDF4.getlibversion().split()[0],
                      "orbit_sim_version": cfg["orbitsim_version_long"],
                      "SRF_NEdR_version": " "}

                # Create/set variables:

                o_data["ctime"] = pld_info_look_ctime[it_npb:it_npe]

                output["TIRS_L0_Data"] = o_data

                write_data_fromspec(output, outp_fpath, filespecs_fpath,
                                    verbose=True)

                if it == n_pld_info_entries:
                    break  # Done
                beg_it = it
                iof += 1
            it += 1
