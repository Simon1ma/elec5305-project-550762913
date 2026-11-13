function [app,controls] = launch_scene_demo(visibility,initialMethod)
%LAUNCH_SCENE_DEMO Import, audition and analyse a recording using acoustic features.
if nargin<1,visibility='on';end
if nargin<2,initialMethod='auto';end
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
manifest=jsondecode(fileread(fullfile(root,'data','local','scene','development','development_manifest.json')));
catalog=struct('case_id',{manifest.cases.case_id},'wav',{manifest.cases.wav});
testPath=fullfile(root,'data','local','scene','holdout','holdout_manifest.json');
if isfile(testPath)
    test=jsondecode(fileread(testPath));
    catalog=[catalog,struct('case_id',{test.cases.case_id},'wav',{test.cases.wav})];
end
app=uifigure('Name','ELEC5305 | Acoustic Scene Analysis','Position',[80 50 1220 950],'Visible',visibility);
g=uigridlayout(app,[10 4]);
g.RowHeight={35,32,35,36,25,130,155,'1x',45,32};
g.ColumnWidth={150,'1x',170,150};
heading=uilabel(g,'Text','Acoustic scene analysis | plastic bottle, alarm and speech', ...
    'FontSize',21,'FontWeight','bold');heading.Layout.Row=1;heading.Layout.Column=[1 4];
methodLabel=uilabel(g,'Text','Analysis method:');methodLabel.Layout.Row=2;methodLabel.Layout.Column=1;
methodNames={'Baseline: 12-feature centroid','MFCC: centroid','MFCC: linear SVM', ...
    'MFCC: RBF SVM','MFCC: extra-randomised trees','Dual-scale RBF SVM', ...
    'Dual-scale SVM + tree fusion','Dual-scale SVM + noise augmentation'};
methodIDs={'baseline','rich_centroid_full','rich_linear_svm_full','rich_rbf_svm_full', ...
    'rich_extratrees_full','rich_rbf_multiscale','rich_fusion_multiscale','rich_rbf_augmented'};
method=uidropdown(g,'Items',methodNames,'ItemsData',methodIDs,'Value','baseline');
method.Layout.Row=2;method.Layout.Column=[2 4];
if isfile(fullfile(root,'data','local','scene','advanced','runtime.json'))
    method.Value='rich_fusion_multiscale';
end
if string(initialMethod)=="baseline",method.Value='baseline';end
method.ValueChangedFcn=@changeMethod;
openButton=uibutton(g,'Text','Import recording','ButtonPushedFcn',@importFile);
openButton.Layout.Row=3;openButton.Layout.Column=1;
cases=catalog;
selector=uidropdown(g,'Items',cellstr(string({cases.case_id})),'ValueChangedFcn',@selectCase);
selector.Layout.Row=3;selector.Layout.Column=2;
playButton=uibutton(g,'Text','Play original','ButtonPushedFcn',@playAudio);
playButton.Layout.Row=3;playButton.Layout.Column=3;
stopButton=uibutton(g,'Text','Stop','ButtonPushedFcn',@(~,~)stopAudio());
stopButton.Layout.Row=3;stopButton.Layout.Column=4;
resultLabel=uilabel(g,'Text','Ready','FontSize',17,'FontWeight','bold');
resultLabel.Layout.Row=4;resultLabel.Layout.Column=[1 4];
scope=uilabel(g,'Text','9 development recordings | Whole-recording / temporal analysis | Independent test pending');
if isfile(fullfile(root,'results','scene_holdout','test_audit.json'))
    scope.Text='01-03: development | 04-06: new-recording test | Fixed models trained on 01-03 only';
