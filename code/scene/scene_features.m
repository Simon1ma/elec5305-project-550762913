function [features, quality] = scene_features(audio, fs)
%SCENE_FEATURES Summarise a sound-scene recording using acoustic features.
% One row per complete recording. Windows are observations within that row,
% not independent training examples. No classifier labels enter extraction.
validateattributes(audio,{'double'},{'real','finite','nonempty'});
validateattributes(fs,{'numeric'},{'scalar','positive','finite'});
assert(isvector(audio),'Supply a mono recording.');
x=audio(:); quality.durationSeconds=numel(x)/fs;
assert(quality.durationSeconds>=0.5,'At least 0.5 seconds is required.');
quality.peak=max(abs(x)); quality.fullScaleSamples=sum(abs(x)>=1-1/32768);
quality.silent=all(x==0);
x=x-mean(x);
if fs~=16000
    [p,q]=rat(16000/fs); x=resample(x,p,q); fs=16000;
end
L=400; H=160; nfft=512;
starts=1:H:numel(x)-L+1;
frames=x(starts+(0:L-1).');
frameRMS=sqrt(mean(frames.^2,1));
amplitude=sqrt(mean(x.^2));
safePower=max(amplitude^2*1e-12,realmin);
S=abs(fft(frames.*hann(L,'periodic'),nfft,1));
S=S(1:nfft/2+1,:); P=S.^2;
frequency=(0:nfft/2).'*fs/nfft;
mass=sum(P,1); safeMass=max(mass,realmin);
centroid=sum(frequency.*P,1)./safeMass;
flatness=exp(mean(log(max(P,safePower)),1))./max(mean(P,1),safePower);
probability=P./safeMass;
entropy=-sum(probability.*log2(max(probability,realmin)),1)/log2(size(P,1));
normalisedMagnitude=S./max(sqrt(sum(S.^2,1)),realmin);
flux=sqrt(sum(max(diff(normalisedMagnitude,1,2),0).^2,1));
zcr=mean(frames(1:end-1,:).*frames(2:end,:)<0,1);
lowFraction=sum(P(frequency<=500,:),1)./safeMass;
highFraction=sum(P(frequency>=3000,:),1)./safeMass;
rolloff=zeros(size(mass));
for k=1:numel(mass)
    if mass(k)>0
        rolloff(k)=frequency(find(cumsum(P(:,k))>=0.85*mass(k),1));
    end
end
features=table(20*log10(max(amplitude,1e-12)), ...
    std(frameRMS,1)/max(mean(frameRMS),eps), ...
    quantile(frameRMS,.95)/max(quantile(frameRMS,.5),eps), ...
    mean(zcr),mean(centroid),std(centroid,1),mean(flatness), ...
    mean(entropy),mean(flux),std(flux,1),mean(lowFraction), ...
    mean(highFraction),mean(rolloff), ...
    'VariableNames',{'RMS_dBFS','RMS_CV','BurstRatio95_50','ZCR', ...
    'Centroid_Hz','Centroid_SD_Hz','Flatness','Entropy', ...
    'PositiveFlux','PositiveFlux_SD','LowFraction','HighFraction','Rolloff85_Hz'});
assert(all(isfinite(features{:,:})),'Nonfinite feature output.');
end
