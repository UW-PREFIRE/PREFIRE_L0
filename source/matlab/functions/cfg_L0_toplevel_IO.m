function [pd] = cfg_L0_toplevel_IO
% Assigns filepaths, directories/paths, and other control parameters to the
%  fields of a new structure array 'pd'

if isunix

   [func_path, ~, ~] = fileparts(which('cfg_L0_toplevel_IO'));
   top_path = fullfile(func_path, '..', '..', '..'); % has 'dist','source', etc.
   begDir = cd(top_path);
   pd.top_path = pwd;  % Resolve '.' and '..'
   cd(begDir);
   top_path = pd.top_path;

   tmp = getenv('PROC_MODE');
   if strlength(tmp) < 1  % relevant environment variables are not set
      pd.proc_mode = 52;

      pd.tools_anc_data_dir = fullfile(top_path, '..', ...
                                       'PREFIRE_tools/dist/ancillary');

      if (pd.proc_mode == 52)
         pd.orbitsim_cfg_fpath = 'cfg-orbitsim_01.json';
      end

   else
      pd = obtain_from_env_vars(pd, tmp);
   end

else  % MS-Windows

   [func_path, ~, ~] = fileparts(which('cfg_L0_toplevel_IO'));
   top_path = fullfile(func_path, '..', '..', '..'); % has 'dist','source', etc.
   begDir = cd(top_path);
   pd.top_path = pwd;  % Resolve '.' and '..'
   cd(begDir);
   top_path = pd.top_path;

   tmp = getenv('PROC_MODE');
   if strlength(tmp) < 1  % relevant environment variables are not set
      pd.proc_mode = 52;  % Change this to run different modes

      pd.tools_anc_data_dir = fullfile(top_path, '..', ...
                                       'PREFIRE_tools\dist\ancillary');

      if (pd.proc_mode == 52)
         pd.orbitsim_cfg_fpath = 'cfg-orbitsim_01.json';
      end

   else
      pd = obtain_from_env_vars(pd, tmp);
   end

end

 function pd = obtain_from_env_vars(pd, procmode)
    pd.top_path = getenv('PACKAGE_TOP_DIR');
    pd.proc_mode = str2double(procmode);

    pd.tools_anc_data_dir = getenv('TOOLS_ANC_DIR');

    if (pd.proc_mode == 52)
       pd.orbitsim_cfg_fpath = getenv('ORBITSIM_CFG_FILE');
    end
 end

end
