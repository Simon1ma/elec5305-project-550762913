function manifest = record_scene_session(sessionID, split, profile)
%RECORD_SCENE_SESSION Manually record nine scene clips in one session.
% Example: record_scene_session('session01','train')
% This function starts the microphone only after an explicit Record choice.
arguments
    sessionID (1,1) string
    split (1,1) string {mustBeMember(split,["train","validation","test"])}
    profile (1,1) string {mustBeMember(profile,["steady_keyboard_mixed","can_alarm_speech","bottle_alarm_speech"])} = "bottle_alarm_speech"
end
assert(~isempty(regexp(char(sessionID),'^[A-Za-z0-9_-]+$','once')), ...
    'Use letters, digits, underscores and hyphens in the session name.');
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
local=fullfile(root,'data','local','scene');
folder=fullfile(local,'recordings',sessionID);
if ~isfolder(folder),mkdir(folder);end
manifestPath=fullfile(local,'recording_manifest.csv');
if isfile(manifestPath)
    manifest=readtable(manifestPath,'TextType','string');
    prior=manifest(manifest.Session==sessionID,:);
    assert(isempty(prior)||all(prior.Split==split),'A session must belong to one split.');
else
    manifest=table('Size',[0 11], ...
        'VariableTypes',{'string','string','string','string','double','double','double','double','double','double','string'}, ...
        'VariableNames',{'File','Label','Session','Split','Take','SampleRate', ...
        'DurationSeconds','RMS_dBFS','Peak','FullScaleSamples','CapturedUTC'});
end
if profile=="can_alarm_speech"||profile=="bottle_alarm_speech"
    labels=["container_press","alarm","speech"];
    instructions=[ ...
        "Press a plastic bottle intermittently with natural pauses. No speech or other playback.", ...
        "Record an alarm from another device. No speech or unrelated playback.", ...
        "Read a short passage naturally. No alarm or bottle sounds. Chinese or English is suitable."];
else
    labels=["steady","keyboard","mixed"];
    instructions=[ ...
        "Run a fan or similar steady mechanical source. Do not speak or type.", ...
        "Type naturally with pauses. Turn off the fan when possible. Do not speak.", ...
        "Run the same mechanical source and type naturally. Do not speak."];
end
fs=48000; seconds=8;
notesPath=fullfile(folder,'session_notes.json');
if ~isfile(notesPath)
    notes=inputdlg({'Microphone / input device:','Sound source(s) / alarm / reading passage:', ...
        'Room, source distance and microphone placement:','Microphone gain setting:'}, ...
        'Recording session conditions',[1 80],{'','','',''});
    if isempty(notes),return;end
    metadata=struct('session',sessionID,'split',split,'device',string(notes{1}), ...
        'sources',string(notes{2}),'profile',profile,'placement',string(notes{3}),'gain',string(notes{4}));
    fid=fopen(notesPath,'w'); assert(fid>=0,'Cannot write session notes.');
    closer=onCleanup(@()fclose(fid));
    fprintf(fid,'%s\n',jsonencode(metadata,PrettyPrint=true)); clear closer
end
recorder=audiorecorder(fs,16,1);
fprintf('Nine 8-second scene recordings. Keep microphone gain fixed.\n');
for k=1:3
    for take=1:3
        file=fullfile(folder,sprintf('%s_%02d.wav',labels(k),take));
        relative=string(strrep(file,[root filesep],''));
        if isfile(file)
            fprintf('Existing clip skipped: %s\n',file); continue
        end
        prompt=sprintf('%s | %s | take %d/3\n\n%s', ...
            sessionID,labels(k),take,instructions(k));
        while true
            choice=menu(prompt,'Record 8 seconds','Skip clip','Stop session');
            if choice==0||choice==3,return;end
            if choice==2,break;end
            fprintf('Recording %s, take %d...\n',labels(k),take);
            recordblocking(recorder,seconds); audio=getaudiodata(recorder,'double');
            sound(audio,fs); pause(seconds+.2);
            peak=max(abs(audio)); fullScale=sum(abs(audio)>=1-1/32768);
            choice=menu(sprintf('Playback complete. Peak %.3f; full-scale samples %d.',peak,fullScale), ...
                'Accept recording','Record again','Stop session');
            if choice==0||choice==3,return;end
            if choice==2,continue;end
            if fullScale>0
                warning('Recording reached full scale. Reduce microphone gain and record again.');
                continue
            end
            if peak<1e-5
                warning('Near-silent input. Check the microphone before recording again.');
                continue
            end
            audiowrite(file,audio,fs,'BitsPerSample',16);
            timestamp=string(datetime('now','TimeZone','UTC','Format',"yyyy-MM-dd'T'HH:mm:ss'Z'"));
            row={relative,labels(k),sessionID,split,take,fs,numel(audio)/fs, ...
                20*log10(max(sqrt(mean(audio.^2)),1e-12)),peak,fullScale,timestamp};
            manifest=[manifest;cell2table(row,'VariableNames',manifest.Properties.VariableNames)]; %#ok<AGROW>
            writetable(manifest,manifestPath);
            fprintf('Saved %s\n',file); break
        end
    end
end
fprintf('Session complete. Manifest: %s\n',manifestPath);
end
