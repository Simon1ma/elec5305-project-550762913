function cfg = preliminary_config()
% Initial parameters for a controlled synthetic-signal demonstration.
cfg.fs = 16000;
cfg.durationSeconds = 3;
cfg.seed = 7;
cfg.targetSNRdB = 5;
cfg.noisePrefixSeconds = 0.3;
cfg.filterOrder = 96;
cfg.cutoffHz = 1200;
cfg.windowLength = 512;
cfg.hopLength = 256;
cfg.fftLength = 1024;
cfg.decisionDirectedAlpha = 0.98;
cfg.minimumGain = 0.05;
end
