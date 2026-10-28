function cfg = latency_config(windowMs)
cfg.fs = 48000;
cfg.windowMs = windowMs;
cfg.windowLength = round(windowMs*cfg.fs/1000);
cfg.hopLength = cfg.windowLength/2;
cfg.fftLength = 2^nextpow2(cfg.windowLength);
cfg.calibrationSeconds = 0.3;
cfg.smoothingSeconds = 0.1;
cfg.minimumGain = 0.05;
cfg.bypassGain = false;
cfg.captureDiagnostics = false;
assert(mod(cfg.windowLength,2) == 0);
end
