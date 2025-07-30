"""
Over a 1-hour time period, reconstruct orbit state vectors and related
information at 1 Hz, and determine any PREFIRE granule boundaries and IDs
within.  Write the resulting information to a NetCDF-format file.

This program requires Python version 3.6 or later, and is importable as a
Python module.
"""

  # From the Python standard library:
import os
import argparse
from pathlib import Path
import datetime
import glob

  # From other external Python packages:
import numpy as np
import netCDF4
from skyfield.api import Loader, load, wgs84, EarthSatellite

  # From custom Python utilities:
from PREFIRE_tools.utils.time import UTC_DT_to_ctime, ctime_to_UTC_DT
import PREFIRE_L0.filepaths as L0_fpaths
from PREFIRE_tools.utils.filesys import mkdir_p
from PREFIRE_tools.utils.unit_conv import mm_to_m, m_to_km
from PREFIRE_PRD_GEN.file_creation import write_data_fromspec


#--------------------------------------------------------------------------
def _find_any_granule_edges(data):
    """ Find/determine ctime of granule edge(s)."""

    # NOTE: This routine is intended for use with regularly-spaced (in time)
    #        input orbit state vectors ONLY, with any time gaps <= 5 seconds.
    
    # A millimeter is added to the position for this search step ONLY, in
    #  order to avoid issues with zero values:
    sign_p3_ma = np.sign(data["position_wrt_ECI_3"]+1.*mm_to_m*m_to_km)
    i_ans = np.where(sign_p3_ma[:-1] != sign_p3_ma[1:])[0]+1

    # Filter out those candidates which are partly or fully in the descending
    #  portion of the orbit:
    i_granule_beg = [i for i in i_ans if (data["velocity_wrt_ECI_3"][i] > 0.
                                      and data["velocity_wrt_ECI_3"][i-1] > 0.)]


    # Interpolate to determine any granule-edge ctimes:
    #  (note that the orbital period of each PREFIRE S/C should decrease with
    #   with elapsed time, due to atmospheric drag and limited station-keeping
    #   capability)
    granule_edge_ctime_s = []
    for igb in i_granule_beg:
        if igb == 0:
            continue  # Leading edge of time period; skip
        else:
            ct_bef, ct_aft = (data["ctime"][igb-1], data["ctime"][igb])
            p3_bef = data["position_wrt_ECI_3"][igb-1]  # [km]
            p3_aft = data["position_wrt_ECI_3"][igb]  # [km]

        ct_diff = ct_aft-ct_bef  # [s]
       
        # Interpolate:
        ct_edge = ct_aft-p3_aft/(p3_aft-p3_bef)*ct_diff  # [s]
        granule_edge_ctime_s.append(ct_edge)

    return (granule_edge_ctime_s)


