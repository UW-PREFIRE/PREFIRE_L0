function app_matlab_run()

try
   [successful_completion, error_ca] = L0_entrypoint();
   if successful_completion
      exit(0);
   else
      fprintf(2, error_ca{1});
      exit(error_ca{2});  % error
   end
catch e
   fprintf(1, 'ERROR: %s\n', e.identifier);
   fprintf(1, '%s\n', e.message);
   for i = 1:numel(e.stack)
      e.stack(i)
   end
   exit(1);  % error
end

end
