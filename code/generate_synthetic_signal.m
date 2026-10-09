function [clean, t] = generate_synthetic_signal(fs, durationSeconds)
% Reproduce the speech-like signal from Audio Processing Report 1.
t = (0:round(fs * durationSeconds)-1).' / fs;
f0 = 130 + 20 * sin(2*pi*1.2*t);
phase = 2*pi*cumsum(f0)/fs;
clean = 0.55*sin(phase) + 0.28*sin(2*phase) ...
    + 0.16*sin(3*phase) + 0.08*sin(4*phase);
envelope = 0.55 + 0.45*sin(2*pi*2.1*t).^2;
syllableGate = double(mod(t, 0.75) < 0.52);
clean = clean .* envelope .* syllableGate;
clean = clean / max(abs(clean));
end
