function capture_final_event(cohort)
%CAPTURE_FINAL_EVENT Gain diagnostics on an outcome-independent keyboard case.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
if nargin<1,cohort="external";end
if string(cohort)=="external",suffix='final_external';else,suffix='final';end
addpath(fullfile(root,'code','latency'));
manifest=jsondecode(fileread(fullfile(root,'results',suffix,'input_manifest.json')));
cases=manifest.cases;
selected=cases(find(string({cases.speech_id})==string(cases(1).speech_id) & ...
    string({cases.noise_class})=="keyboard_typing" & [cases.input_snr_db]==0,1));
data=load(fullfile(root,selected.input_mat));input=double(data.input);
P=double(data.prefixSamples);N=double(data.speechSamples);fs=double(data.fs);
clean=data.clean;noisy=input(P+(1:N));trueNoise=noisy-clean;
saved=load(fullfile(root,'data','local',suffix,'wiener',string(selected.case_id)+".mat"));
diagnostics=struct();
for window=[10 80]
    cfg=latency_config(window);cfg.captureDiagnostics=true;
    [enhanced,info]=run_causal_stream(input,cfg);
    assert(max(abs(enhanced(P+(1:N))-saved.outputs(:,[10 20 40 80]==window)))<1e-12);
    field=sprintf('window%d',window);
    diagnostics.(field).gain=info.gains;
    diagnostics.(field).frameCentreSeconds=(info.gainFrameStartSamples+cfg.windowLength/2-P)/fs;
    diagnostics.(field).frequency=(0:cfg.fftLength/2).'*fs/cfg.fftLength;
end
caseID=char(selected.case_id); % Portable MAT character vector for SciPy.
save(fullfile(root,'data','local',suffix,'event_diagnostics.mat'), ...
    'diagnostics','clean','noisy','trueNoise','input','fs','P','N','caseID','-v7');
fprintf('PASS: event diagnostics do not alter the evaluated outputs.\n');
end
