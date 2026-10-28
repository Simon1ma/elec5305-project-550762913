function x = r2_istft(S, meta)
% Dual windowing with sum-of-squared-window overlap normalisation.
full = [S; conj(S(end-1:-1:2,:))];
frames = real(ifft(full,meta.Nfft,1));
output = zeros(meta.paddedLength,1);
weight = zeros(size(output));
for frame = 1:size(S,2)
    indices = (frame-1)*meta.H+(1:meta.L);
    output(indices) = output(indices)+frames(1:meta.L,frame).*meta.window;
    weight(indices) = weight(indices)+meta.window.^2;
end
valid = weight>1e-12;
output(valid) = output(valid)./weight(valid);
x = output(meta.left+(1:meta.length));
end
