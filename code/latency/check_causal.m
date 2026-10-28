function checks = check_causal()
rng(123,'twister');
windows = [10 20 40 80];
reconstruction = zeros(4,1); chunkError = zeros(4,1); enhancedChunkError = zeros(4,1);
futureError = zeros(4,1); impulseShift = zeros(4,1);
delayMs = zeros(4,1);
for k = 1:numel(windows)
    cfg = latency_config(windows(k));
    x = randn(48013,1);
    cfg.bypassGain = true;
    [restored,info] = run_causal_stream(x,cfg);
    reconstruction(k) = norm(restored-x)/norm(x);
    [irregular,~] = run_causal_stream(x,cfg,[137 1 997 48 1703]);
    chunkError(k) = max(abs(irregular-restored));
    impulse = zeros(size(x)); impulse(24001) = 1;
    [~,impulseInfo] = run_causal_stream(impulse,cfg);
    [~,peak] = max(abs(impulseInfo.raw));
    impulseShift(k) = peak-24001;
    assert(impulseShift(k) == cfg.hopLength);
    assert(info.firstValidBlockConsumedSamples == cfg.windowLength);
    delayMs(k) = info.oldestSampleReadyDelayMs;
    cfg.bypassGain = false;
    future = x; cutoff = 33600;
    future(cutoff+1:end) = 10*randn(numel(x)-cutoff,1);
    [enhanced,a] = run_causal_stream(x,cfg);
    enhancedIrregular = run_causal_stream(x,cfg,[137 1 997 48 1703]);
    enhancedChunkError(k) = max(abs(enhancedIrregular-enhanced));
    [~,b] = run_causal_stream(future,cfg);
    emittedBeforeChange = floor(cutoff/cfg.hopLength)*cfg.hopLength;
    futureError(k) = max(abs(a.raw(1:emittedBeforeChange)-b.raw(1:emittedBeforeChange)));
    assert(reconstruction(k)<1e-10 && chunkError(k)<1e-10 && enhancedChunkError(k)<1e-10 && futureError(k)==0);
end
checks = table(windows.',reconstruction,chunkError,enhancedChunkError,futureError,impulseShift,delayMs, ...
    'VariableNames',{'Window_ms','ReconstructionRelativeError','ChunkingMaxError','EnhancedChunkingMaxError', ...
    'FuturePerturbationMaxError','MeasuredTransportShift_samples','OldestSampleReadyDelay_ms'});
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
out = fullfile(root,'results','latency_milestone1');
if ~isfolder(out), mkdir(out); end
writetable(checks,fullfile(out,'checks.csv'));
disp(checks);
fprintf('PASS: reconstruction, arbitrary chunks, future invariance, impulse shift, and output scheduling.\n');
end
