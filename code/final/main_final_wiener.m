function main_final_wiener(cohort)
%MAIN_FINAL_WIENER Evaluate the frozen causal processor on final shared inputs.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
if nargin<1,cohort="voicebank";end
if string(cohort)=="external",suffix='final_external';else,suffix='final';end
addpath(fullfile(root,'code','latency'));
manifest=jsondecode(fileread(fullfile(root,'results',suffix,'input_manifest.json')));
cases=manifest.cases;windows=[10 20 40 80];
local=fullfile(root,'data','local',suffix,'wiener');if ~isfolder(local),mkdir(local);end
rows={};row=0;
for c=1:numel(cases)
    data=load(fullfile(root,cases(c).input_mat));
    input=double(data.input);clean=data.clean;fs=double(data.fs);
    P=double(data.prefixSamples);N=double(data.speechSamples);
    noisy=input(P+(1:N));outputs=zeros(N,4);
    for k=1:4
        cfg=latency_config(windows(k));cfg.bypassGain=true;
        restored=run_causal_stream(input,cfg);
        reconstruction=norm(restored-input)/norm(input);
        assert(reconstruction<1e-10);
        cfg.bypassGain=false;
        [enhanced,info]=run_causal_stream(input,cfg);
        outputs(:,k)=enhanced(P+(1:N));
        assert(all(isfinite(outputs(:,k))));
        row=row+1;
        rows{row}=struct('CaseID',string(cases(c).case_id),'Window_ms',windows(k), ...
            'TransportShift_samples',info.transportShiftSamples, ...
            'OldestSampleReadyDelay_ms',info.oldestSampleReadyDelayMs, ...
            'NewestSampleReadyDelay_ms',info.newestSampleReadyDelayMs, ...
            'ReconstructionRelativeError',reconstruction,'NoiseCalibrationFrames',info.noiseFrameCount);
    end
    save(fullfile(local,string(cases(c).case_id)+".mat"),'outputs','clean','noisy','fs','windows','P','N','-v7');
    if mod(c,12)==0 || c==numel(cases)
        fprintf('Final causal Wiener: %d/%d mixtures completed.\n',c,numel(cases));
        writetable(struct2table([rows{:}]),fullfile(root,'results',suffix,'wiener_checks.csv'));
    end
end
fprintf('PASS: all final Wiener outputs, reconstruction and schedules verified.\n');
end
