function r2_save(R, folder)
% Preserve numerical outputs and apply one shared attenuation for listening.
destination = fullfile(folder,'generated');
if ~isfolder(destination), mkdir(destination); end
writetable(R.metrics,fullfile(destination,'metrics.csv'));
writetable(R.checks,fullfile(destination,'checks.csv'));
save(fullfile(destination,'analysis.mat'),'R','-v7');
audio = [R.x R.outputs(:,2:4)];
attenuation = 0.95/max(1,max(abs(audio),[],'all'));
names = {'original.wav','modulation_lp4.wav','modulation_lp8.wav','modulation_lp16.wav'};
for k=1:4
    audiowrite(fullfile(destination,names{k}),audio(:,k)*attenuation,R.fs,'BitsPerSample',24);
end
file = fopen(fullfile(destination,'run_summary.txt'),'w');
cleanup = onCleanup(@()fclose(file));
fprintf(file,'MATLAB: %s\n',version);
fprintf(file,'Sample rate: %d Hz; samples: %d\n',R.fs,numel(R.x));
fprintf(file,'Window/hop/FFT: %d/%d/%d samples\n',R.meta.L,R.meta.H,R.meta.Nfft);
fprintf(file,'Scored interval: %.6f to %.6f seconds\n',R.scoreRangeSeconds);
fprintf(file,'Common listening attenuation: %.9f; metrics use unattenuated doubles\n',attenuation);
fprintf(file,'No added noise, no intelligibility experiment, offline processing only.\n');
fprintf(file,'CWT event centre: %.6f s; reference-only event selection\n',(R.wavelet.eventSample-1)/R.fs);
end
