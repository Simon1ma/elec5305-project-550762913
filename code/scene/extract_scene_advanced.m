function rows = extract_scene_advanced()
%EXTRACT_SCENE_ADVANCED Source-grouped multi-scale features and controlled probes.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
manifest=jsondecode(fileread(fullfile(root,'data','local','scene','development','development_manifest.json')));
out=fullfile(root,'results','scene_advanced');if ~isfolder(out),mkdir(out);end
rows=table();
for k=1:numel(manifest.cases)
    c=manifest.cases(k);[x,fs]=audioread(fullfile(root,c.wav));
    rng(5305+k,'twister');noise=randn(size(x));
    noise=noise*sqrt(sum(x.^2)/(100*sum(noise.^2)));
    signals={x,.5*x,x+noise};conditions=["clean","gain_minus6","white20"];
    for condition=1:numel(conditions)
        patches=scene_multiscale_features(signals{condition},fs);n=height(patches);
        patches=addvars(patches,repmat(string(c.case_id),n,1),repmat(string(c.label),n,1), ...
            repmat(double(c.development_fold),n,1),repmat(string(c.source_sha256),n,1), ...
            repmat(conditions(condition),n,1),'Before',1, ...
            'NewVariableNames',{'CaseID','Label','Fold','SourceSHA256','Condition'});
        rows=[rows;patches]; %#ok<AGROW>
    end
    fprintf('Advanced features %d/%d: %s\n',k,numel(manifest.cases),c.case_id);
end
writetable(rows,fullfile(out,'multiscale_features.csv'));
fprintf('Saved %d feature rows from 9 source recordings and 3 controlled conditions.\n',height(rows));
end
