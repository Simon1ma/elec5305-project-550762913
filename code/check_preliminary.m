function check_preliminary()
% Focused checks for reconstruction, noise calibration, and repeatability.
cfg = preliminary_config();
rng(42, 'twister');
for lengthSamples = [48001, 12345, 6001]
    x = randn(lengthSamples,1);
    [out, info] = wiener_enhancement(x, cfg);
    assert(numel(out) == numel(x));
    assert(info.reconstructionRelativeError < 1e-10);
    assert(all(info.gain(:) >= cfg.minimumGain & info.gain(:) <= 1));
    assert(all(info.noiseFrameTimes >= cfg.windowLength/(2*cfg.fs)));
    assert(all(info.noiseFrameTimes <= cfg.noisePrefixSeconds-cfg.windowLength/(2*cfg.fs)));
end
clean = randn(8000,1);
noise = randn(8000,1);
for target = [0, 5, 10]
    noisy = mix_noise(clean, noise, target);
    assert(abs(calculate_snr(clean,noisy)-target) < 1e-10);
end
assert(isinf(calculate_snr(clean,clean)));
assert(abs(calculate_snr(clean,zeros(size(clean)))) < 1e-12);
first = main_preliminary();
second = main_preliminary();
assert(isequal(first,second), 'Repeated runs must produce identical metrics.');
fprintf('PASS: reconstruction, length, gain bounds, prefix isolation, SNR mixing, and repeatability.\n');
end
