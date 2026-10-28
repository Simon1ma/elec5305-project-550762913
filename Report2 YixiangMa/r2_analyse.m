function R = r2_analyse(x, fs)
% Complete deterministic analysis; no downloads, external runtimes, or devices.
assert(fs==16000 && iscolumn(x) && all(isfinite(x)));
[S,meta] = r2_stft(x,fs);
floorMagnitude = max(abs(S),[],'all')*1e-6;
logMagnitude = 20*log10(max(abs(S),floorMagnitude));
phase = exp(1i*angle(S));
cutoffs = [Inf 4 8 16];
outputs = zeros(numel(x),4);
targets = cell(1,4); details = cell(1,4);
score = (0:numel(x)-1).'/fs>=0.5 & (0:numel(x)-1).'/fs<(numel(x)/fs-0.5);
scoreFrames = meta.time>=0.5 & meta.time<(numel(x)/fs-0.5);
snrDb = zeros(4,1); envelopeCorrelation = snrDb; spectralRMSE = snrDb;
consistency = snrDb; retained = snrDb;
referenceEnvelope = sqrt(movmean(x.^2,round(0.020*fs)));
for k = 1:4
    [filtered,details{k}] = r2_modfilter(logMagnitude,fs/meta.H,cutoffs(k),round(0.5*fs/meta.H));
    if k==1
        target = S; % Exact bypass: log floor is an intentional analysis convention.
    else
        target = 10.^(filtered/20).*phase;
        target([1 end],:) = real(target([1 end],:));
    end
    targets{k} = target;
    output = r2_istft(target,meta);
    outputs(:,k) = output;
    [again,~] = r2_stft(output,fs);
    error = x(score)-output(score);
    snrDb(k) = 10*log10(sum(x(score).^2)/max(sum(error.^2),realmin));
    outputEnvelope = sqrt(movmean(output.^2,round(0.020*fs)));
    correlation = corrcoef(referenceEnvelope(score),outputEnvelope(score));
    envelopeCorrelation(k) = correlation(1,2);
    difference = 20*log10(max(abs(again(:,scoreFrames)),floorMagnitude))-logMagnitude(:,scoreFrames);
    spectralRMSE(k) = sqrt(mean(difference.^2,'all'));
    consistency(k) = norm(again-target,'fro')/norm(target,'fro');
    retained(k) = details{k}.retainedDynamicPercent;
end
condition = ["Bypass";"LP 4 Hz";"LP 8 Hz";"LP 16 Hz"];
R.metrics = table(condition,cutoffs.',retained,snrDb,envelopeCorrelation,spectralRMSE,consistency, ...
    'VariableNames',{'Condition','StopFrequency_Hz','TargetDynamicEnergy_pct', ...
    'WaveformSNR_dB','RMS_EnvelopeCorrelation','LogSpectrumRMSE_dB','STFTConsistencyError'});

% Calibration in the log-spectrogram domain: exact integer-cycle components.
rate = fs/meta.H; t = (0:999)/rate;
control = repmat(3+2*cos(2*pi*4*t)+cos(2*pi*16*t),9,1);
[calibrated,~] = r2_modfilter(control,rate,8,0);
amplitudes = [2*abs(mean(control(1,:).*exp(-1i*2*pi*4*t))), ...
    2*abs(mean(control(1,:).*exp(-1i*2*pi*16*t))); ...
    2*abs(mean(calibrated(1,:).*exp(-1i*2*pi*4*t))), ...
    2*abs(mean(calibrated(1,:).*exp(-1i*2*pi*16*t)))];
constant = ones(9,127)*7;
constantOutput = r2_modfilter(constant,rate,8,20);
reconstruction = norm(outputs(:,1)-x)/norm(x);
logRoundTrip = norm(r2_modfilter(logMagnitude,rate,Inf,63)-logMagnitude,'fro')/norm(logMagnitude,'fro');
checkNames = ["Unit-gain STFT reconstruction";"Unmodified 2-D FFT round trip"; ...
    "Constant log-spectrogram preservation";"4 Hz calibration amplitude error"; ...
    "16 Hz calibration residual amplitude";"Maximum inverse-FFT imaginary error"];
values = [reconstruction; logRoundTrip; max(abs(constantOutput-constant),[],'all'); ...
    abs(amplitudes(2,1)-2); amplitudes(2,2); ...
    max(cellfun(@(d)d.imaginaryRelativeError,details))];
tolerance = ones(6,1)*1e-10;
assert(all(values<tolerance),'Report 2 validation failed.');
assert(all(isfinite(outputs),'all') && all(size(outputs)==[numel(x) 4]));
assert(all(diff(retained(2:4))>=-1e-10),'Nested masks must retain nondecreasing energy.');
R.checks = table(checkNames,values,tolerance,values<tolerance, ...
    'VariableNames',{'Check','Value','Tolerance','Passed'});

% Choose an event using only the reference RMS envelope, not output quality.
novelty = [0;abs(diff(referenceEnvelope))];
margin = round(0.7*fs); novelty(1:margin)=0; novelty(end-margin:end)=0;
[~,eventSample] = max(novelty);
eventIndices = eventSample+(-round(0.4*fs):round(0.4*fs));
eventTime = (eventIndices-1)/fs;
[waveletOriginal,frequency,coi] = cwt(x(eventIndices),fs,'amor', ...
    'VoicesPerOctave',12,'FrequencyLimits',[80 4000]);
waveletFiltered = cwt(outputs(eventIndices,3),fs,'amor', ...
    'VoicesPerOctave',12,'FrequencyLimits',[80 4000]);
R.wavelet = struct('original',waveletOriginal,'filtered',waveletFiltered, ...
    'frequency',frequency,'coi',coi,'time',eventTime,'eventSample',eventSample);
R.x=x; R.fs=fs; R.meta=meta; R.S=S; R.logMagnitude=logMagnitude;
R.outputs=outputs; R.targets=targets; R.details=details; R.cutoffs=cutoffs;
R.control=struct('time',t,'original',control(1,:),'filtered',calibrated(1,:), ...
    'amplitudes',amplitudes);
R.referenceEnvelope=referenceEnvelope;
R.scoreRangeSeconds=[0.5 numel(x)/fs-0.5];
R.floorMagnitude=floorMagnitude;
end
