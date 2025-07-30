% Creates simulated PREFIRE raw L0 bus telemetry files, nominally for an entire
%  year.
function [error_ca] = create_orbitsim_bus_tlm(pd)

error_ca = {'#NONE#', 0};  % Default

% Perform rough check for correct orbit MLTAN alignment on first chunk?
%  (if true, takes substantially more time to calculate everything)
perform_MLTAN_check = false;

orig_path = path;
path(orig_path, fullfile(pd.top_path, 'source', 'matlab', 'PREFIRE_tools', ...
                         'external_packages', 'sgp4', 'mat'));

uc = constants_unit_conversion;  % Unit conversion constants
tc = constants_time(pd.tools_anc_data_dir);  % Time-related constants

%-----------------------------------------------------------------------------

% Read in JSON-format configuration file:
cfgdat = jsondecode(fileread(pd.orbitsim_cfg_fpath));
cfg = cfgdat.Config;  % Short handle to refer to

tmp = regexprep(cfg.nom_UTC_DTstrrep_beg, {'\-', 'T', ':'}, {'_', '_', '_'});
nominal_DTbeg = datetime(tmp, 'InputFormat', ...
                         'yyyy_MM_dd_HH_mm_ss', 'TimeZone', 'UTC');
tmp = regexprep(cfg.nom_UTC_DTstrrep_end, {'\-', 'T', ':'}, {'_', '_', '_'});
nominal_DTend = datetime(tmp, 'InputFormat', ...
                         'yyyy_MM_dd_HH_mm_ss', 'TimeZone', 'UTC');

  % Vernal equinox (UTC datetime) immediately prior to the nominal start of the
  %  orbit simulation (used for MLTAN->RAAN conversion):
tmp = regexprep(cfg.UTC_DT_of_prior_vEquinox, {'\-', 'T', ':'}, ...
                {'_', '_', '_'});
DT_prior_vEqnx = datetime(tmp, 'InputFormat', ...
                        'yyyy_MM_dd_HH_mm_ss', 'TimeZone', 'UTC');

%-----------------------------------------------------------------------------


% Actual orbit simulation temporal range parameters:

  % In order to have data before and after the nominal range for interpolation,
  %  extend the actual orbit simulation time range by one downlink interval on
  %  both ends:
nominal_intv_td = seconds(max(cfg.downlink_intervals_in_s));
btlm_DTbeg = nominal_DTbeg-nominal_intv_td;
btlm_DTend = nominal_DTend+nominal_intv_td;

total_sample_s = fix(seconds(btlm_DTend-btlm_DTbeg));  % [s]

% Inclination angle for a sun-synchronous orbit (from Walter, eq. 12.3.15)
mu_E = 3.986e14;  % [m^3/s^2]
R_E = 6378.e3;  % [m]
J2 = 1.0826e-3;  % [-]
a = R_E+cfg.orbit_height_in_km*uc.km_to_m;  % [m]
n = sqrt(mu_E / a^3);
j2 = 1.5 * J2 * (R_E / a / (1-cfg.eccen*cfg.eccen))^2;
  % 360 degrees per 365.25 days, converted to rad/s:
synch_rate = (360/365.25) * pi / (180 * uc.day_to_s);
inclination = rad2deg(acos(-synch_rate/n/j2));

% Mean right ascension of the ascending node (RAAN):
fDsVE = seconds(btlm_DTbeg-DT_prior_vEqnx)*uc.s_to_day;  % frac days since vEqnx
RAAN = mod(cfg.MLTAN_in_hr*(360/24.)-180+360/365.2422*fDsVE, 360.);  % [deg]

% Output file prefix:
outp_pfx_string = sprintf('%s_%02d_%s', 'prefire', cfg.sat_num, 'bus_tlm');

%% Generate time intervals (as duration objects) between attitude entries:

fprintf('Generating time intervals between attitude entries ...\n');

min_s_between_nonstd_blocks = 4528;  % [s]
max_s_between_nonstd_blocks = 9999;  % [s]

