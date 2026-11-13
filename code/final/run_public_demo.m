function result = run_public_demo(showUI)
% Rerun original causal Wiener methods on the bundled public evaluation case.
if nargin<1,showUI=true;end
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));addpath(fullfile(root,'code','latency'));
d=load(fullfile(root,'data','demo_public','case.mat'));fs=double(d.fs);P=double(d.prefixSamples);N=double(d.speechSamples);windows=double(d.windows(:).');
x=double(d.input);clean=double(d.clean);noisy=x(P+(1:N));outputs=zeros(N,4);errors=zeros(1,4);
for k=1:4
 y=run_causal_stream(x,latency_config(windows(k)));outputs(:,k)=y(P+(1:N));
 errors(k)=max(abs(outputs(:,k)-d.expectedWiener(:,k)));assert(errors(k)<1e-10,'Processor disagrees with evaluated output.');
end
allAudio=[clean noisy outputs d.reference];gain=.95/max(1,max(abs(allAudio),[],'all'));
result=struct('maximumBaselineError',max(errors),'fs',fs,'noisySNR',score(noisy),'wienerSNR',arrayfun(@(k)score(outputs(:,k)),1:4),'referenceSNR',score(d.reference));
fprintf('PASS: four original Wiener outputs reproduced; maximum error %.3g.\n',max(errors));
if ~showUI,return;end
manifest=jsondecode(fileread(fullfile(root,'data','demo_public','manifest.json')));
f=figure('Name','ELEC5305 | Public example: actual Wiener rerun','NumberTitle','off','Position',[80 70 1150 760]);
ax1=axes('Parent',f,'Position',[.08 .58 .86 .31]);ax2=axes('Parent',f,'Position',[.08 .16 .86 .31]);
labels={'Noisy','Wiener10','Wiener20','Wiener40','Wiener80','DeepFilterNet3 (saved reference)'};
selector=uicontrol(f,'Style','popupmenu','String',labels,'Value',4,'Units','normalized','Position',[.08 .94 .34 .04],'Callback',@update);
status=uicontrol(f,'Style','text','Units','normalized','Position',[.44 .93 .5 .05],'HorizontalAlignment','left');
uicontrol(f,'Style','text','Units','normalized','Position',[.08 .02 .86 .05],'String','Bundled public case | clean/noisy/output share one gain | DFNet3 is saved output; Wiener methods are rerun');
uicontrol(f,'Style','pushbutton','String','Play clean','Units','normalized','Position',[.08 .09 .17 .045],'Callback',@(~,~)playClip(clean));
uicontrol(f,'Style','pushbutton','String','Play noisy','Units','normalized','Position',[.28 .09 .17 .045],'Callback',@(~,~)playClip(noisy));
uicontrol(f,'Style','pushbutton','String','Play output','Units','normalized','Position',[.48 .09 .17 .045],'Callback',@(~,~)playClip(current));
uicontrol(f,'Style','pushbutton','String','Stop','Units','normalized','Position',[.68 .09 .17 .045],'Callback',@(~,~)stopClip());
player=[];current=[];f.CloseRequestFcn=@closeApp;update([],[]);
 function v=score(y),v=10*log10(sum(clean.^2)/sum((y-clean).^2));end
 function update(~,~)
  stopClip();idx=selector.Value;
  if idx==1,current=noisy;method='Noisy';ready=0;
  elseif idx==6,current=d.reference;method='DeepFilterNet3';ready=40;
  else,current=outputs(:,idx-1);method=sprintf('Wiener%d',windows(idx-1));ready=windows(idx-1);end
  scores=manifest.scores;row=scores(string({scores.Method})==string(method));
  status.String=sprintf('Ready %d ms | SNR %.2f dB | Saved STOI %.4f',ready,score(current),str2double(row.STOI));
  t=(0:N-1)/fs;plot(ax1,t,clean,'Color',[.65 .65 .65]);hold(ax1,'on');plot(ax1,t,current,'Color',[.05 .43 .55]);hold(ax1,'off');xlim(ax1,[0 N/fs]);xlabel(ax1,'Time (s)');ylabel(ax1,'Amplitude');title(ax1,labels{idx});legend(ax1,{'Clean','Selected output'});
  [S,ff,tt]=spectrogram(current,hann(960,'periodic'),720,1024,fs);imagesc(ax2,tt,ff/1000,20*log10(max(abs(S),1e-8)));axis(ax2,'xy');ylim(ax2,[0 8]);xlabel(ax2,'Time (s)');ylabel(ax2,'Frequency (kHz)');drawnow;
 end
 function playClip(y),stopClip();player=audioplayer(y*gain,fs);play(player);end
 function stopClip(),if ~isempty(player),stop(player);end,end
 function closeApp(~,~),stopClip();delete(f);end
end
