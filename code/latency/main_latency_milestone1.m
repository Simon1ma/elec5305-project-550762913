function benchmark = main_latency_milestone1()
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
local = fullfile(root,'data','local','latency');
out = fullfile(root,'results','latency_milestone1');
audio = fullfile(out,'audio');
if ~isfolder(audio), mkdir(audio); end
[clean,fs] = audioread(fullfile(local,'clean.wav'));
[noise,noiseFs] = audioread(fullfile(local,'noise.wav'));
assert(fs == 48000 && noiseFs == fs);
prefixSamples = round(.3*fs);
rawSpeechNoise = noise(prefixSamples+(1:numel(clean)));
noiseScale = sqrt(mean(clean.^2)/mean(rawSpeechNoise.^2));
noisy = clean+noiseScale*rawSpeechNoise; % Exactly 0 dB over the speech segment.
prefix = noiseScale*noise(1:prefixSamples);
input = [prefix; noisy];
windows = [10 20 40 80]; repeats = 7;
outputs = zeros(numel(clean),numel(windows));
times = zeros(numel(windows),repeats);
readyDelay = zeros(4,1); minReadyDelay = zeros(4,1);
transport = zeros(4,1); calibrationFrames = zeros(4,1);
reconstruction = zeros(4,1); hopMs = windows.'/2;
fftLengths = zeros(4,1); windowSamples = zeros(4,1);
for k = 1:numel(windows)
    cfg = latency_config(windows(k));
    cfg.bypassGain = true;
    restored = run_causal_stream(input,cfg);
    reconstruction(k) = norm(restored-input)/norm(input);
    assert(reconstruction(k)<1e-10);
    cfg.bypassGain = false;
    run_causal_stream(input,cfg); % Warm-up excluded from timed repeats.
    for repeat = 1:repeats
        timer = tic;
        [enhanced,info] = run_causal_stream(input,cfg);
        times(k,repeat) = toc(timer);
    end
    outputs(:,k) = enhanced(prefixSamples+(1:numel(clean)));
    readyDelay(k) = info.oldestSampleReadyDelayMs;
    minReadyDelay(k) = info.newestSampleReadyDelayMs;
    transport(k) = 1000*info.transportShiftSamples/fs;
    calibrationFrames(k) = info.noiseFrameCount;
    fftLengths(k) = cfg.fftLength; windowSamples(k) = cfg.windowLength;
end
medianRTF = median(times,2)/(numel(input)/fs);
minimumRTF = min(times,[],2)/(numel(input)/fs);
maximumRTF = max(times,[],2)/(numel(input)/fs);
benchmark = table(windows.',windowSamples,fftLengths,hopMs,transport,readyDelay,minReadyDelay, ...
    medianRTF,minimumRTF,maximumRTF,calibrationFrames,reconstruction, ...
    'VariableNames',{'Window_ms','Window_samples','FFTLength','Hop_ms', ...
    'TransportShift_ms','OldestSampleReadyDelay_ms','NewestSampleReadyDelay_ms', ...
    'RTF_median','RTF_min','RTF_max','CalibrationFrames','ReconstructionRelativeError'});
writetable(benchmark,fullfile(out,'benchmark.csv'));
save(fullfile(out,'experiment.mat'),'clean','noisy','outputs','fs','windows','times','benchmark');
% Double-precision WAV preserves unscaled metric signals, even above unity.
audiowrite(fullfile(audio,'clean.wav'),clean,fs,'BitsPerSample',64);
audiowrite(fullfile(audio,'noisy.wav'),noisy,fs,'BitsPerSample',64);
for k = 1:4
    audiowrite(fullfile(audio,sprintf('wiener_%dms.wav',windows(k))), ...
        outputs(:,k),fs,'BitsPerSample',64);
end
fid = fopen(fullfile(out,'environment.txt'),'w');
assert(fid ~= -1); cleanup = onCleanup(@() fclose(fid));
fprintf(fid,'MATLAB: %s\nComputer: %s\n',version,computer);
fprintf(fid,'CPU: %s\n',getenv('PROCESSOR_IDENTIFIER'));
fprintf(fid,'Target input SNR: 0 dB\nCalibration: 300 ms\n');
fprintf(fid,'Smoothing time constant: 100 ms; gain floor: 0.05\n');
fprintf(fid,'Timing: 7 repeats after 1 warm-up per setting; includes init and flush; excludes I/O, plots, quality metrics.\n');
fprintf(fid,'RTF denominator: full input duration including calibration.\n');
fprintf(fid,'Oldest-sample ready delay excludes compute, sound-card, OS, and network delay.\n');
fprintf(fid,'Quality alignment: remove known H-sample transport shift and 300 ms prefix; no lag search.\n');
disp(benchmark);
end
