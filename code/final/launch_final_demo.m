function [app,controls] = launch_final_demo(cohort)
%LAUNCH_FINAL_DEMO Re-run evaluated causal processors and audition results.
% This is a recorded-file demonstration, not live microphone latency testing.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root,'code','latency'));
if nargin<1
    if isfile(fullfile(root,'results','final_external','metrics.csv')),cohort="external";
    else,cohort="voicebank";end
end
if string(cohort)=="external",suffix='final_external';label='LibriSpeech test-clean; 16 kHz speech upsampled to 48 kHz';
else,suffix='final';label='VCTK-derived engineering cohort; upstream training overlap risk';end
manifest=jsondecode(fileread(fullfile(root,'results',suffix,'input_manifest.json')));
cases=manifest.cases;firstSpeech=string(cases(1).speech_id);
cases=cases(string({cases.speech_id})==firstSpeech);
noiseNames=string({cases.noise_class})+"_"+string({cases.noise_source});
items=unique(noiseNames,'stable');
metrics=readtable(fullfile(root,'results',suffix,'metrics.csv'),'TextType','string');
app=uifigure('Name','ELEC5305 | Causal Latency-Quality Demonstration','Position',[70 60 1200 760]);
g=uigridlayout(app,[7 6]);g.RowHeight={38,28,36,36,'1x','1x',40};g.ColumnWidth={125,195,110,135,'1x',170};
heading=uilabel(g,'Text','Causal speech enhancement: latency and quality','FontSize',22,'FontWeight','bold');heading.Layout.Row=1;heading.Layout.Column=[1 6];
scope=uilabel(g,'Text',label);scope.Layout.Row=2;scope.Layout.Column=[1 6];
uilabel(g,'Text','Recorded noise:');
noiseBox=uidropdown(g,'Items',cellstr(items),'Value',char(items(1)));
uilabel(g,'Text','Input SNR (dB):');
snrBox=uidropdown(g,'Items',{'0','5','10'},'Value','0');
methodBox=uidropdown(g,'Items',{'Noisy','Wiener10','Wiener20','Wiener40','Wiener80','DeepFilterNet3'},'Value','Wiener40');
runButton=uibutton(g,'Text','Run processor','ButtonPushedFcn',@update);
uibutton(g,'Text','Play clean','ButtonPushedFcn',@(~,~)playClip('clean'));
uibutton(g,'Text','Play noisy','ButtonPushedFcn',@(~,~)playClip('noisy'));
uibutton(g,'Text','Play processed','ButtonPushedFcn',@(~,~)playClip('processed'));
uibutton(g,'Text','Stop audio','ButtonPushedFcn',@(~,~)stopAudio());
status=uilabel(g,'Text','Ready','FontWeight','bold');status.Layout.Row=4;status.Layout.Column=[5 6];
ax1=uiaxes(g);ax1.Layout.Row=5;ax1.Layout.Column=[1 6];
ax2=uiaxes(g);ax2.Layout.Row=6;ax2.Layout.Column=[1 6];
note=uilabel(g,'Text','Recorded-file simulation | Ready delay excludes compute/device delay | Separate 300 ms calibration | Common audio gain');
note.Layout.Row=7;note.Layout.Column=[1 6];
current=[];player=[];controls=struct('method',methodBox,'noise',noiseBox,'snr',snrBox,'run',runButton);
update([],[]);
    function update(~,~)
        stopAudio();
        selected=cases(noiseNames==string(noiseBox.Value) & [cases.input_snr_db]==str2double(snrBox.Value));
        assert(isscalar(selected));
        data=load(fullfile(root,selected.input_mat));x=double(data.input);fs=double(data.fs);
        P=double(data.prefixSamples);N=double(data.speechSamples);idx=P+(1:N);
        saved=load(fullfile(root,'data','local',suffix,'wiener',string(selected.case_id)+".mat"));
        referencePath=fullfile(root,'data','local',suffix,'reference',string(selected.case_id)+".wav");
        rawReference=audioread(referencePath);reference=rawReference(1440+idx);
        method=string(methodBox.Value);
        if method=="Noisy"
            y=x(idx);ready=0;expected=saved.noisy;
        elseif startsWith(method,"Wiener")
            window=str2double(extractAfter(method,'Wiener'));
            [full,info]=run_causal_stream(x,latency_config(window));y=full(idx);ready=info.oldestSampleReadyDelayMs;
            expected=saved.outputs(:,[10 20 40 80]==window);
        else
            destination=fullfile(root,'data','local',suffix,'demo_runtime');if ~isfolder(destination),mkdir(destination);end
            executable=fullfile(root,'data','local','latency2','deep-filter.exe');model=fullfile(root,'data','local','latency2','DeepFilterNet3_onnx.tar.gz');
            command=sprintf('"%s" --model "%s" --output-dir "%s" "%s"',executable,model,destination,fullfile(root,selected.input_wav));
            [exitCode,message]=system(command);assert(exitCode==0,'%s',message);
            generated=audioread(fullfile(destination,string(selected.case_id)+".wav"));y=generated(1440+idx);ready=40;expected=reference;
        end
        assert(max(abs(y-expected))<1e-10,'Demonstration output differs from evaluated output.');
        clean=data.clean;noisy=x(idx);allAudio=[clean noisy saved.outputs reference];gain=.95/max(1,max(abs(allAudio),[],'all'));
        current=struct('clean',clean*gain,'noisy',noisy*gain,'processed',y*gain,'fs',fs);
        SNR=10*log10(sum(clean.^2)/sum((y-clean).^2));
        metric=metrics(metrics.CaseID==string(selected.case_id) & metrics.Method==method,:);
        status.Text=sprintf('Ready %.0f ms | SNR %.2f dB | STOI %.4f',ready,SNR,metric.STOI);
        t=(0:N-1).'/fs;plot(ax1,t,clean,'Color',[.6 .6 .6]);hold(ax1,'on');plot(ax1,t,y,'Color',[.04 .43 .55]);hold(ax1,'off');
        xlabel(ax1,'Time in scored speech (s)');ylabel(ax1,'Amplitude');xlim(ax1,[0 4.5]);legend(ax1,{'Clean','Processed'});
        title(ax1,sprintf('%s | %s | %s dB | %s',method,noiseBox.Value,snrBox.Value,firstSpeech),'Interpreter','none');
        [S,f,tSpec]=spectrogram(y,hann(960,'periodic'),720,1024,fs);cleanSpec=spectrogram(clean,hann(960,'periodic'),720,1024,fs);
        peak=max(abs(cleanSpec),[],'all');imagesc(ax2,tSpec,f/1000,20*log10(max(abs(S),peak*1e-6)));axis(ax2,'xy');clim(ax2,20*log10(peak)+[-70 0]);
        xlim(ax2,[0 4.5]);ylim(ax2,[0 8]);xlabel(ax2,'Time in scored speech (s)');ylabel(ax2,'Frequency (kHz)');title(ax2,'Common-grid output spectrogram (0-8 kHz view)');colorbar(ax2);drawnow;
    end
    function playClip(which)
        stopAudio();player=audioplayer(current.(which),current.fs);play(player);
    end
    function stopAudio()
        if ~isempty(player),stop(player);end
    end
end
