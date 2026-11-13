function result = classify_scene_advanced(file, route)
%CLASSIFY_SCENE_ADVANCED MATLAB features -> locally trained Python classifier.
if nargin<2,route="rich_fusion_multiscale";end
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
runtimePath=fullfile(root,'data','local','scene','advanced','runtime.json');
assert(isfile(runtimePath),'Run scene_advanced.py develop before advanced inference.');
runtime=jsondecode(fileread(runtimePath));
[audio,fs]=audioread(file);if size(audio,2)>1,audio=mean(audio,2);end
timer=tic;
[~,quality]=scene_features(audio,fs);
assert(~quality.silent && quality.peak>=1e-5,'Recording is silent or nearly silent.');
rows=scene_multiscale_features(audio,fs);
folder=fullfile(root,'tmp');if ~isfolder(folder),mkdir(folder);end
stem=tempname(folder);query=[stem '.csv'];output=[stem '.json'];log=[stem '.log'];
cleanup=onCleanup(@()removeTemps({query,output,log}));
writetable(rows,query);
values={runtime.python,fullfile(root,'code','scene','scene_advanced.py'), ...
    'infer','--query',query,'--output',output,'--route',char(route)};
args=java.util.ArrayList();
for k=1:numel(values),args.add(java.lang.String(values{k}));end
builder=java.lang.ProcessBuilder(args);
environment=builder.environment();environment.put('PYTHONPATH',runtime.pythonpath);
builder.redirectErrorStream(true);builder.redirectOutput(java.io.File(log));
process=builder.start();status=process.waitFor();
assert(status==0,'Advanced classifier failed: %s',fileread(log));
result=jsondecode(fileread(output));result.label=string(result.label);
result.analysisSeconds=toc(timer);result.quality=quality;
result.features=rows(rows.Mode=="full",4:end);
switch result.label
    case "speech"
        result.suggestion="Speech: preserve useful speech; assess background noise before enhancement.";
    case "alarm"
        result.suggestion="Alarm: retain warning audio unless the application explicitly requests suppression.";
    otherwise
        result.suggestion="Plastic bottle pressing: transient event; inspect suppression alongside speech preservation.";
end
if result.needs_review
    result.suggestion=result.suggestion+" Window/model votes disagree; review this recording.";
end
end

function removeTemps(files)
for k=1:numel(files),if isfile(files{k}),delete(files{k});end,end
end
