function run_personal_wiener()
%RUN_PERSONAL_WIENER Reuse all four unchanged causal settings on personal mixtures.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root,'code','latency'));
out=fullfile(root,'results','scene_bridge');
manifest=jsondecode(fileread(fullfile(out,'input_manifest.json')));
folder=fullfile(root,'data','local','scene_bridge','wiener');
if ~isfolder(folder),mkdir(folder);end
windows=[10 20 40 80];checks=table();
for c=1:numel(manifest.cases)
    item=manifest.cases(c);data=load(fullfile(root,item.input_mat));
    input=double(data.input);clean=data.clean;fs=double(data.fs);
    P=double(data.prefixSamples);N=double(data.speechSamples);
    noisy=input(P+(1:N));outputs=zeros(N,4);
    for k=1:4
        cfg=latency_config(windows(k));cfg.bypassGain=true;
        restored=run_causal_stream(input,cfg);
        reconstruction=norm(restored-input)/norm(input);assert(reconstruction<1e-10);
        cfg.bypassGain=false;[enhanced,info]=run_causal_stream(input,cfg);
        outputs(:,k)=enhanced(P+(1:N));assert(all(isfinite(outputs(:,k))));
        row=table(string(item.case_id),windows(k),reconstruction,info.noiseFrameCount, ...
            info.oldestSampleReadyDelayMs,'VariableNames', ...
            {'CaseID','Window_ms','ReconstructionRelativeError','CalibrationFrames','ReadyDelay_ms'});
        checks=[checks;row]; %#ok<AGROW>
    end
    save(fullfile(folder,string(item.case_id)+".mat"),'outputs','clean','noisy','fs','windows','P','N','-v7');
    if mod(c,9)==0,fprintf('Personal Wiener %d/27\n',c);end
end
writetable(checks,fullfile(out,'wiener_checks.csv'));
fprintf('PASS: all 27 personal mixtures, four frozen settings and reconstruction checks.\n');
end
