function features = analyse_scene_pilot()
%ANALYSE_SCENE_PILOT Describe the three complete pilot recordings.
% Class names come from the supplied labels; they are not model predictions.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
manifest=jsondecode(fileread(fullfile(root,'data','local','scene','pilot','pilot_manifest.json')));
out=fullfile(root,'results','scene_pilot');
if ~isfolder(out),mkdir(out);end
features=table(); qualityRows=table();
fig=figure('Visible','off','Position',[50 50 1500 1000],'Color','white');
cleanup=onCleanup(@()close(fig));
layout=tiledlayout(fig,3,2,'TileSpacing','compact','Padding','compact');
names=["Plastic bottle pressing","Alarm","Spoken reading"];
for k=1:numel(manifest.cases)
    if iscell(manifest.cases),item=manifest.cases{k};else,item=manifest.cases(k);end
    [x,fs]=audioread(fullfile(root,item.wav));
    [row,q]=scene_features(x,fs);
    row=addvars(row,string(item.case_id),string(item.label), ...
        'Before',1,'NewVariableNames',{'CaseID','SuppliedLabel'});
    features=[features;row]; %#ok<AGROW>
    info=table(string(item.case_id),q.durationSeconds,q.peak,q.fullScaleSamples,q.silent, ...
        'VariableNames',{'CaseID','DurationSeconds','Peak','FullScaleSamples','Silent'});
    qualityRows=[qualityRows;info]; %#ok<AGROW>
    ax=nexttile(layout);
    stride=max(1,floor(numel(x)/30000)); idx=1:stride:numel(x);
    plot(ax,(idx-1)/fs,x(idx),'Color',[.09 .42 .53]);
    xlim(ax,[0 numel(x)/fs]); ylim(ax,[-1 1]);
    title(ax,names(k)+" | waveform"); xlabel(ax,'Time (s)'); ylabel(ax,'Amplitude');
    ax=nexttile(layout);
    [p,r]=rat(16000/fs); y=resample(x,p,r); win=hann(400,'periodic');
    [S,f,t]=spectrogram(y,win,240,512,16000);
    db=20*log10(max(abs(S)/sum(win),1e-6));
    imagesc(ax,t,f/1000,db); axis(ax,'xy'); clim(ax,[-100 -10]);
    ylim(ax,[0 8]); xlim(ax,[0 numel(x)/fs]);
    xlabel(ax,'Time (s)'); ylabel(ax,'Frequency (kHz)');
    title(ax,names(k)+" | spectrogram"); colorbar(ax);
end
title(layout,'User-provided pilot recordings | supplied labels | common display scales');
exportgraphics(fig,fullfile(out,'pilot_waveforms_spectrograms.png'),'Resolution',150);
writetable(features,fullfile(out,'features.csv'));
writetable(qualityRows,fullfile(out,'quality.csv'));
disp(features(:,{'SuppliedLabel','RMS_dBFS','RMS_CV','Centroid_Hz','Flatness','PositiveFlux'}));
fprintf('Pilot feature extraction complete: three source recordings, no classifier accuracy estimate.\n');
end