#--------------------------------------------------------------------------
def predict_orbit_from_TLE(TLE_line1, TLE_line2, anc_data_dir, start_UTC_DT,
                           length_s, cadence_ms):
    """Predict satellite orbit from a TLE over the specified time period with
    specified cadence."""

    # Output a dictionary with satellite position and velocity
    # vectors in the Geocentric Celestial Reference System (GCRS), prediction
    # times, satellite solar illumination flag, and satellite reference
    # altitude/lat/lon coordinates.

    # Parameters
    # ----------
    # TLE_line1 : str
    #     First line of the two-line element (TLE) element set to use
    # TLE_line2 : str
    #     Second line of the two-line element (TLE) element set to use
    # anc_data_dir : str
    #     Path/directory of any ancillary data files
    # start_UTC_DT : datetime.datetime object
    #     UTC datetime object specifying when to begin the orbit propagation
    # length_s : float
    #     Length of the prediction period (integer number of seconds)
    # cadence_ms : float
    #     Time interval between satellite position calculations in milliseconds

    ts = load.timescale()

    cadence_td = datetime.timedelta(milliseconds=cadence_ms)
    length_td = datetime.timedelta(seconds=length_s)
    datestr_fmt = "%Y%m%dT%H%M%SZ"

    satellite = EarthSatellite(TLE_line1, TLE_line2, "PREFIRE_CubeSat", ts)
    epoch_tstr = satellite.epoch.utc_datetime().strftime(datestr_fmt)

    odat = {}

    # Generate times for orbit predictions (from given start UTC, advance a
    #  given amount of time into the future):
    odat["UTC_DT"] = np.array([start_UTC_DT+x*cadence_td for x in
                                              range(int(length_td/cadence_td))])
    times_sf = ts.from_datetimes(odat["UTC_DT"])
    
    # Calculate satellite position at each prediction time
    GCRS_states = satellite.at(times_sf)
   
    # Get satellite position vector components (technically in the GCRS frame;
    #  Geocentric Celestial Reference System):
    odat["position_wrt_ECI_1"] = GCRS_states.position.km[0]  # [km]
    odat["position_wrt_ECI_2"] = GCRS_states.position.km[1]  # [km]
    odat["position_wrt_ECI_3"] = GCRS_states.position.km[2]  # [km]
    
    # Get satellite velocity vector components (technically in the GCRS frame;
    #  Geocentric Celestial Reference System):
    odat["velocity_wrt_ECI_1"] = GCRS_states.velocity.km_per_s[0]  # [km s-1]
    odat["velocity_wrt_ECI_2"] = GCRS_states.velocity.km_per_s[1]  # [km s-1]
    odat["velocity_wrt_ECI_3"] = GCRS_states.velocity.km_per_s[2]  # [km s-1]
    
    # Get satellite sunlit status, using a publicly-available JPL ephemeris:
    loadlocal = Loader('.')  # avoid duplicating large DE files
    de_data = loadlocal(os.path.join(anc_data_dir, "de421.bsp"))
    odat["SC_in_Earth_umbra"] = ~GCRS_states.is_sunlit(de_data)

    # Get satellite geodetic lat, lon, and alt:
    geod_pos = wgs84.geographic_position_of(GCRS_states)
    alt_sf = geod_pos.elevation
    lat_sf = geod_pos.latitude
    lon_sf = geod_pos.longitude
    odat["ref_altitude"] = alt_sf.km  # [km]
    odat["ref_latitude"] = lat_sf.degrees  # [km]
    odat["ref_longitude"] = lon_sf.degrees  # [km]

    return odat


#--------------------------------------------------------------------------
def determine_orbit_info(leap_s_info, anc_data_dir, ELSET_line1, ELSET_line2,
                         ELSET_epoch_ctime, ELSET_epoch_UTC_DT, ELSET_revcount,
                         tgt_L0_ctime, tgt_L0_UTC_DT):
    """Determine orbit info for the targeted time period, including any granule
       edges and IDs."""

    margin_td = datetime.timedelta(hours=1.6)  # A bit more than one orbit

    # Propagate orbit to fully encompass both the ELSET epoch and the targeted
    #  time range (with ~1 orbit margin on either side):

    if (ELSET_epoch_UTC_DT >= tgt_L0_UTC_DT[0] and
                   ELSET_epoch_UTC_DT < tgt_L0_UTC_DT[1]):  # ELSET epoch within
        start_UTC_DT = tgt_L0_UTC_DT[0]-margin_td
        duration_td = (tgt_L0_UTC_DT[1]-start_UTC_DT)+margin_td
    elif ELSET_epoch_UTC_DT < tgt_L0_UTC_DT[0]:  # ELSET epoch before
        start_UTC_DT = ELSET_epoch_UTC_DT-margin_td
        duration_td = (tgt_L0_UTC_DT[1]-start_UTC_DT)+margin_td
    elif ELSET_epoch_UTC_DT >= tgt_L0_UTC_DT[1]:  # ELSET epoch after
        start_UTC_DT = tgt_L0_UTC_DT[0]-margin_td
        duration_td = (ELSET_epoch_UTC_DT-start_UTC_DT)+margin_td

    orbit_from_near_epoch = predict_orbit_from_TLE(ELSET_line1, ELSET_line2,
                  anc_data_dir, start_UTC_DT, duration_td.total_seconds(), 1.e3)

      # Add ctime to dict:
    orbit_from_near_epoch["ctime"], _ = UTC_DT_to_ctime(
                              orbit_from_near_epoch["UTC_DT"], 's', leap_s_info)

    # Find/determine ctime of granule edges:
    #    (where p3[i-1] < 0 < p3[i] and v3[i-1],v3[i] > 0)
    granule_edge_ctime_s = np.array(
                                 _find_any_granule_edges(orbit_from_near_epoch))

    # For each granule (defined as starting at each granule edge), determine
    #  the rev count (granule_ID) based on the ELSET epoch rev count:
    i_ep = np.argmin(np.abs(granule_edge_ctime_s-ELSET_epoch_ctime))
    n_granule_edges = len(granule_edge_ctime_s)
    granule_rev_count = np.full((n_granule_edges,), -9999, dtype="int32")
    granule_rev_count[i_ep] = ELSET_revcount
    if i_ep > 0:
        for igr in range(i_ep-1, -1, -1):
            granule_rev_count[igr] = granule_rev_count[igr+1]-1
    if i_ep+1 < n_granule_edges:
        for igr in range(i_ep+1, n_granule_edges):
            granule_rev_count[igr] = granule_rev_count[igr-1]+1

    # Subset the orbit info to within the given ctime search interval (remove
    #  the 'UTC_DT' key):
    o_data = {}
    ind = np.nonzero((orbit_from_near_epoch["ctime"] >= tgt_L0_ctime[0]) &
                     (orbit_from_near_epoch["ctime"] < tgt_L0_ctime[1]))
    tmp_UTC_DT = orbit_from_near_epoch["UTC_DT"][ind]
    for key in orbit_from_near_epoch:
        if key != "UTC_DT":
            o_data[key] = orbit_from_near_epoch[key][ind]

    # Subset the granule (edge) info to within the given ctime search interval:
    ind = np.nonzero((granule_edge_ctime_s >= tgt_L0_ctime[0]) &
                     (granule_edge_ctime_s < tgt_L0_ctime[1]))
    o_data["granule_edge_ctime"] = np.array(granule_edge_ctime_s[ind],
                                            dtype="float64")  # [s]
    o_data["granule_ID"] = granule_rev_count[ind]

    # UTC integer representation:
    o_data["UTC_datetime_repr"] = np.array([t.year*10000000000000+
                          t.month*100000000000+t.day*1000000000+t.hour*10000000+
                          t.minute*100000+t.second*1000+int(t.microsecond/1000)
                                           for t in  tmp_UTC_DT])

    return o_data


