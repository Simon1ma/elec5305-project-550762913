function result = classify_scene_file(file, modelPath)
%CLASSIFY_SCENE_FILE Classify one complete recording with the development model.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
if nargin<2
    modelPath=fullfile(root,'data','local','scene','development','scene_model.mat');
end
assert(isfile(modelPath),'Run extract_scene_development and evaluate_scene_development first.');
loaded=load(modelPath,'model'); model=loaded.model;
[audio,fs]=audioread(file); if size(audio,2)>1,audio=mean(audio,2);end
timer=tic; [features,quality]=scene_features(audio,fs);
assert(~quality.silent && quality.peak>=1e-5,'Recording is silent or nearly silent.');
[label,distances,separation]=scene_predict_features(model,features);
result=struct('label',label,'distances',distances,'distanceClasses',model.classes, ...
    'distanceSeparation',separation,'features',features,'quality',quality, ...
    'analysisSeconds',toc(timer),'modelRole',model.role);
switch label
    case "speech"
        result.suggestion="Speech: preserve useful speech; assess background noise before enhancement.";
    case "alarm"
        result.suggestion="Alarm: retain warning audio unless the application explicitly requests suppression.";
    otherwise
        result.suggestion="Plastic bottle pressing: transient event; inspect suppression alongside speech preservation.";
end
end
