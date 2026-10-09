function [enhanced, b] = fir_baseline(noisy, cfg)
% Offline forward-backward filtering: the effective response is |H|^2.
b = fir1(cfg.filterOrder, cfg.cutoffHz/(cfg.fs/2), ...
    'low', hamming(cfg.filterOrder+1));
enhanced = filtfilt(b, 1, noisy);
end
