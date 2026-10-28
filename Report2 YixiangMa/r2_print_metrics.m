function r2_print_metrics(metrics)
% A compact table avoids splitting wide MATLAB tables across PDF pages.
fprintf('StopHz  Retained%%  SNR_dB  EnvCorr  LogRMSE  Consistency\n');
for k=1:height(metrics)
    fprintf('%6g %9.2f %7.2f %8.4f %8.2f %12.4g\n', ...
        metrics.StopFrequency_Hz(k),metrics.TargetDynamicEnergy_pct(k), ...
        metrics.WaveformSNR_dB(k),metrics.RMS_EnvelopeCorrelation(k), ...
        metrics.LogSpectrumRMSE_dB(k),metrics.STFTConsistencyError(k));
end
end
