function check_report2()
% Focused tests independent of the saved Live Script outputs.
state=rng; cleanup=onCleanup(@()rng(state)); rng(53,'twister');
for lengthSamples=[777 4096 16003]
    x=randn(lengthSamples,1);
    [S,meta]=r2_stft(x,16000);
    restored=r2_istft(S,meta);
    assert(numel(restored)==lengthSamples);
    assert(norm(restored-x)/norm(x)<1e-10);
end
for columns=[126 127]
    A=randn(11,columns);
    bypass=r2_modfilter(A,125,Inf,20);
    [filtered,info]=r2_modfilter(A,125,8,20);
    assert(norm(bypass-A,'fro')/norm(A,'fro')<1e-10);
    assert(isreal(filtered) && all(isfinite(filtered),'all'));
    assert(all(info.mask>=0 & info.mask<=1));
    assert(info.imaginaryRelativeError<1e-10);
end
fprintf('PASS: ragged lengths, exact STFT reconstruction, odd/even modulation grids, finite outputs, and mask bounds.\n');
end
