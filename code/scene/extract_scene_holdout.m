function rows = extract_scene_holdout()
%EXTRACT_SCENE_HOLDOUT Apply the frozen feature recipe to new recordings.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
manifest=jsondecode(fileread(fullfile(root,'data','local','scene','holdout','holdout_manifest.json')));
out=fullfile(root,'results','scene_holdout');if ~isfolder(out),mkdir(out);end
rows=table();
for k=1:numel(manifest.cases)
    c=manifest.cases(k);[x,fs]=audioread(fullfile(root,c.wav));
    rng(6305+k,'twister');noise=randn(size(x));
    noise=noise*sqrt(sum(x.^2)/(100*sum(noise.^2)));
    signals={x,.5*x,x+noise};conditions=["clean","gain_minus6","white20"];
    for condition=1:numel(conditions)
        patches=scene_multiscale_features(signals{condition},fs);n=height(patches);
        patches=addvars(patches,repmat(string(c.case_id),n,1),repmat(string(c.label),n,1), ...
            repmat(string(c.source_sha256),n,1),repmat(conditions(condition),n,1),'Before',1, ...
            'NewVariableNames',{'CaseID','Label','SourceSHA256','Condition'});
        rows=[rows;patches]; %#ok<AGROW>
    end
    fprintf('Holdout features %d/%d: %s\n',k,numel(manifest.cases),c.case_id);
end
writetable(rows,fullfile(out,'multiscale_features.csv'));
fprintf('Saved %d rows from nine new sources; no fitting performed.\n',height(rows));
end