nonstd_block_s = [1, 1, 1, 55, 2, 1, 2, 1, 9, 109, 158, 9, 60, 1, 1, 1];  % [s]
nonstd_block_s_colv = nonstd_block_s';  % [s]
nonstd_block_s_len = length(nonstd_block_s);
nonstd_block_total_s = sum(nonstd_block_s);  % [s]

max_n_nonstd_blocks = fix(total_sample_s/min_s_between_nonstd_blocks);
tloc_of_nonstd_blocks = randi([min_s_between_nonstd_blocks, ...
                               max_s_between_nonstd_blocks], 1, ...
                               max_n_nonstd_blocks);

% Allocate and initialize a numeric array that is large enough to hold the
%  maximum number of entries:
delta_t_sim = zeros(total_sample_s, 1);

% Determine simulated time intervals [s] between attitude entries, over the
%  entire simulated time:
i_tloc = 1;
ib = 1;
tsum = 0;
while tsum < total_sample_s
    ie = ib+fix(tloc_of_nonstd_blocks(i_tloc)/ ...
                                         cfg.nom_bus_tlm_entry_cadence_in_s)-1;
    delta_t_sim(ib:ie,1) = cfg.nom_bus_tlm_entry_cadence_in_s;
    tsum = tsum+sum(delta_t_sim(ib:ie,1));
    ib = ie+1;
    ie = ib+nonstd_block_s_len-1;
    delta_t_sim(ib:ie,1) = nonstd_block_s_colv(:,1);
    tsum = tsum+sum(delta_t_sim(ib:ie,1));
    if mod(i_tloc, 20) == 0
        fprintf('Status: Done with entry at %9.1f s (of %9.1f s).\n', ...
                tsum, total_sample_s);
    end

    i_tloc = i_tloc+1;
    ib = ie+1;
end
n_delta_t_sim = ie;

% Convert into duration objects, copying only the entries that are filled:
td_sim = seconds(delta_t_sim(1:n_delta_t_sim,1));

%% Start and stop info for output simulated bus telemetry files:

fprintf('Generating start and stop info for output simulated bus telemetry files ...\n');

s_between_output_f = seconds(cfg.nom_bus_tlm_entry_cadence_in_s);

  % [s] Roughly reflects using only one antenna site for each cubesat (the
  %  number of downlinks per day is implicitly set by how many of the specified
  %  downlink time intervals add up to one day):
intv_list = seconds(cfg.downlink_intervals_in_s);
n_intv = length(intv_list);

j = 1;
i = 1;
DTbeg{i} = btlm_DTbeg;
while DTbeg{i} < btlm_DTend
    DTbeg{i}.Format = 'yyyyMMddHHmmss';  % Set output format

    this_intv = intv_list(j);
    if j == n_intv
       j = 1;
    else
       j = j+1;
    end

    tmp_DT = DTbeg{i}+this_intv;
    if tmp_DT <= btlm_DTend
        DTend{i} = DTbeg{i}+this_intv;
    else
        DTend{i} = btlm_DTend;
    end
    DTend{i}.Format = 'yyyyMMddHHmmss';  % Set output format

    i = i+1;
    DTbeg{i} = DTend{i-1}+s_between_output_f;
end

%% Compute simulated spacecraft attitude information:

fprintf('Computing simulated spacecraft attitude information ...\n');

% Finish computing simulation timepoints:
epoch = year(DTbeg{1});  % year of 'epoch' most relevant to this simulation
epoch_day = day(DTbeg{1}, 'dayofyear')+  ...
                             seconds(timeofday(DTbeg{1}))*uc.s_to_day;  % [day]
sim_times_s = seconds(cumsum(td_sim));  % [s] from 'epoch'

% Obtain basic parameters for Earth from the 1984 Geodesy data:
earth_param_flag = 84;
[E_m, a, esq, flag] = def_Earth(earth_param_flag, 'meter');

node = RAAN;  % [degrees] longitude for ascending equator crossing

