function [noisy, scaledNoise, scaleFactor] = mix_noise(clean, noise, targetSNRdB)
validateattributes(clean, {'double'}, {'column', 'real', 'finite', 'nonempty'});
validateattributes(noise, {'double'}, {'column', 'real', 'finite', 'numel', numel(clean)});
validateattributes(targetSNRdB, {'double'}, {'scalar', 'real', 'finite'});
signalPower = mean(clean.^2);
noisePower = mean(noise.^2);
assert(signalPower > 0 && noisePower > 0, 'Speech and noise must have nonzero energy.');
scaleFactor = sqrt(signalPower / (noisePower * 10^(targetSNRdB/10)));
scaledNoise = scaleFactor * noise;
noisy = clean + scaledNoise;
end
