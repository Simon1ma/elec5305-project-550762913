function benchmark_final_wiener(cohort)
%BENCHMARK_FINAL_WIENER Separate representative timing from quality runs.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
if nargin<1,cohort="voicebank";end
if string(cohort)=="external",suffix='final_external';else,suffix='final';end
addpath(fullfile(root,'code','latency'));
manifest=jsondecode(fileread(fullfile(root,'results',suffix,'input_manifest.json')));
cases=manifest.cases;firstSpeech=string(cases(1).speech_id);
rows={};row=0;blocks={};blockRow=0;
for category=["washing_machine","keyboard_typing"]
    candidates=find(string({cases.speech_id})==firstSpeech & ...
        string({cases.noise_class})==category & [cases.input_snr_db]==0);
    selected=cases(candidates(1));data=load(fullfile(root,selected.input_mat));input=double(data.input);
    for window=[10 20 40 80]
        cfg=latency_config(window);run_causal_stream(input,cfg); % omitted warm-up
        seconds=zeros(7,1);
        for repeat=1:7
            [~,info]=run_causal_stream(input,cfg);seconds(repeat)=info.processingSeconds;
            processor=CausalWiener(cfg);H=cfg.hopLength;offset=0;
            while offset+H<=numel(input)
                arrived=input(offset+(1:H));timer=tic;processor.step(arrived);elapsed=toc(timer);
                offset=offset+H;blockRow=blockRow+1;
                blocks{blockRow}=struct('CaseID',string(selected.case_id),'Noise',category, ...
                    'Window_ms',window,'Repeat',repeat,'ConsumedSamples',offset, ...
                    'StepSeconds',elapsed,'HopBudgetSeconds',H/cfg.fs, ...
                    'OverHopBudget',elapsed>H/cfg.fs);
            end
            % Timing above is for recurring full input calls only; no EOF flush.
        end
        rtf=seconds/(numel(input)/cfg.fs);row=row+1;
        rows{row}=struct('CaseID',string(selected.case_id),'Noise',category,'Window_ms',window, ...
            'OldestSampleReadyDelay_ms',window,'RTF_median',median(rtf), ...
            'RTF_min',min(rtf),'RTF_max',max(rtf),'Repeats',7);
        fprintf('Timing complete: %s, window %d ms.\n',category,window);
    end
end
writetable(struct2table([rows{:}]),fullfile(root,'results',suffix,'wiener_benchmark.csv'));
writetable(struct2table([blocks{:}]),fullfile(root,'results',suffix,'wiener_block_timings.csv'));
fprintf('PASS: separate repeated RTF and per-hop timing measurements saved.\n');
end