%**Note: E.MeanRadius and radiusearthkm are not generally the same value
%         (typically < 10 km different) -- this may lead to discrepancies?
[tumin, mu, radiusearthkm, xke, j2, j3, j4, j3oj2] = getgravc(flag);

arg_perigee = 0.;  % [degrees]
mean_anom = 0.;  % [degrees]
bstar = cfg.bstar_in_invErad;  % [1/Rearth] drag term

mean_motion = orbit_mm_from_height(cfg.orbit_height_in_km, cfg.eccen, ...
                                   radiusearthkm);

[sat] = sgp4_rv_simulation(epoch, epoch_day, ...
                           inclination, node, cfg.eccen, arg_perigee, ...
                           mean_motion, mean_anom, bstar, ...
                           sim_times_s, earth_param_flag);

%% Process simulated spacecraft attitude info further, and write it to file(s):

fprintf('Further process and write out simulated spacecraft attitude information ...\n');

% ctime [seconds since 2000-01-01T00:00:00 UTC]:
[error_ca, sat.ctime] = change_ctime_epoch_type(sat.ctimeN, 's', true, tc, uc);
if (error_ca{2} ~= 0)
   fprintf(2, '%s\n', error_ca{1});
   return
end

% Obtain actual-UTC datetimes and (ctime - UTC) values:
[error_ca, sat.UTC_DT, sat.ctime_minus_UTC] = ctime_to_UTC_DT(sat.ctime, ...
                                                              's', tc);
if (error_ca{2} ~= 0)
   fprintf(2, '%s\n', error_ca{1});
   return
end

% Determine (ctimeN - UTC) values:
sat.ctimeN_minus_UTC = sat.ctime_minus_UTC+ ...
                       tc.ref_ctimeOffsetFromUTC_atEp_s;  % [s]

sat.UTC_splitvals = datevec(sat.UTC_DT);

