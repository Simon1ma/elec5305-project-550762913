function value = calculate_snr(clean, estimate)
% Reference-to-error SNR includes residual noise and speech distortion.
validateattributes(clean, {'double'}, {'column', 'real', 'finite', 'nonempty'});
validateattributes(estimate, {'double'}, {'column', 'real', 'finite', 'numel', numel(clean)});
referenceEnergy = sum(clean.^2);
assert(referenceEnergy > 0, 'The reference must have nonzero energy.');
errorEnergy = sum((estimate-clean).^2);
value = 10*log10(referenceEnergy/errorEnergy);
end
