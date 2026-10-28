function [filtered, info] = r2_modfilter(logMagnitude, frameRate, stopHz, padding)
% Temporal mask in the 2-D Fourier domain; spectral modulation is unfiltered.
T = size(logMagnitude,2);
p = min(padding,T-1);
extended = [logMagnitude(:,p+1:-1:2), logMagnitude, ...
    logMagnitude(:,end-1:-1:end-p)];
N = size(extended,2);
centredHz = (-floor(N/2):ceil(N/2)-1)*frameRate/N;
absoluteHz = abs(centredHz);
mask = ones(1,N);
if isfinite(stopHz)
    assert(stopHz>0 && stopHz<frameRate/2);
    passHz = 0.8*stopHz;
    transition = absoluteHz>passHz & absoluteHz<stopHz;
    mask(absoluteHz>=stopHz) = 0;
    mask(transition) = 0.5*(1+cos(pi*(absoluteHz(transition)-passHz)/(stopHz-passHz)));
end
gain = ifftshift(mask);
M = fft2(extended);
modified = M.*gain;
restored = ifft2(modified);
info.imaginaryRelativeError = norm(imag(restored),'fro')/max(norm(real(restored),'fro'),eps);
filtered = real(restored(:,p+(1:T)));
dynamicColumns = ifftshift(absoluteHz)>0;
originalEnergy = sum(abs(M(:,dynamicColumns)).^2,'all');
retainedEnergy = sum(abs(modified(:,dynamicColumns)).^2,'all');
info.retainedDynamicPercent = 100*retainedEnergy/max(originalEnergy,eps);
info.temporalHz = centredHz;
info.mask = mask;
info.paddingFrames = p;
end
