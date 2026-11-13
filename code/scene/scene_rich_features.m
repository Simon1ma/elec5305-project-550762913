function row = scene_rich_features(audio, fs)
%SCENE_RICH_FEATURES 69 relative acoustic, cepstral and periodicity descriptors.
% Uses official Audio Toolbox MFCC/delta computation. C0/energy are omitted.
x=double(audio(:)); x=x-mean(x);
if fs~=16000,[p,q]=rat(16000/fs);x=resample(x,p,q);end
fs=16000;
base=scene_features(x,fs); base.RMS_dBFS=[];
[C,D,DD]=mfcc(x,fs,'Window',hann(400,'periodic'),'OverlapLength',240, ...
    'FFTLength',512,'NumCoeffs',14,'LogEnergy','ignore','DeltaWindowLength',9);
C=C(:,2:14);D=D(:,2:14);DD=DD(:,2:14);
values=[mean(C,1),std(C,1,1),std(D,1,1),std(DD,1,1)];
names=[compose('MFCC_Mean_%02d',1:13),compose('MFCC_SD_%02d',1:13), ...
    compose('Delta_SD_%02d',1:13),compose('Delta2_SD_%02d',1:13)];
row=[base,array2table(values,'VariableNames',cellstr(names))];
starts=1:160:numel(x)-399; frames=x(starts+(0:399).');
frameRMS=sqrt(mean(frames.^2,1)); frames=frames.*hann(400,'periodic');
acf=real(ifft(abs(fft(frames,1024,1)).^2,[],1));
[strength,index]=max(acf(33:321,:)./max(acf(1,:),realmin),[],1);
strength=max(0,min(1,strength));
active=frameRMS>=max(max(frameRMS)*.1,1e-10);
if any(active),selected=strength(active);else,selected=0;end
voiced=active&strength>.6;
pitch=fs./(index(voiced)+31);
if numel(pitch)>1,pitchCV=std(pitch,1)/mean(pitch);else,pitchCV=0;end
envelope=frameRMS-mean(frameRMS);
envelopeACF=real(ifft(abs(fft(envelope,2^nextpow2(2*numel(envelope)))).^2));
last=min(200,numel(envelope)-10);
if last>=10&&envelopeACF(1)>eps
    repeat=max(0,max(envelopeACF(11:last+1))/envelopeACF(1));
else,repeat=0;end
extra=table(mean(selected),std(selected,1),mean(selected>.6),pitchCV,repeat, ...
    'VariableNames',{'Periodicity_Mean','Periodicity_SD','StrongPeriodicFraction','Pitch_CV','EnvelopeRepeat'});
row=[row,extra];
assert(width(row)==69&&all(isfinite(row{:,:})));
end
