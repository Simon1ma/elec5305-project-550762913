function rows = scene_multiscale_features(audio, fs)
%SCENE_MULTISCALE_FEATURES Full recording plus activity-filtered 1.5/3 s windows.
x=double(audio(:)); if fs~=16000,[p,q]=rat(16000/fs);x=resample(x,p,q);end
fs=16000; x=x-mean(x); duration=numel(x)/fs;
assert(duration>=.5,'At least 0.5 seconds is required.');
row=scene_rich_features(x,fs);
rows=addvars(row,"full",0,duration,'Before',1, ...
    'NewVariableNames',{'Mode','StartSeconds','EndSeconds'});
for scale=[1.5 3]
    L=min(round(scale*fs),numel(x));H=max(1,floor(L/2));
    starts=unique([1:H:numel(x)-L+1,numel(x)-L+1]);
    levels=arrayfun(@(s)sqrt(mean(x(s:s+L-1).^2)),starts);
    keep=levels>=max(max(levels)*.15,1e-10);
    if ~any(keep),[~,best]=max(levels);keep(best)=true;end
    starts=starts(keep);
    for start=starts
        row=scene_rich_features(x(start:start+L-1),fs);
        row=addvars(row,"w"+string(scale),(start-1)/fs,(start+L-1)/fs, ...
            'Before',1,'NewVariableNames',{'Mode','StartSeconds','EndSeconds'});
        rows=[rows;row]; %#ok<AGROW>
    end
end
end
