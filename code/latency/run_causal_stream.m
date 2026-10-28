function [aligned, info] = run_causal_stream(input, cfg, chunkPattern)
% Recorded-file driver: only step() sees audio, one arrived block at a time.
% A zero flush occurs ONLY after the real file has ended.
if nargin < 3, chunkPattern = cfg.hopLength; end
assert(all(chunkPattern > 0 & mod(chunkPattern,1) == 0));
processor = CausalWiener(cfg);
H = cfg.hopLength;
N = numel(input);
capacity = ceil(N/H)*H+H;
raw = zeros(capacity,1);
schedule = zeros(capacity/H,2);
written = 0; rows = 0; offset = 0; iteration = 0;
capture = isfield(cfg,'captureDiagnostics') && cfg.captureDiagnostics;
if capture
    allGains = zeros(cfg.fftLength/2+1,capacity/H);
end
processingTimer = tic;
while offset < N
    iteration = iteration+1;
    take = min(chunkPattern(mod(iteration-1,numel(chunkPattern))+1),N-offset);
    [out,trace,gains] = processor.step(input(offset+(1:take)));
    raw(written+(1:numel(out))) = out;
    schedule(rows+(1:size(trace,1)),:) = trace;
    if capture, allGains(:,rows+(1:size(trace,1))) = gains; end
    written = written+numel(out); rows = rows+size(trace,1);
    offset = offset+take;
end
tailPadding = mod(-N,H)+H;
[out,trace,gains] = processor.step(zeros(tailPadding,1));
raw(written+(1:numel(out))) = out;
schedule(rows+(1:size(trace,1)),:) = trace;
if capture, allGains(:,rows+(1:size(trace,1))) = gains; end
written = written+numel(out); rows = rows+size(trace,1);
info.processingSeconds = toc(processingTimer);
raw = raw(1:written); schedule = schedule(1:rows,:);
% Fixed, known transform shift; never use a quality-optimising lag search.
aligned = raw(H+(1:N));
valid = schedule(:,2) >= 0 & schedule(:,2)+H <= N & schedule(:,1) <= N;
oldestSampleAge = schedule(valid,1)-schedule(valid,2);
assert(all(oldestSampleAge == cfg.windowLength));
info.transportShiftSamples = H;
info.captureBlockSamples = H;
info.oldestSampleReadyDelayMs = 1000*max(oldestSampleAge)/cfg.fs;
info.newestSampleReadyDelayMs = 1000*(min(oldestSampleAge)-H+1)/cfg.fs;
info.firstValidBlockConsumedSamples = schedule(find(schedule(:,2)==0,1),1);
info.raw = raw;
info.schedule = schedule;
info.noiseFrameCount = processor.noiseCount;
info.flushPaddingSamples = tailPadding;
if capture
    info.gains = allGains(:,1:rows);
    info.gainFrameStartSamples = schedule(:,2);
end
end
