function model = scene_fit_classifier(features, labels, featureNames, method)
%SCENE_FIT_CLASSIFIER Standardise using training rows only; fit simple baselines.
arguments
    features table
    labels string
    featureNames
    method (1,1) string {mustBeMember(method,["centroid","nearest"])}
end
X=features{:,featureNames}; labels=labels(:);
assert(size(X,1)==numel(labels) && all(isfinite(X),'all'));
model.method=method; model.featureNames=featureNames;
model.mean=mean(X,1); model.scale=std(X,1,1);
model.scale(model.scale<1e-12)=1;
Z=(X-model.mean)./model.scale;
model.classes=sort(unique(labels)); model.trainingLabels=labels;
assert(numel(model.classes)==3,'All three classes must occur in training.');
if method=="centroid"
    model.points=zeros(numel(model.classes),size(Z,2));
    for k=1:numel(model.classes)
        model.points(k,:)=mean(Z(labels==model.classes(k),:),1);
    end
    model.pointLabels=model.classes;
else
    model.points=Z; model.pointLabels=labels;
end
end
