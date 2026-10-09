function [enhanced, info] = wiener_enhancement(noisy, cfg)
% Estimate noise using only complete frames in the noise-only prefix.
% No clean speech or isolated ground-truth noise is an input here.
validateattributes(noisy, {'double'}, {'column', 'real', 'finite', 'nonempty'});
assert(cfg.hopLength == cfg.windowLength/2, ...
    'This Hann/OLA implementation requires 50 percent overlap.');
assert(cfg.minimumGain >= 0 && cfg.minimumGain <= 1);
assert(cfg.decisionDirectedAlpha >= 0 && cfg.decisionDirectedAlpha < 1);
assert(numel(noisy) > round(cfg.noisePrefixSeconds*cfg.fs));
win = hann(cfg.windowLength, 'periodic');
padLength = cfg.windowLength;
tailLength = padLength + mod(-numel(noisy), cfg.hopLength);
padded = [zeros(padLength,1); noisy; zeros(tailLength,1)];
transformArgs = {'Window', win, ...
    'OverlapLength', cfg.windowLength-cfg.hopLength, ...
    'FFTLength', cfg.fftLength, 'FrequencyRange', 'twosided'};
[Y, frequency, frameTime] = stft(padded, cfg.fs, transformArgs{:});
frameTime = frameTime - padLength/cfg.fs;
halfWindowSeconds = cfg.windowLength/(2*cfg.fs);
noiseFrames = frameTime >= halfWindowSeconds ...
    & frameTime <= cfg.noisePrefixSeconds-halfWindowSeconds;
assert(nnz(noiseFrames) >= 2, 'The prefix must contain at least two complete frames.');
observedPower = abs(Y).^2;
noisePSD = mean(observedPower(:,noiseFrames), 2);
noisePSD = max(noisePSD, max(max(noisePSD)*1e-12, realmin));
gain = zeros(size(observedPower));
previousEnhancedPower = zeros(size(noisePSD));
for frame = 1:size(Y,2)
    posteriorSNR = observedPower(:,frame)./noisePSD;
    instantaneousPrior = max(posteriorSNR-1, 0);
    if frame == 1
        priorSNR = instantaneousPrior;
    else
        priorSNR = cfg.decisionDirectedAlpha * previousEnhancedPower./noisePSD ...
            + (1-cfg.decisionDirectedAlpha) * instantaneousPrior;
    end
    gain(:,frame) = max(cfg.minimumGain, priorSNR./(1+priorSNR));
    previousEnhancedPower = gain(:,frame).^2 .* observedPower(:,frame);
end
inverseArgs = [transformArgs, {'Method', 'ola', 'ConjugateSymmetric', true}];
unitGainOutput = istft(Y, cfg.fs, inverseArgs{:});
filteredOutput = istft(gain.*Y, cfg.fs, inverseArgs{:});
keep = padLength + (1:numel(noisy));
assert(numel(unitGainOutput) >= keep(end), 'ISTFT returned insufficient samples.');
reconstruction = unitGainOutput(keep);
enhanced = filteredOutput(keep);
info.reconstructionRelativeError = norm(reconstruction-noisy)/max(norm(noisy), eps);
info.noiseFrameCount = nnz(noiseFrames);
info.noiseFrameTimes = frameTime(noiseFrames);
info.noisePSD = noisePSD;
info.gain = gain;
info.frequency = frequency;
info.frameTime = frameTime;
assert(info.reconstructionRelativeError < 1e-10, ...
    'Unit-gain STFT/ISTFT reconstruction failed.');
assert(all(isfinite(enhanced)), 'Wiener output contains invalid values.');
end
