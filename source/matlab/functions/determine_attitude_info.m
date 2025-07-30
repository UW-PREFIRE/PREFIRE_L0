function [sat] = determine_attitude_info(sat, flag, E, uc, tc)

% Process the position and velocity arrays produced by SGP4, and compute various
%  other needed quantities.
%
%% INPUT:
% flag :  (1, 2, or 3), specifies the amount of calculations performed for
%          input from a data simulation (1=all calcs, 2=fewer extra calcs,
%          3=no extra calcs)
% sat :  this structure array must have the following fields:
%   sat.V_eci :  (shape: 3,n), velocity vector(s) in the ECI frame [km/s]
%
%   -- if flag == 2, then 'sat' must have valid values for:
%     sat.R_eci:  (shape: 3,n), position vector(s) in ECI frame [km]
%     sat.UTC_splitvals:  (shape: n,6), array of leap-second-aware UTC,
%                        represented by [year, month, day, hour, minute, sec],
%                        where the first 5 components are integers, and 'sec' is
%                        a real number (with a possible fractional component)
%     sat.ctimeN_minus_UTC: (shape: n,1), array of values corresponding to the
%                        offset of "faux-UTC"-referenced ctime from UTC
%                        (i.e., ctimeN - UTC) [s]
%
%   -- if flag == 1, then 'sat' must ALSO have valid values for:
%     sat.ctime :  (shape: n,1), ctime
%     sat.TIRS_tau :  (scalar), TIRS integration period [s]
%
% E :  referenceEllipsoid object, in units of meters.
% uc :  the returned structure array from 'constants_unit_conversion'
% tc :  the returned structure array from 'constants_time'
%
%% OUTPUT:
% The input 'sat' structure array will have the following fields added/filled:
%
%   -- if flag == 1, then 'sat' will now have valid values for:
%     sat.geod_lat_b :  (shape: n,1), satellite geodetic latitude [deg_N] at
%                        beginning of TIRS integration period
%     sat.geod_lon_b :  (shape: n,1), satellite geodetic longitude [deg_E]] at
%                        beginning of TIRS integration period
%     sat.geod_alt_b :  (shape: n,1), satellite geodetic altitude [km]] at
%                        beginning of TIRS integration period
%     sat.geod_lat_e :  (shape: n,1), satellite geodetic latitude [deg_N] at
%                        end of TIRS integration period
%     sat.geod_lon_e :  (shape: n,1), satellite geodetic longitude [deg_E]] at
%                        end of TIRS integration period
%     sat.geod_alt_e :  (shape: n,1), satellite geodetic altitude [km]] at
%                        end of TIRS integration period
%     sat.beta:  yaw or heading to north of the velocity vector, used as
%                 principal pointing vector [deg]
%   -- if flag == 1 or 2, then 'sat' will now have valid values for:
%     sat.geod_lat :  (shape: n,1), satellite geodetic latitude [deg_N]
%     sat.geod_lon :  (shape: n,1), satellite geodetic longitude [deg_E]
%     sat.geod_alt :  (shape: n,1), satellite geodetic altitude [km]
%   -- if flag == 1, 2, or 3, then 'sat' will now have valid values for:
%     sat.quaternion :  (shape: 4,n), attitude quaternion (dummy values)

n_t = length(sat.ctimeN_minus_UTC);

% Create dummy unit quaternion values (semi-arbitrarily from ECI velocity):
sat.quaternion = zeros(4, n_t);