#--------------------------------------------------------------------------
def create_L0_orbit_reconst(leap_s_info, sat_IDnum, start_UTC_dtrepr):
    """Predict satellite orbit track for a specified time interval and cadence
       using TLE data."""

    anc_data_dir = os.environ["ANCILLARY_DATA_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    filespecs_fpath = os.path.join(anc_data_dir, "orbit_reconst_filespecs.json")
    fpath_with_ELSETs = os.environ["FPATH_WITH_ELSETS"].strip()
    
    if sat_IDnum == 1:  # SAT1
        NORAD_ID_check = "59965"
    else:  # SAT2
        NORAD_ID_check = "59881"

    about_one_hour_td = (datetime.timedelta(hours=1)-
                         datetime.timedelta(microseconds=1))
    tgt_L0_UTC_DT = [datetime.datetime.strptime(start_UTC_dtrepr[:-1]+"+0000",
                                                         "%Y-%m-%dT%H:%M:%S%z")]
    tgt_L0_UTC_DT.append(tgt_L0_UTC_DT[0]+about_one_hour_td)
    tgt_L0_ctime, _ = UTC_DT_to_ctime(tgt_L0_UTC_DT, 's', leap_s_info)
    tgt_grmdpt_ctime = sum(tgt_L0_ctime)/len(tgt_L0_ctime)
    tgt_grmdpt_UTC_DT, _ = ctime_to_UTC_DT(tgt_grmdpt_ctime, 's', leap_s_info)

    # Set spacecraft ID string representation:
    spacecraft_ID = f"PREFIRE{sat_IDnum:02d}"

    # <any> input ELSETs:
    #    <any> input ELSET <= 2 days from granule mid-time --> use input ELSET
    #    <no> input ELSET <= 2 days from granule mid-time --> try ELSET archive
    # no input ELSETs (no fpath or empty file contents) or trying ELSET archive:
    #    <any> archive ELSET <= 2 days from granule mid-time --> ELSET archive
    #    <no> archive ELSET <= 2 days from granule mid-time --> ERROR

    two_days_td = datetime.timedelta(days=2)
    three_minutes_td = datetime.timedelta(minutes=3)  # 0.05 hours

    use_archived_ELSETs = True
    if len(fpath_with_ELSETs) > 0:
        if not os.path.exists(fpath_with_ELSETs):
            print("WARNING: specified ELSETs file ({}) was not found -- will "
                  "try the archived ELSETs".format(
                  fpath_with_ELSETs))
        elif os.stat(fpath_with_ELSETs).st_size < 138:  # [bytes]
            print("WARNING: specified ELSETs file ({}) does not seem to "
                  "contain one or more ELSETs -- will try the archived "
                  "ELSETs".format(fpath_with_ELSETs))
        else:
            # Read in given ELSETs:
            with open(fpath_with_ELSETs, 'r') as f:
                lines = f.readlines()

            nonempty_lines = [line for line in lines if line.strip()]
            ELSETs_line1 = [line.strip() for line in nonempty_lines if
                                                                 line[0] == '1']
            ELSETs_line2 = [line.strip() for line in nonempty_lines if
                                                                 line[0] == '2']

            ELSET_epoch_UTC_DT_l = []
            for line1 in ELSETs_line1:
                yy = int(line1[18:20])
                if yy < 70:
                    yyyy = yy+2000
                else:
                    yyyy = yy+1900
                ref_dtrep = f"{yyyy}-01-01T00:00:00+0000"
                ref_UTC_DT = datetime.datetime.strptime(ref_dtrep,
                                                        "%Y-%m-%dT%H:%M:%S%z")

                fdoy = float(line1[20:32])
                elapsed_days_in_year = max(fdoy-1., 0.)

                ELSET_epoch_UTC_DT_l.append(ref_UTC_DT+datetime.timedelta(
                                                     days=elapsed_days_in_year))

            ELSET_epoch_ctime_l, _ = UTC_DT_to_ctime(ELSET_epoch_UTC_DT_l, 's',
                                                     leap_s_info)
            ELSET_epoch_ctime_a = np.array(ELSET_epoch_ctime_l)
            ELSET_ep_grmdpt_abs = np.abs(ELSET_epoch_ctime_a-tgt_grmdpt_ctime)
            i_to_use = np.argmin(ELSET_ep_grmdpt_abs)

            if (ELSET_ep_grmdpt_abs[i_to_use] <= two_days_td.total_seconds()):
                use_archived_ELSETs = False  # Found usable ELSET
                ELSET_line1 = ELSETs_line1[i_to_use]
                ELSET_line2 = ELSETs_line2[i_to_use]
                ELSET_epoch_ctime = ELSET_epoch_ctime_a[i_to_use]
                ELSET_epoch_UTC_DT = ELSET_epoch_UTC_DT_l[i_to_use]
                ELSET_revcount = int(ELSET_line2[63:68])

    if use_archived_ELSETs:
        searchstr = "TLEplus_{}_*.nc".format(NORAD_ID_check)
        globstr = os.path.join(anc_data_dir, searchstr)
        all_fpaths = sorted(glob.glob(globstr))
        if len(all_fpaths) == 0:
            raise RuntimeError("No input files found.")

        ds_l = []
        n_total_elset = 0
        for fpath in all_fpaths:
            ds_l.append(netCDF4.Dataset(fpath, 'r'))
            n_total_elset += ds_l[-1].dimensions["elset"].size

        UTC_os = "+0000"
        ELSET_UTC_DT_tot_bnds = [datetime.datetime.strptime(
                   ds_l[0].UTC_coverage_start+UTC_os, "%Y-%m-%dT%H:%M:%S.%f%z"),
                                 datetime.datetime.strptime(
                   ds_l[-1].UTC_coverage_end+UTC_os, "%Y-%m-%dT%H:%M:%S.%f%z")]

        # Index of first element set that should be considered for use (initial
        #  ELSETs are "messy"):
        if sat_IDnum == 1:
            ib = 4  # SAT1
        else:
            ib = 3  # SAT2

        n = n_total_elset-ib
        ELSET_epoch_UTC_DT_a = np.empty((n,), dtype="object")
        i_ds = np.empty((n,), dtype="int32")
        ds_ibeg = np.empty((n,), dtype="int32")

        i_beg = 0
        for i, ds in enumerate(ds_l):
            n_elset = ds.dimensions["elset"].size
            if i == 0:
                ibs = ib
            else:
                ibs = 0               
            i_end = i_beg+n_elset-ibs  # NumPy end index
            
            ELSET_epoch_UTC_DT_a[i_beg:i_end] = np.array(
                             [datetime.datetime.strptime(str(x)+"000"+UTC_os,
                              "%Y%m%d%H%M%S%f%z") for x in ds.groups["Data"].
                             variables["epoch_UTC_datetime_repr"][ibs:n_elset]])
            i_ds[i_beg:i_end] = i
            ds_ibeg[i_beg:i_end] = i_beg

            i_beg = i_end

        ELSET_epoch_ctime_a, _ = UTC_DT_to_ctime(ELSET_epoch_UTC_DT_a, 's',
                                               leap_s_info)
        ELSET_ep_grmdpt_abs = np.abs(ELSET_epoch_ctime_a-tgt_grmdpt_ctime)
        i_to_use = np.argmin(ELSET_ep_grmdpt_abs)

        if (ELSET_ep_grmdpt_abs[i_to_use] > two_days_td.total_seconds() and
                                                                 i_to_use > 0):
            raise RuntimeError("no ELSET epoch within 2 days of target time")

        ELSET_line1 = ''.join([x.decode("UTF-8") for x in
                               ds_l[i_ds[i_to_use]].groups["Data"].
                            variables["TLE_line1"][i_to_use-ds_ibeg[i_to_use]]])
        ELSET_line2 = ''.join([x.decode("UTF-8") for x in
                               ds_l[i_ds[i_to_use]].groups["Data"].
                            variables["TLE_line2"][i_to_use-ds_ibeg[i_to_use]]])

        ELSET_epoch_ctime = ELSET_epoch_ctime_a[i_to_use]
        ELSET_epoch_UTC_DT = ELSET_epoch_UTC_DT_a[i_to_use]
        ELSET_revcount = int(ELSET_line2[63:68])

    print("ep time:",ELSET_epoch_ctime,ELSET_epoch_UTC_DT)
    print("ep_revcount:", ELSET_revcount)

    o_data = determine_orbit_info(leap_s_info, anc_data_dir,
               ELSET_line1, ELSET_line2, ELSET_epoch_ctime, ELSET_epoch_UTC_DT,
                                    ELSET_revcount, tgt_L0_ctime, tgt_L0_UTC_DT)

    now_UTC_DT = datetime.datetime.now(datetime.timezone.utc)
    now_UTC_strrep = now_UTC_DT.strftime("%Y-%m-%dT%H:%M:%S.%f")

    UTC_dtrepr = [x.strftime("%Y%m%d%H%M%S") for x in tgt_L0_UTC_DT]
    UTC_dtrepr.append(now_UTC_DT.strftime("%Y%m%d%H%M%S"))
    outp_nc_fn = "prefire_0{:1d}_orbit_reconst_{}_{}_{}.nc".format(sat_IDnum,
                                UTC_dtrepr[0], UTC_dtrepr[1], UTC_dtrepr[2])
    outp_nc_fpath = os.path.join(output_dir, outp_nc_fn)

    product_full_version = os.environ["PRODUCT_FULLVER"].strip()
    
    with open(L0_fpaths.scipkg_prdgitv_fpaths[2], 'r') as in_f:
        line_parts = in_f.readline().split('(', maxsplit=1)
        this_pkg_provenance = "{}{} ( {}".format(line_parts[0],
                                                 product_full_version,
                                                 line_parts[1].strip())
    with open(L0_fpaths.scipkg_version_fpath, 'r') as in_f:
        proc_algID = in_f.readline().strip()

    orbit_sim_version = os.environ["ORBSIM_VERSION"].strip()
    if len(orbit_sim_version) == 0:
        orbit_sim_version = ' '

    output = {}
    output["Global_Attributes"] = ({
                   "full_versionID": product_full_version,
                   "granule_type": "0-ORB-REC",
                   "granule_ID": ' ',
                   "provenance": this_pkg_provenance,
                   "file_name": os.path.basename(outp_nc_fpath),
                   "input_product_files": ' ',
                   "processing_algorithmID": proc_algID,
                   "UTC_of_file_creation": now_UTC_strrep,
                   "spacecraft_ID": spacecraft_ID,
                   "ctime_coverage_start_s": o_data["ctime"][0],
                   "ctime_coverage_end_s": o_data["ctime"][-1],
                   "UTC_coverage_start": tgt_L0_UTC_DT[0].strftime(
                                                        "%Y-%m-%dT%H:%M:%S.%f"),
                   "UTC_coverage_end": tgt_L0_UTC_DT[1].strftime(
                                                        "%Y-%m-%dT%H:%M:%S.%f"),
                   "netCDF_lib_version": netCDF4.getlibversion().split()[0],
                   "orbit_sim_version": orbit_sim_version })
    output["Orbit_L0_Data"] = o_data
    
    mkdir_p(os.path.dirname(outp_nc_fpath))

    write_data_fromspec(output, outp_nc_fpath, filespecs_fpath, verbose=True)

    return outp_nc_fpath
