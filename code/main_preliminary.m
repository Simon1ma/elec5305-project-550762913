function results = main_preliminary()
% Run from any working directory. Results are saved relative to this file.
cfg = preliminary_config();
rng(cfg.seed, 'twister');
root = fileparts(fileparts(mfilename('fullpath')));
outDir = fullfile(root, 'results', 'preliminary');
figDir = fullfile(outDir, 'figures');
audioDir = fullfile(outDir, 'audio');
if ~isfolder(figDir), mkdir(figDir); end
if ~isfolder(audioDir), mkdir(audioDir); end
[clean, t] = generate_synthetic_signal(cfg.fs, cfg.durationSeconds);
hum = sin(2*pi*60*t) + 0.5*sin(2*pi*120*t);
rawNoise = 0.75*randn(size(clean)) + 0.25*hum;
[noisy, scaledNoise, noiseScale] = mix_noise(clean, rawNoise, cfg.targetSNRdB);
prefixLength = round(cfg.noisePrefixSeconds*cfg.fs);
prefixTime = (-prefixLength:-1).'/cfg.fs;
prefixHum = sin(2*pi*60*prefixTime) + 0.5*sin(2*pi*120*prefixTime);
noisePrefix = noiseScale * (0.75*randn(prefixLength,1) + 0.25*prefixHum);
noisyWithPrefix = [noisePrefix; noisy];
[firWithPrefix, coefficients] = fir_baseline(noisyWithPrefix, cfg);
[wienerWithPrefix, wienerInfo] = wiener_enhancement(noisyWithPrefix, cfg);
speechIndices = prefixLength + (1:numel(clean));
firOutput = firWithPrefix(speechIndices);
wienerOutput = wienerWithPrefix(speechIndices);
inputSNR = calculate_snr(clean, noisy);
assert(abs(inputSNR-cfg.targetSNRdB) < 1e-10);
method = ["Unprocessed"; "FIR"; "Wiener"];
outputSNR = [inputSNR; calculate_snr(clean, firOutput); calculate_snr(clean, wienerOutput)];
results = table(method, repmat(inputSNR,3,1), outputSNR, outputSNR-inputSNR, ...
    'VariableNames', {'Method', 'InputSNR_dB', 'OutputSNR_dB', 'Improvement_dB'});
writetable(results, fullfile(outDir, 'metrics.csv'));
save(fullfile(outDir, 'experiment.mat'), 'cfg', 'clean', 'noisy', 'scaledNoise', ...
    'noisePrefix', 'firOutput', 'wienerOutput', 'coefficients', 'results', 'wienerInfo');
% WAV files use one shared attenuation, never separate peak normalisation.
signals = [clean, noisy, firOutput, wienerOutput];
playbackScale = min(1, 0.99/max(abs(signals(:))));
audioNames = {'clean', 'noisy', 'fir', 'wiener'};
for k = 1:4
    audiowrite(fullfile(audioDir, [audioNames{k} '.wav']), ...
        playbackScale*signals(:,k), cfg.fs, 'BitsPerSample', 24);
end
plot_preliminary(signals, t, cfg, results, coefficients, figDir);
fid = fopen(fullfile(outDir, 'run_summary.txt'), 'w');
assert(fid ~= -1, 'Cannot write run summary.');
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, 'Synthetic demonstration only; not real-speech evaluation.\n');
fprintf(fid, 'MATLAB: %s\nSeed: %d\n', version, cfg.seed);
fprintf(fid, 'Noise: white Gaussian plus 60/120 Hz hum\n');
fprintf(fid, 'Prefix samples excluded from scoring: %d\n', prefixLength);
fprintf(fid, 'Unit-gain reconstruction relative error: %.3g\n', wienerInfo.reconstructionRelativeError);
fprintf(fid, 'Complete noise-only frames: %d\n', wienerInfo.noiseFrameCount);
fprintf(fid, 'Shared WAV playback scale (not used for metrics): %.9f\n', playbackScale);
for k = 1:height(results)
    fprintf(fid, '%s: output SNR %.6f dB; improvement %.6f dB\n', ...
        char(results.Method(k)), outputSNR(k), outputSNR(k)-inputSNR);
end
disp(results);
fprintf('Reconstruction relative error: %.3g\n', wienerInfo.reconstructionRelativeError);
fprintf('Results directory: %s\n', outDir);
end

function plot_preliminary(signals, t, cfg, results, coefficients, figDir)
names = {'Clean reference', 'Noisy input', 'FIR output', 'Wiener output'};
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1100 850]);
cleanup = onCleanup(@() close(fig));
tiledlayout(4,1, 'TileSpacing', 'compact');
amplitudeLimit = max(abs(signals(:))) * 1.05;
for k = 1:4
    nexttile;
    plot(t, signals(:,k)); grid on;
    xlabel('Time (s)'); ylabel('Amplitude');
    title(names{k}); ylim([-amplitudeLimit amplitudeLimit]); xlim([0 t(end)]);
end
exportgraphics(fig, fullfile(figDir, 'waveforms.png'), 'Resolution', 180);
clear cleanup;

fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1200 800]);
cleanup = onCleanup(@() close(fig));
tiledlayout(2,2, 'TileSpacing', 'compact');
win = hann(cfg.windowLength, 'periodic');
for k = 1:4
    nexttile;
    [s,f,tt] = spectrogram(signals(:,k), win, cfg.windowLength-cfg.hopLength, ...
        cfg.fftLength, cfg.fs);
    imagesc(tt, f/1000, 20*log10(max(abs(s),1e-8)));
    axis xy; ylim([0 cfg.fs/2000]); clim([-80 40]);
    xlabel('Time (s)'); ylabel('Frequency (kHz)'); title(names{k});
    cb = colorbar; cb.Label.String = 'STFT magnitude (dB)';
end
colormap(fig, parula);
exportgraphics(fig, fullfile(figDir, 'spectrograms.png'), 'Resolution', 180);
clear cleanup;

fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 950 420]);
cleanup = onCleanup(@() close(fig));
tiledlayout(1,2);
nexttile;
bar(categorical(results.Method, results.Method), results.OutputSNR_dB);
ylabel('Reference-to-error SNR (dB)'); title('Synthetic signal: 5 dB input'); grid on;
nexttile;
[response,frequency] = freqz(coefficients,1,2048,cfg.fs);
plot(frequency/1000,20*log10(max(abs(response).^2,1e-8)));
xlabel('Frequency (kHz)'); ylabel('Magnitude (dB)');
title('Effective forward-backward FIR response'); grid on; ylim([-100 5]);
exportgraphics(fig, fullfile(figDir, 'snr_and_fir_response.png'), 'Resolution', 180);
end