if flag <= 2
   % Ignore the real (but small) values of these for now:
   deltaUT1 = zeros(n_t, 1);  % [s]
   polarmotion = zeros(n_t, 2);  % [rad]

   %--- for FOV midpoints:
   
     %@@ revisit these...
   deltaAT = sat.ctimeN_minus_UTC;  % [s] full offset (equivalent to TAI - UTC)

     % Calculate the current lat, lon, altitude at each time dimension element:
   lla = eci2lla(sat.R_eci'*uc.km_to_m, ...
                 sat.UTC_splitvals, 'IAU-2000/2006', ...
                 deltaAT, deltaUT1, polarmotion, ...
                 'flattening', E.Flattening, 're', E.SemimajorAxis);

   sat.geod_lat = lla(:,1);  % [deg_N]
   sat.geod_lon = lla(:,2);  % [deg_E]
   sat.geod_alt = lla(:,3)*uc.m_to_km;  % [km], `eci2lla` outputs meters

   if flag == 1

      %--- for FOV @ time of TIRS integration start (for each TIRS integration):

      ctime_new = sat.ctime-0.5*sat.TIRS_tau;  % [s]
      [error_ca, UTC_DT_new, ctime_minus_UTC_new] = ctime_to_UTC_DT( ...
                                                 ctime_new, 'seconds', tc, uc);
        %@@ revisit this...
      deltaAT = ctime_minus_UTC_new+tc.ref_ctimeOffsetFromUTC_atEp_s;  % [s]

      UTC_new_splitvals = datevec(UTC_DT_new);

        % Calculate lat, lon, altitude:
      lla1 = eci2lla((sat.R_eci-0.5*sat.TIRS_tau*sat.V_eci)'*uc.km_to_m, ...
                     UTC_new_splitvals, 'IAU-2000/2006', ...
                     deltaAT, deltaUT1, polarmotion, ...
                     'flattening', E.Flattening, 're', E.SemimajorAxis);

      sat.geod_lat_b = lla1(:,1);  % [deg_N]
      sat.geod_lon_b = lla1(:,2);  % [deg_E]
      sat.geod_alt_b = lla1(:,3)*uc.m_to_km;  % [km], `eci2lla` outputs meters

      %--- for FOV @ time of TIRS integration end (for each TIRS integration):

      ctime_new = sat.ctime+0.5*sat.TIRS_tau;  % [s]
      [error_ca, UTC_DT_new, ctime_minus_UTC_new] = ctime_to_UTC_DT( ...
                                                 ctime_new, 'seconds', tc, uc);
        %@@ revisit this...
      deltaAT = ctime_minus_UTC_new+tc.ref_ctimeOffsetFromUTC_atEp_s;  % [s]

      UTC_new_splitvals = datevec(UTC_DT_new);

        % Calculate lat, lon, altitude:
      lla2 = eci2lla((sat.R_eci+0.5*sat.TIRS_tau*sat.V_eci)'*uc.km_to_m, ...
                     UTC_new_splitvals, 'IAU-2000/2006', ...
                     deltaAT, deltaUT1, polarmotion, ...
                     'flattening', E.Flattening, 're', E.SemimajorAxis);

      sat.geod_lat_e = lla2(:,1);  % [deg_N]
      sat.geod_lon_e = lla2(:,2);  % [deg_E]
      sat.geod_alt_e = lla2(:,3)*uc.m_to_km;  % [km], `eci2lla` outputs meters

      %--- For FOV as a whole:

      R = vecnorm(sat.R_eci(1:2,:));  % [km]
      Re = sqrt(R.*R+sat.R_eci(3,:).*sat.R_eci(3,:));  % [km]
      dP = lla1(:,1)'-lla2(:,1)';  % [deg]

      dQ = lla1(:,2)'-lla2(:,2)';  % [deg]
      i_antimeridian_issue = find(abs(dQ) > 200.);
      for i=1:length(i_antimeridian_issue)
         iq = i_antimeridian_issue(i);
         if dQ(iq) < 0
            dQ(iq) = (360+lla1(iq,2))-lla2(iq,2);
         else
            dQ(iq) = lla1(iq,2)-(360+lla2(iq,2));
         end
      end

      sat.beta = -rad2deg(atan(Re.*dP./(R.*dQ)));  % [deg]
   end
end

end
