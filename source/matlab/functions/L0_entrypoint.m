function [successful_completion, error_ca] = L0_entrypoint(varargin)

successful_completion = false;

pd = cfg_L0_toplevel_IO;  % Get/set shared filepaths, dirs, control params

switch pd.proc_mode
   case 52
      error_ca = create_orbitsim_bus_tlm(pd);
   otherwise
      tmp_str = sprintf('ERROR: unknown processing mode (%d)', pd.proc_mode);
      error_ca = {tmp_str, 2};
end

if (error_ca{2} ~= 0)
   fprintf(2, '%s\n', error_ca{1});
   return
end

% Output which MatLab toolboxes are used by this program
%license('inuse')

successful_completion = true;

end
