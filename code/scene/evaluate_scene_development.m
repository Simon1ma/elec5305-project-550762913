function summary = evaluate_scene_development()
%EVALUATE_SCENE_DEVELOPMENT Recording-held-out exploratory development checks.
% No windows from a held-out source enter fitting or feature standardisation.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
out=fullfile(root,'results','scene_development');
features=readtable(fullfile(out,'features.csv'),'TextType','string');
allNames=features.Properties.VariableNames(6:end);
relativeNames=setdiff(allNames,{'RMS_dBFS'},'stable');
classes=sort(unique(features.Label)); assert(numel(classes)==3);
methods=["centroid","centroid","nearest","nearest"];
sets=["relative","all","relative","all"];
summary=table(); predictions=table();
fig=figure('Visible','off','Position',[60 60 1200 950],'Color','white');
cleanup=onCleanup(@()close(fig)); layout=tiledlayout(fig,2,2,'TileSpacing','compact','Padding','loose');
for config=1:4
    if sets(config)=="relative", names=relativeNames; else, names=allNames; end
    predicted=strings(height(features),1); separation=zeros(height(features),1);
    for fold=1:3
        held=features.Fold==fold; fit=~held;
        assert(sum(held)==3 && sum(fit)==6);
        assert(isempty(intersect(features.SourceSHA256(fit),features.SourceSHA256(held))));
        assert(isempty(intersect(features.WavSHA256(fit),features.WavSHA256(held))));
        model=scene_fit_classifier(features(fit,:),features.Label(fit),names,methods(config));
        [predicted(held),~,separation(held)]=scene_predict_features(model,features(held,:));
    end
    matrix=zeros(3);
    for i=1:3
        for j=1:3
            matrix(i,j)=sum(features.Label==classes(i)&predicted==classes(j));
        end
    end
    precision=diag(matrix)./max(sum(matrix,1).',1);
    recall=diag(matrix)./max(sum(matrix,2),1);
    f1=2*diag(matrix)./max(sum(matrix,1).'+sum(matrix,2),1);
    correct=sum(features.Label==predicted); accuracy=correct/height(features);
    name=methods(config)+"_"+sets(config);
    row=table(name,numel(names),height(features),correct,accuracy,mean(f1), ...
        'VariableNames',{'Configuration','FeatureCount','Recordings','Correct','Accuracy','MacroF1'});
    summary=[summary;row]; %#ok<AGROW>
    rows=table(repmat(name,height(features),1),features.CaseID,features.Fold, ...
        features.Label,predicted,separation,features.Label==predicted, ...
        'VariableNames',{'Configuration','CaseID','Fold','TrueLabel','Prediction','DistanceSeparation','Correct'});
    predictions=[predictions;rows]; %#ok<AGROW>
    perClass=table(classes,sum(matrix,2),precision,recall,f1, ...
        'VariableNames',{'Class','Recordings','Precision','Recall','F1'});
    writetable(perClass,fullfile(out,name+"_per_class.csv"));
    writetable(array2table(matrix,'VariableNames',cellstr(classes),'RowNames',cellstr(classes)), ...
        fullfile(out,name+"_confusion.csv"),'WriteRowNames',true);
    ax=nexttile(layout); imagesc(ax,matrix); clim(ax,[0 3]);
    xticks(ax,1:3); yticks(ax,1:3); xticklabels(ax,replace(classes,'_',' '));
    yticklabels(ax,replace(classes,'_',' ')); xlabel(ax,'Predicted'); ylabel(ax,'Supplied label');
    title(ax,sprintf('%s | %d/9 | macro-F1 %.3f',name,correct,mean(f1)),'Interpreter','none');
    for i=1:3
        for j=1:3
            if matrix(i,j)>=2, ink='black';else,ink='white';end
            text(ax,j,i,string(matrix(i,j)),'HorizontalAlignment','center','Color',ink,'FontWeight','bold','FontSize',15);
        end
    end
end
title(layout,'Development-only recording-level 3-fold CV | 6 fit + 3 held-out per fold');
exportgraphics(fig,fullfile(out,'development_confusions.png'),'Resolution',140);
writetable(summary,fullfile(out,'development_summary.csv'));
writetable(predictions,fullfile(out,'development_predictions.csv'));
% Primary prototype chosen before inspecting these scores; other rows are comparisons.
model=scene_fit_classifier(features,features.Label,relativeNames,"centroid");
model.role="Development prototype; independent evaluation pending";
model.trainingCaseIDs=features.CaseID; model.trainingSourceSHA256=features.SourceSHA256;
local=fullfile(root,'data','local','scene','development');
save(fullfile(local,'scene_model.mat'),'model');
disp(summary);
fprintf('Saved fixed nearest-centroid prototype without absolute RMS. Independent test remains pending.\n');
end
