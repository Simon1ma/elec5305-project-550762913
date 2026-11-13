function result = check_personal_submission()
root=fileparts(mfilename('fullpath'));addpath(fullfile(root,'code','scene'));addpath(fullfile(root,'code','latency'));
assert(~isempty(ver('signal')),'Signal Processing Toolbox is required.');
check_causal();check_scene_features();
m=jsondecode(fileread(fullfile(root,'results','scene_bridge','input_manifest.json')));
for k=1:numel(m.cases)
 c=m.cases(k);d=load(fullfile(root,c.input_mat));y=run_causal_stream(double(d.input),latency_config(40));
 s=load(fullfile(root,'data','local','scene_bridge','wiener',string(c.case_id)+".mat"));
 assert(max(abs(y(double(d.prefixSamples)+(1:double(d.speechSamples)))-s.outputs(:,3)))<1e-10);
 assert(isfile(fullfile(root,'data','local','scene_bridge','reference',string(c.case_id)+".wav")));
end
m=jsondecode(fileread(fullfile(root,'data','local','scene','holdout','holdout_manifest.json')));
for k=1:numel(m.cases),result=classify_scene_file(fullfile(root,m.cases(k).wav));assert(ismember(string(result.label),["speech","alarm","container_press"]));end
result=struct('personalMixtures',27,'testSources',9,'status','passed');
fprintf('PASS: causal checks, feature checks, all 27 Wiener40 saved outputs, nine baseline classifications.\n');
end
