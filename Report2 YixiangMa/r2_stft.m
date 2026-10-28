function [S, meta] = r2_stft(x, fs)
% Fixed-grid, padded STFT used for every report condition.
x = x(:);
L = 512; H = 128; Nfft = 512;
w = hann(L,'periodic');
left = L;
padded = [zeros(left,1); x; zeros(L,1)];
count = ceil((numel(padded)-L)/H)+1;
padded(end+1:(count-1)*H+L) = 0;
indices = (1:L).' + (0:count-1)*H;
full = fft(padded(indices).*w,Nfft,1);
S = full(1:Nfft/2+1,:);
meta = struct('fs',fs,'window',w,'L',L,'H',H,'Nfft',Nfft, ...
    'left',left,'length',numel(x),'paddedLength',numel(padded));
meta.time = ((0:count-1)*H+L/2-left)/fs;
meta.frequency = (0:Nfft/2).'*fs/Nfft;
end
