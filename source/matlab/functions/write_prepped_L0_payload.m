function [] = write_prepped_L0_payload(ancillary_data_dir, dn, encoder, ...
                  therm_dn, thermistor_temps, ctime, output_fpath, global_atts)
% 
% write L0 payload data, created from simulation (via the 'inverse
% instrument model') into a prepped L0 Bus netcdf file.
%
% inputs:
% ancillary_data_dir - directory path containing needed JSON-format filespecs
% dn - time ordered stream of adjusted "sci" convention TIRS DN
%     (digital numbers)  shape is (64, 8, num_frames)
% encoder - time series of encoder position samples
% therm_dn - instrument thermistor values converted to DN
%     shape is (8, num_frames)
% thermistor_temps - instrument thermistor values in K
%     shape is (8, num_frames)
% ctime - continuous time array, shape (1, num_frames)
% output_fpath - string file path + name for the netCDF4 file that
%     will be created
% global_atts - struct with netCDF global attributes
%
% This function returns no variables.
%

[n_spectral, n_xtrack, n_atrack] = size(dn);
FillValue = -9999.0;

% common dimension sizes
n_spectralxtrack = 512;
n_TIRS_T = 8;
n_ROIC_T = 4;
n_CDH_T = 2;
n_misc = 6;
n_eng = 40;

% populates the only section of eng data telemetry that we have.
engdata_tlm = zeros([n_eng,n_atrack],'uint16');
engdata_tlm(9:16,:) = therm_dn;

odat = struct;
odat.global_atts = struct;
odat.TIRS_L0_Data = struct;
odat.TIRS_L0_Data.group_dims = struct;

odat.TIRS_L0_Data.ctime        = ctime;
odat.TIRS_L0_Data.CDH_T        = zeros([n_CDH_T,n_atrack]) + FillValue;
odat.TIRS_L0_Data.ROIC_T       = zeros([n_ROIC_T,n_atrack]) + FillValue;
odat.TIRS_L0_Data.TIRS_T       = thermistor_temps;
odat.TIRS_L0_Data.MoE_T        = zeros([1,n_atrack]) + FillValue;
odat.TIRS_L0_Data.PDU_12V_I    = zeros([1,n_atrack]) + FillValue;
odat.TIRS_L0_Data.PDU_SCBATT_I = zeros([1,n_atrack]) + FillValue;
odat.TIRS_L0_Data.MoE_12V_I    = zeros([1,n_atrack]) + FillValue;
odat.TIRS_L0_Data.encoder_pos  = uint16(encoder);
odat.TIRS_L0_Data.engdata_tlm  = engdata_tlm;
odat.TIRS_L0_Data.misc_tlm     = zeros([n_misc,n_atrack],'uint16');
% the netcdf expects data written as (nframe, nspatial, nspectral)
% here, so the axes need to be permuted.
odat.TIRS_L0_Data.adj_srd_DN   = int32(permute(dn, [3,2,1]));

% field names need to match the JSON file descriptions
odat.TIRS_L0_Data.group_dims.atrack_scipkt = n_atrack;
odat.TIRS_L0_Data.group_dims.n_CDH_therm   = n_CDH_T;
odat.TIRS_L0_Data.group_dims.n_ROIC_therm  = n_ROIC_T;
odat.TIRS_L0_Data.group_dims.n_TIRS_therm  = n_TIRS_T;
odat.TIRS_L0_Data.group_dims.n_engd        = n_eng;
odat.TIRS_L0_Data.group_dims.n_misc        = n_misc;
odat.TIRS_L0_Data.group_dims.xtrack        = n_xtrack;
odat.TIRS_L0_Data.group_dims.allspectral   = n_spectral;

% TBD: set global attrs. (odat.global_atts.<attr_name>)
odat.global_atts = global_atts;

JSON_fspecs_L0_fpath = fullfile(ancillary_data_dir, ...
                                'payload_tlm_filespecs.json');

[L0_schema, ~] = init_nc_schema_from_JSON(JSON_fspecs_L0_fpath, false);

[m_ncs, vars_to_write] = modify_nc_schema(L0_schema, odat);

% Move Dimensions to the top level, up from the Group level.
% This makes it match similar output from python netCDF creator
nc_dimensions = m_ncs.Groups(1).Dimensions;
m_ncs.Groups = rmfield(m_ncs.Groups, 'Dimensions');
m_ncs.Dimensions = nc_dimensions;

repaired_ncwriteschema(output_fpath, m_ncs);
write_predef_nc_vars(output_fpath, vars_to_write);

end
