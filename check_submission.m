function result = check_submission()
root=fileparts(mfilename('fullpath'));addpath(fullfile(root,'code','latency'));addpath(fullfile(root,'code','scene'));addpath(fullfile(root,'code','final'));
assert(~isempty(ver('signal')),'Signal Processing Toolbox is required.');
check_causal();check_scene_features();result=run_public_demo(false);
assert(abs(result.noisySNR)<1e-5);assert(all(isfinite(result.wienerSNR)));
fprintf('PASS: fresh-download self-check. No personal recording, Python or neural-runtime download required.\n');
end
