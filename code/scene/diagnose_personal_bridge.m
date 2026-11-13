function diagnose_personal_bridge()
%DIAGNOSE_PERSONAL_BRIDGE Inspect startup statistics without changing processors.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root,'code','latency'));
out=fullfile(root,'results','scene_bridge');
manifest=jsondecode(fileread(fullfile(out,'input_manifest.json')));
startup=table();projection=table();
for k=1:numel(manifest.cases)
    c=manifest.cases(k);d=load(fullfile(root,c.input_mat));
    x=double(d.input);P=double(d.prefixSamples);N=double(d.speechSamples);
    prefixPower=mean(x(1:P).^2);noisePower=mean(d.scaledNoise.^2);
    row=table(string(c.case_id),string(c.noise_source), ...
        10*log10(max(prefixPower,realmin)),10*log10(max(noisePower,realmin)), ...
        10*log10(max(noisePower,realmin)/max(prefixPower,realmin)), ...
        'VariableNames',{'CaseID','NoiseSource','PrefixPower_dBFS','ScoredNoisePower_dBFS','NoiseRise_dB'});
    startup=[startup;row]; %#ok<AGROW>
    neural=audioread(fullfile(root,'data','local','scene_bridge','reference',string(c.case_id)+".wav"));
    y=neural(1440+P+(1:N));clean=d.clean;
    row=table(string(c.case_id),c.input_snr_db,dot(clean,y)/dot(clean,clean), ...
        norm(y)/norm(clean),'VariableNames', ...
        {'CaseID','InputSNR_dB','TargetProjectionGain','OutputReferenceNormRatio'});
    projection=[projection;row]; %#ok<AGROW>
    if k==1
        cfg=latency_config(40);cfg.captureDiagnostics=true;
        [enhanced,info]=run_causal_stream(x,cfg);
        expected=load(fullfile(root,'data','local','scene_bridge','wiener',string(c.case_id)+".mat"));
        assert(max(abs(enhanced(P+(1:N))-expected.outputs(:,3)))<1e-12);
        inside=info.gainFrameStartSamples>=P & info.gainFrameStartSamples+cfg.windowLength<=P+N;
        gains=info.gains(:,inside);
        starts=info.gainFrameStartSamples(inside);
        powers=zeros(size(gains));
        for frame=1:numel(starts)
            spectrum=abs(fft(x(starts(frame)+(1:cfg.windowLength)).*hann(cfg.windowLength,'periodic'),cfg.fftLength)).^2;
            powers(:,frame)=spectrum(1:cfg.fftLength/2+1).*[1;2*ones(cfg.fftLength/2-1,1);1];
        end
        energyGain=sum(gains.^2.*powers,'all')/sum(powers,'all');
        relativeDifference=norm(enhanced(P+(1:N))-x(P+(1:N)))/norm(x(P+(1:N)));
        diagnostic=table(string(c.case_id),min(gains,[],'all'),mean(gains,'all'),mean(gains>.99,'all'), ...
            energyGain,relativeDifference,'VariableNames',{'CaseID','MinimumGain','MeanGain', ...
            'FractionAbove099','EnergyWeightedGainSquared','OutputInputRelativeDifference'});
        writetable(diagnostic,fullfile(out,'first_case_gain_diagnostics.csv'));
    end
end
writetable(startup,fullfile(out,'startup_diagnostics.csv'));
writetable(projection,fullfile(out,'reference_projection_diagnostics.csv'));
fprintf('PASS: startup and gain diagnostics; original output unchanged.\n');
disp(startup([1 4 7],:));disp(diagnostic);
end
