function run_adaptive_comparison()
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root,'code','latency'));
m=jsondecode(fileread(fullfile(root,'results','scene_bridge','input_manifest.json')));
folder=fullfile(root,'data','local','scene_adaptive');if ~isfolder(folder),mkdir(folder);end
checks=table();
for k=1:numel(m.cases)
 c=m.cases(k);d=load(fullfile(root,c.input_mat));x=double(d.input);cfg=latency_config(40);
 fixed=run_causal_stream(x,cfg);saved=load(fullfile(root,'data','local','scene_bridge','wiener',string(c.case_id)+".mat"));
 P=double(d.prefixSamples);N=double(d.speechSamples);
 err=norm(fixed(P+(1:N))-saved.outputs(:,3))/max(norm(saved.outputs(:,3)),eps);assert(err<1e-12);
 y=run_exploratory_stream(x,cfg);
 if k==1
  cfg.bypassGain=true;b=run_exploratory_stream(x,cfg);assert(norm(b-x)/norm(x)<1e-10);cfg.bypassGain=false;
  z=run_exploratory_stream(x,cfg,[137 997 2048]);assert(norm(z-y)<1e-10);
  split=floor(numel(x)/2);changed=x;changed(split+1:end)=0;
  z=run_exploratory_stream(changed,cfg);safe=split-cfg.windowLength;assert(norm(z(1:safe)-y(1:safe))<1e-10);
 end
 output=y(P+(1:N));save(fullfile(folder,string(c.case_id)+".mat"),'output','-v7');
 checks=[checks;table(string(c.case_id),err,'VariableNames',{'CaseID','FixedBaselineRelativeError'})];
end
writetable(checks,fullfile(root,'results','scene_adaptive','checks.csv'));
fprintf('PASS: 27 baseline matches; reconstruction, chunk and future invariance.\n');
end
