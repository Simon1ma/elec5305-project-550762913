function [labels, distances, separation] = scene_predict_features(model, features)
%SCENE_PREDICT_FEATURES Distances are geometric scores, not probabilities.
X=features{:,model.featureNames};
assert(all(isfinite(X),'all'));
Z=(X-model.mean)./model.scale;
distances=inf(size(Z,1),numel(model.classes));
for k=1:numel(model.classes)
    points=model.points(model.pointLabels==model.classes(k),:);
    for n=1:size(Z,1)
        distances(n,k)=min(sqrt(sum((points-Z(n,:)).^2,2)));
    end
end
[~,index]=min(distances,[],2); labels=model.classes(index);
ordered=sort(distances,2);
separation=(ordered(:,2)-ordered(:,1))./max(ordered(:,2),eps);
end
