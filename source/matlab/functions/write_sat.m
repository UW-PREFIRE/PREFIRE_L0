function [error_ca] = write_sat(fileout, sat, i_beg, i_end, tc, uc)

csvID = fopen(fileout, 'w');
str_to_write = sprintf('%s\n', 'ft,TIME_RTC_TAI_SECOND,TIME_RTC_TAI_SUBSEC,REFS_REFS_VALID,REFS_ESM_VALID,REFS_BETA_ANGLE,REFS_SUN_ECLIPSE_EARTH_PENUMBRA_FLAG,REFS_SUN_ECLIPSE_EARTH_UMBRA_FLAG,REFS_SUN_ECLIPSE_MOON_PENUMBRA_FLAG,REFS_SUN_ECLIPSE_MOON_UMBRA_FLAG,REFS_POSITION_WRT_ECI1,REFS_POSITION_WRT_ECI2,REFS_POSITION_WRT_ECI3,REFS_VELOCITY_WRT_ECI1,REFS_VELOCITY_WRT_ECI2,REFS_VELOCITY_WRT_ECI3,ATT_DET_Q_BODY_WRT_ECI1,ATT_DET_Q_BODY_WRT_ECI2,ATT_DET_Q_BODY_WRT_ECI3,ATT_DET_Q_BODY_WRT_ECI4,ATT_DET_ATTITUDE_VALID,ATT_CMD_PRI_REF_DIR,ATT_CMD_PRI_CMD_VEC_BODY1,ATT_CMD_PRI_CMD_VEC_BODY2,ATT_CMD_PRI_CMD_VEC_BODY3,ATT_CMD_SEC_REF_DIR,ATT_CMD_SEC_CMD_VEC_BODY1,ATT_CMD_SEC_CMD_VEC_BODY2,ATT_CMD_SEC_CMD_VEC_BODY3,ATT_CMD_CMD_TARGET1,ATT_CMD_CMD_TARGET2,ATT_CMD_CMD_TARGET3');
fwrite(csvID, str_to_write);

first_to_write = randi([1, 4], length(sat.UTC_DT), 1);

   % ctimeN: [seconds since 2000-01-01T00:00:00 "faux-UTC"]
[error_ca, ctimeN] = change_ctime_epoch_type(sat.ctime, 's', false, tc, uc);
if (error_ca{2} ~= 0)
   return
end

% Simulate condition seen in testing where no ESM REFS info was available (not
%  even 'REFS_ESM_VALID'):
if (i_end-i_beg+1 > 6)
   i_refESM_off = i_end-4;  % Simulate this condition at this entry
else
   i_refESM_off = 0;  % No such condition will be produced
end

downlink_info_here = isfield(sat, 'is_downlink');

for i=i_beg:i_end
   t = datevec(sat.UTC_DT(i));
   UTC_timestamp_str = sprintf('%04d-%02d-%02dT%02d:%02d:%02d.%03dZ', ...
                               t(1), t(2), t(3), t(4), t(5), t(6), 0.0);

   % TIME group:
   strg_to_write{1} = sprintf('%s,%.0f,%1d,,,,,,,,,,,,,,,,,,,,,,,,,,,,,\n', ...
                             UTC_timestamp_str, ctimeN(i,1), 4);

   % REFS group:
   if (i ~= i_refESM_off)
       fmt = '%s,,,YES,YES,-10000,NO,NO,NO,NO,%.12f,%.12f,%.12f,%.12f,%.12f,%.12f,,,,,,,,,,,,,,,,\n';
   else
       fmt = '%s,,,YES,,,,,,,%.12f,%.12f,%.12f,%.12f,%.12f,%.12f,,,,,,,,,,,,,,,,\n';
   end

   strg_to_write{2} = sprintf(fmt, UTC_timestamp_str, ...
                            sat.R_eci(1,i), sat.R_eci(2,i), sat.R_eci(3,i), ...
                            sat.V_eci(1,i), sat.V_eci(2,i), sat.V_eci(3,i));

   % ATT_DET group:
   strg_to_write{3} = sprintf('%s,,,,,,,,,,,,,,,,%.12f,%.12f,%.12f,%.12f,YES,,,,,,,,,,,\n', ...
               UTC_timestamp_str, sat.quaternion(1,i), sat.quaternion(2,i), ...
                              sat.quaternion(3,i), sat.quaternion(4,i));

   % ATT_CMD group:
   if downlink_info_here
      if sat.is_downlink(i,1)
         strg_to_write{4} = sprintf('%s,,,,,,,,,,,,,,,,,,,,,TARG_ECEF,%.10f,%.10f,%.10f,SUN,%.10f,%.10f,%.10f,%.12f,%.12f,%.12f\n', ...
                            UTC_timestamp_str, 0.9999999749999999,0,0, ...
                                         0, -0.42261537405, -0.90630766965, ...
                       4972.9091796875, -357.5090026855469, 3965.611083984375);
      else
         strg_to_write{4} = sprintf('%s,,,,,,,,,,,,,,,,,,,,,GCNADIR,%.10f,%.10f,%.10f,VEL,%.10f,%.10f,%.10f,%.12f,%.12f,%.12f\n', ...
                            UTC_timestamp_str, 0, 0.9999999749999999, 0, ...
                                              -0.9999999749999999, 0, 0, ...
                                              0, 0, 0);
      end
   else
      strg_to_write{4} = sprintf('%s,,,,,,,,,,,,,,,,,,,,,GCNADIR,%.10f,%.10f,%.10f,VEL,%.10f,%.10f,%.10f,%.12f,%.12f,%.12f\n', ...
                            UTC_timestamp_str, 0, 0.9999999749999999, 0, ...
                                              -0.9999999749999999, 0, 0, ...
                                              0, 0, 0);
   end

   % Lines for same UTC timestamp are written in "random" order:
   iw = first_to_write(i);
   fwrite(csvID, strg_to_write{iw});
   iw = mod(iw, 4)+1;
   fwrite(csvID, strg_to_write{iw});
   iw = mod(iw, 4)+1;
   fwrite(csvID, strg_to_write{iw});
   iw = mod(iw, 4)+1;
   fwrite(csvID, strg_to_write{iw});
end
fclose(csvID);

end
