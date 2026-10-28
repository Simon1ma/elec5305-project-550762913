function benchmark = main_latency_milestone2()
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
local = fullfile(root,'data','local','latency2');
out = fullfile(root,'results','latency_milestone2');
data = load(fullfile(local,'inputs.mat'));
fs = double(data.fs); clean = data.clean; inputs = data.inputs;
P = double(data.prefixSamples); N = double(data.speechSamples);
noisy = inputs(P+(1:N),:);
windows = [10 20 40 80]; labels = ["washing","keyboard"];
outputs = zeros(N,4,2); runtimes = zeros(4,7,2);
reconstruction = zeros(8,1); ready = zeros(8,1); minimumReady = zeros(8,1);
windowColumn = zeros(8,1); noiseColumn = strings(8,1); shift = zeros(8,1);
diagnostics = struct();
for noiseIndex = 1:2
    for k = 1:4
        row = (noiseIndex-1)*4+k;
        cfg = latency_config(windows(k));
        cfg.bypassGain = true;
        restored = run_causal_stream(inputs(:,noiseIndex),cfg);
        reconstruction(row) = norm(restored-inputs(:,noiseIndex))/norm(inputs(:,noiseIndex));
        assert(reconstruction(row)<1e-10);
        cfg.bypassGain = false;
        run_causal_stream(inputs(:,noiseIndex),cfg);
        for repeat = 1:7
            [enhanced,info] = run_causal_stream(inputs(:,noiseIndex),cfg);
            runtimes(k,repeat,noiseIndex) = info.processingSeconds;
        end
        outputs(:,k,noiseIndex) = enhanced(P+(1:N));
        ready(row) = info.oldestSampleReadyDelayMs;
        minimumReady(row) = info.newestSampleReadyDelayMs;
        shift(row) = 1000*info.transportShiftSamples/fs;
        windowColumn(row) = windows(k); noiseColumn(row) = labels(noiseIndex);
        if noiseIndex == 2 && ismember(windows(k),[10 80])
            cfg.captureDiagnostics = true;
            [captured,detail] = run_causal_stream(inputs(:,noiseIndex),cfg);
            assert(max(abs(captured-enhanced))<1e-12,'Diagnostics must not alter output.');
            field = sprintf('window%d',windows(k));
            diagnostics.(field).gain = detail.gains;
            diagnostics.(field).frameCentreSeconds = ...
                (detail.gainFrameStartSamples+cfg.windowLength/2-P)/fs;
            diagnostics.(field).frequency = (0:cfg.fftLength/2).'*fs/cfg.fftLength;
        end
    end
end
rtfMedian = zeros(8,1); rtfMinimum = zeros(8,1); rtfMaximum = zeros(8,1);
for c = 1:2
    rows = (c-1)*4+(1:4);
    rtf = runtimes(:,:,c)/(size(inputs,1)/fs);
    rtfMedian(rows) = median(rtf,2); rtfMinimum(rows) = min(rtf,[],2); rtfMaximum(rows) = max(rtf,[],2);
end
benchmark = table(noiseColumn,windowColumn,ready,minimumReady,shift,rtfMedian,rtfMinimum,rtfMaximum,reconstruction, ...
    'VariableNames',{'Noise','Window_ms','OldestSampleReadyDelay_ms','NewestSampleReadyDelay_ms', ...
    'TransportShift_ms','RTF_median','RTF_min','RTF_max','ReconstructionRelativeError'});
writetable(benchmark,fullfile(out,'wiener_benchmark.csv'));
trueNoise = data.trueNoise(P+(1:N),:);
save(fullfile(out,'experiment.mat'),'fs','clean','inputs','noisy','outputs','windows', ...
    'runtimes','diagnostics','trueNoise','P','N');
disp(benchmark);
end
