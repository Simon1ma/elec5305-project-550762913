function features = extract_scene_development()
%EXTRACT_SCENE_DEVELOPMENT One acoustic feature row per full source recording.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
manifest=jsondecode(fileread(fullfile(root,'data','local','scene','development','development_manifest.json')));
out=fullfile(root,'results','scene_development'); if ~isfolder(out),mkdir(out);end
features=table(); quality=table();
assert(numel(manifest.cases)==9);
for k=1:numel(manifest.cases)
    c=manifest.cases(k); [x,fs]=audioread(fullfile(root,c.wav));
    [row,q]=scene_features(x,fs);
    row=addvars(row,string(c.case_id),string(c.label),double(c.development_fold), ...
        string(c.source_sha256),string(c.wav_sha256), ...
        'Before',1,'NewVariableNames',{'CaseID','Label','Fold','SourceSHA256','WavSHA256'});
    features=[features;row]; %#ok<AGROW>
    info=table(string(c.case_id),q.durationSeconds,q.peak,q.fullScaleSamples,q.silent, ...
        'VariableNames',{'CaseID','DurationSeconds','Peak','FullScaleSamples','Silent'});
    quality=[quality;info]; %#ok<AGROW>
end
assert(numel(unique(features.SourceSHA256))==height(features));
assert(numel(unique(features.WavSHA256))==height(features));
writetable(features,fullfile(out,'features.csv'));
writetable(quality,fullfile(out,'quality.csv'));
fprintf('Extracted %d full-recording feature rows.\n',height(features));
end