end
scope.Layout.Row=5;scope.Layout.Column=[1 4];
wave=uiaxes(g);wave.Layout.Row=6;wave.Layout.Column=[1 4];
spectrum=uiaxes(g);spectrum.Layout.Row=7;spectrum.Layout.Column=[1 4];
tabs=uitabgroup(g);tabs.Layout.Row=8;tabs.Layout.Column=[1 4];
featureTab=uitab(tabs,'Title','Acoustic / MFCC features');fg=uigridlayout(featureTab,[1 1]);
featureTable=uitable(fg,'ColumnName',{'Acoustic feature','Value'});
voteTab=uitab(tabs,'Title','Temporal model decisions');vg=uigridlayout(voteTab,[1 1]);
voteTable=uitable(vg);
advice=uilabel(g,'Text','','WordWrap','on','FontSize',14);
advice.Layout.Row=9;advice.Layout.Column=[1 4];
bridgeButton=uibutton(g,'Text','Open personal speech-enhancement experiment','ButtonPushedFcn',@openBridge);
bridgeButton.Layout.Row=10;bridgeButton.Layout.Column=[1 4];
player=[];current=[];app.CloseRequestFcn=@closeApp;
controls=struct('selector',selector,'result',resultLabel,'load',@loadFile,'method',method,'tabs',tabs,'voteTab',voteTab);
loadFile(fullfile(root,cases(1).wav));
    function importFile(~,~)
        [name,folder]=uigetfile({'*.wav;*.m4a;*.flac','Audio recordings'},'Choose a recording');
        if isequal(name,0),return;end
        try,loadFile(fullfile(folder,name));catch err,uialert(app,err.message,'Cannot analyse recording');end
    end
    function selectCase(~,~)
        chosen=cases(string({cases.case_id})==string(selector.Value));
        if isempty(chosen),return;end
        loadFile(fullfile(root,chosen.wav));
    end
    function changeMethod(~,~)
        if ~isempty(current),loadFile(current.file);end
    end
    function openBridge(~,~)
        stopAudio();addpath(fullfile(root,'code','final'));
        launch_final_demo('personal');
    end
    function loadFile(file)
        stopAudio();resultLabel.Text='Analysing recording...';drawnow;
        if string(method.Value)=="baseline",result=classify_scene_file(file);
        else,result=classify_scene_advanced(file,string(method.Value));end
        [x,fs]=audioread(file);if size(x,2)>1,x=mean(x,2);end
        current=struct('audio',x,'fs',fs,'file',file);
        selected=find(arrayfun(@(c)strcmp(fullfile(root,c.wav),file),cases),1);
        selector.Items=cellstr(string({cases.case_id}));
        if isempty(selected)
            selector.Items=[selector.Items,{'Imported recording'}];selector.Value='Imported recording';
        else
            selector.Value=char(cases(selected).case_id);
        end
        [~,name,ext]=fileparts(file);
        resultLabel.Text=sprintf('%s | Best match: %s | Analysis %.3f s', ...
            [name ext],replace(result.label,'_',' '),result.analysisSeconds);
        step=max(1,floor(numel(x)/20000));idx=1:step:numel(x);
        plot(wave,(idx-1)/fs,x(idx),'Color',[.09 .42 .53]);
        xlim(wave,[0 numel(x)/fs]);ylim(wave,[-1 1]);
        xlabel(wave,'Time (s)');ylabel(wave,'Amplitude');title(wave,'Original recording');
        [p,q]=rat(16000/fs);y=resample(x,p,q);win=hann(400,'periodic');
        [S,f,t]=spectrogram(y,win,240,512,16000);
        imagesc(spectrum,t,f/1000,20*log10(max(abs(S)/sum(win),1e-6)));
        axis(spectrum,'xy');clim(spectrum,[-100 -10]);ylim(spectrum,[0 8]);
        xlim(spectrum,[0 numel(x)/fs]);
        xlabel(spectrum,'Time (s)');ylabel(spectrum,'Frequency (kHz)');
        title(spectrum,'25 ms / 10 ms spectrogram');
        featureTable.Data=table(string(result.features.Properties.VariableNames).',result.features{1,:}.', ...
            'VariableNames',{'Feature','Value'});
        if isfield(result,'timeline'),voteTable.Data=struct2table(result.timeline);
        else,voteTable.Data=table();end
        advice.Text=result.suggestion;drawnow;
    end
    function playAudio(~,~)
        stopAudio();player=audioplayer(current.audio,current.fs);play(player);
    end
    function stopAudio()
        if ~isempty(player),stop(player);end
    end
    function closeApp(~,~)
        stopAudio();delete(app);
    end
end