% Arrays temporarily allocated within `determine_attitude_info` are often too
%  large for most machines to handle, so perform this operation in chunks:
n = size(sat.ctimeN_minus_UTC, 1);
sat.quaternion = zeros(4, n);  % Preallocate
sat.is_downlink = false(n, 1);    %
in1_fields_to_copy = {'R_eci', 'V_eci'};  % (:,n)
in2_fields_to_copy = {'ctimeN_minus_UTC', 'UTC_splitvals'};  % (n,:)
out1_fields_to_copy = {'quaternion'};  % (:,n)
n_per_chunk = 100000;  % For "production"
%n_per_chunk = 20000;  % For testing
icnt = 0;
iin = 1;
while iin <= n
   icnt = icnt+1;
   iin_end = min(iin+n_per_chunk-1, n);
   fprintf('Chunk #%d (entries %d to %d, of %d)\n', icnt, iin, iin_end, n);

   % Create structure array for subset, then copy field subset(s) to it from
   %  the main structure array:
   sato = struct;
   for i=1:length(in1_fields_to_copy)
      sato.(in1_fields_to_copy{i}) = ...
                          sat.(in1_fields_to_copy{i})(:,iin:iin_end);
   end
   for i=1:length(in2_fields_to_copy)
      sato.(in2_fields_to_copy{i}) = ...
                          sat.(in2_fields_to_copy{i})(iin:iin_end,:);
   end

   iflag = 2;
   [sato] = determine_attitude_info(sato, iflag, E_m, uc, tc);  % no quaternion to input

   % Rough check for correct orbit alignment (last field should be
   %  less than +/- 15 minutes, and stay roughly constant/sun_synchronous for
   %  all successive orbits):
   if perform_MLTAN_check && iin == 1
      inddd = find(abs(sato.geod_lat(:,1)) < 0.1);  % Within 0.1 deg of equator
      for iddd=1:length(inddd)
         this_Vz = sato.V_eci(3,inddd(iddd));
         if this_Vz > 0.  % Part of the ascending pass
            this_lon = sato.geod_lon(inddd(iddd),1);
            this_MLT = timeofday(sat.UTC_DT(inddd(iddd)+iin-1)+ ...
                                                          hours(this_lon/15.));
            fprintf('%8.3f, %8.3f, %8.3f, %s, %s\n', ...
                    sato.geod_lat(inddd(iddd),1), this_lon, ...
                    sato.V_eci(3,inddd(iddd)), this_MLT, ...
                    this_MLT-hours(cfg.MLTAN_in_hr));
         end
      end
   end

   % Determine *very approximately* where downlinks might be. Takes into account
   %   1) realistic ground station and sub-satellite track locations
   %   2) Communicate with a different ground station every 5 days
   n_entries = iin_end-iin+1;
   %   sato.is_downlink = false(n_entries, 1);
   sato.lon_b = zeros(n_entries, 1);
   sato.lon_e = zeros(n_entries, 1);
   sato.lat_b = zeros(n_entries, 1);
   sato.lat_e = zeros(n_entries, 1);
   gndst_metric = int32((sat.UTC_DT(iin:iin_end)-sat.UTC_DT(1))/days(5));

   site_id = idivide(gndst_metric, 2);
     % Antenna site near Punta Arenas, Chile
   inddd0 = find(site_id == 0);
   sato.lon_b(inddd0) = -85.87;
   sato.lon_e(inddd0) = -55.87;
   sato.lat_b(inddd0) = -72.94;
   sato.lat_e(inddd0) = -32.94;
     % Antenna site near Puertollano, Spain
   inddd1 = find(site_id == 1);
   sato.lon_b(inddd1) = -19.16;
   sato.lon_e(inddd1) = 11.16;
   sato.lat_b(inddd1) = 18.67;
   sato.lat_e(inddd1) = 58.67;

   sato.is_downlink = (sato.geod_lat >= sato.lat_b & ...
                       sato.geod_lat <= sato.lat_e & ...
                       sato.geod_lon >= sato.lon_b & ...
                       sato.geod_lon <= sato.lon_e);

   % Copy field subset(s) to main structure array, then destroy the subset
   %  structure array:
   sat.is_downlink(iin:iin_end,1) = sato.is_downlink(:,1);
   for i=1:length(out1_fields_to_copy)
      sat.(out1_fields_to_copy{i})(:,iin:iin_end) = ...
                                                 sato.(out1_fields_to_copy{i});
   end
   clear sato;

   iin = iin_end+1;
end

%% Write raw bus telemetry file(s):
  % Create output filepath:
base_output_path = cfg.base_output_dir;  % Fallback position only
  % Try to determine the absolute path:
[status, info] = fileattrib(base_output_path);
if status
   base_output_path = info.Name;
end
output_dir = fullfile(base_output_path, cfg.raw_bus_tlm_dirname);
if ~isfolder(output_dir)
   mkdir(output_dir);
end
itm = 1;
itm_beg_next = itm;
sat.UTC_DT.Format = 'yyyyMMddHHmmss';  % Set output format
for i=1:length(DTend)
   itm_beg = itm_beg_next;
   while sat.time(itm) < DTend{i}
      itm = itm+1;
   end
   itm_beg_next = itm;
   itm_end = itm-1;

   now_UTCn_DT = datetime('now', 'TimeZone', 'UTC', 'Format', ...
                      'yyyy-MM-dd''T''HH:mm:ss.SSSSSS');  % faux-UTC (no leap-s)
   now_UTCn_DT.Format = 'yyyyMMddHHmmss';  % Set output format
   output_fn_string = sprintf('%s_%s_%s_%s.csv', ...
                              outp_pfx_string, sat.UTC_DT(itm_beg), ...
                              sat.UTC_DT(itm_end), now_UTCn_DT);
   output_fpath = fullfile(output_dir, output_fn_string);

   [error_ca] = write_sat(output_fpath, sat, itm_beg, itm_end, tc, uc);
   if (error_ca{2} ~= 0)
      fprintf(2, '%s\n', error_ca{1});
      return;
   end
end

end
