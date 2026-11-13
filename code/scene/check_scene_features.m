function check_scene_features()
% Signal-level checks only; these are not scene-classification results.
rng(5305,'twister'); fs=48000; t=(0:fs*3-1).'/fs;
tone=.1*sin(2*pi*500*t); noise=.02*randn(size(t));
[a,q]=scene_features(tone,fs); b=scene_features(.2*tone,fs);
assert(abs(a.Centroid_Hz-500)<10);
assert(abs((b.RMS_dBFS-a.RMS_dBFS)-20*log10(.2))<1e-8);
relative=setdiff(a.Properties.VariableNames,{'RMS_dBFS'});
assert(max(abs(a{:,relative}-b{:,relative}))<1e-7);
c=scene_features(noise,fs);
assert(c.Flatness>a.Flatness && c.Centroid_Hz>a.Centroid_Hz);
[silent,silentQ]=scene_features(zeros(size(t)),fs);
assert(silentQ.silent && all(isfinite(silent{:,:})) && ~q.silent);
shortRejected=false;
try, scene_features(zeros(100,1),fs); catch, shortRejected=true; end
assert(shortRejected);
fprintf('PASS: spectral location, level scaling, noise contrast, silence and length checks.\n');
end
