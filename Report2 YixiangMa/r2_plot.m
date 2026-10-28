function fig = r2_plot(R, number)
% Report figures use explicit English labels and fixed comparison scales.
colours = [0.10 0.10 0.10;0.72 0.22 0.16;0.05 0.43 0.57;0.36 0.48 0.18];
fig = figure('Color','w','Position',[80 80 850 590], ...
    'Name',sprintf('Report 2 - Figure %d',number));
set(fig,'DefaultAxesFontSize',12,'DefaultTextFontSize',12);
if number>1, duration = numel(R.x)/R.fs; end
switch number
    case 1
        set(fig,'Position',[80 80 650 440]); axis off;
        labels = {'Recorded speech: anti-alias resample to 16 kHz', ...
            'Hann STFT: 32 ms window, 8 ms hop', ...
            'Log magnitude -> 2-D FFT -> temporal modulation mask', ...
            'Inverse 2-D FFT -> original phase -> overlap-add', ...
            'Compare fidelity, RMS envelope, spectrogram and CWT'};
        for k=1:5
            y=0.85-(k-1)*0.175;
            annotation(fig,'textbox',[0.07 y 0.86 0.115], ...
                'String',labels{k},'HorizontalAlignment','center', ...
                'VerticalAlignment','middle','FontSize',11, ...
                'EdgeColor',[.25 .25 .25],'BackgroundColor',[.94 .97 .98]);
            if k<5
                annotation(fig,'arrow',[.5 .5],[y y-0.06],'LineWidth',1.1);
            end
        end
    case 2
        tiledlayout(2,1,'TileSpacing','loose','Padding','compact');
        nexttile; keep=R.control.time<=1;
        plot(R.control.time(keep),R.control.original(keep),'Color',colours(1,:));hold on;
        plot(R.control.time(keep),R.control.filtered(keep),'Color',colours(3,:),'LineWidth',1.3);
        xlabel('Time (s)');ylabel('Log-magnitude trace (dB)');grid on;
        title('a  Known 4 Hz and 16 Hz modulation components');
        legend('Input trace','8 Hz low-pass','Location','southoutside','Orientation','horizontal');
        nexttile;
        b=bar([4 16],R.control.amplitudes.');
        b(1).FaceColor=colours(1,:); b(2).FaceColor=colours(3,:);
        xticks([4 16]); xlabel('Temporal modulation frequency (Hz)');
        ylabel('Component amplitude (dB)'); title('b  Calibration amplitude recovery');
        grid on; legend('Input','8 Hz low-pass','Location','northeast');
    case 3
        set(fig,'Position',[80 80 850 790]);
        tiledlayout(3,1,'TileSpacing','loose','Padding','compact');
        nexttile; plot((0:numel(R.x)-1)/R.fs,R.x,'Color',colours(3,:));
        xlim([0 duration]);xlabel('Time (s)');ylabel('Amplitude');
        title('a  Recorded speech after resampling');grid on;
        nexttile; spectrum(R,R.S,'b  Original STFT magnitude');
        nexttile;
        keep=R.meta.time>=0 & R.meta.time<=duration;
        z=R.logMagnitude(:,keep); [F,T]=size(z);
        taper=hann(F)*hann(T).';
        M=abs(fftshift(fft2((z-mean(z,2)).*taper)));
        hz=(-floor(T/2):ceil(T/2)-1)*(R.fs/R.meta.H)/T;
        cycles=(-floor(F/2):ceil(F/2)-1)*1000/(F*R.fs/R.meta.Nfft);
        imagesc(hz,cycles,20*log10(max(M,eps)/max(M,[],'all')));
        axis xy; xlim([-30 30]);ylim([-4 4]);clim([-70 0]);
        xlabel('Temporal modulation (Hz)');ylabel('Spectral modulation (cycles/kHz)');
        title('c  Display-only modulation spectrum');
        cb=colorbar;ylabel(cb,'Magnitude relative to peak (dB)');
    case 4
        tiledlayout(2,1,'TileSpacing','loose','Padding','compact');
        nexttile;hold on;
        for k=2:4
            plot(R.details{k}.temporalHz,R.details{k}.mask,'Color',colours(k,:),'LineWidth',1.5);
        end
        xlim([0 30]);ylim([-.03 1.05]);grid on;
        xlabel('Temporal modulation (Hz)');ylabel('Mask gain');
        title('a  Unity below 0.8 f_c; zero at and above f_c');
        legend('4 Hz','8 Hz','16 Hz','Location','northeast');
        nexttile;
        b=bar(R.cutoffs(2:4),R.metrics.TargetDynamicEnergy_pct(2:4),'FaceColor','flat');
        b.CData=colours(2:4,:);xticks([4 8 16]);ylim([0 100]);grid on;
        xlabel('Stop frequency f_c (Hz)');ylabel('Retained target dynamic energy (%)');
        title('b  Excludes all zero-temporal-modulation coefficients');
    case 5
        set(fig,'Position',[80 80 900 670]);
        tiledlayout(2,2,'TileSpacing','loose','Padding','compact');
        labels={'a  Original','b  4 Hz low-pass','c  8 Hz low-pass','d  16 Hz low-pass'};
        for k=1:4
            nexttile;
            if k==1, S=R.S;else,S=r2_stft(R.outputs(:,k),R.fs);end
            spectrum(R,S,labels{k});
        end
    case 6
        time=(0:numel(R.x)-1)/R.fs;
        tiledlayout(2,1,'TileSpacing','loose','Padding','compact');
        nexttile;hold on;
        for k=2:4
            envelope=sqrt(movmean(R.outputs(:,k).^2,round(.020*R.fs)));
            plot(time,envelope,'Color',colours(k,:),'LineWidth',1);
        end
        plot(time,R.referenceEnvelope,'Color',colours(1,:),'LineWidth',1.2);
        xlim([0 duration]);xlabel('Time (s)');ylabel('20 ms RMS amplitude');grid on;
        title('a  Whole-utterance RMS envelope');
        legend('4 Hz','8 Hz','16 Hz','Original','Location','southoutside','Orientation','horizontal');
        nexttile;
        plot(R.cutoffs(2:4),R.metrics.WaveformSNR_dB(2:4),'o-', ...
            'Color',colours(3,:),'LineWidth',1.4);
        xticks([4 8 16]);grid on;xlabel('Stop frequency (Hz)');
        xlim([3 17]);
        ylabel('Reference-to-error SNR (dB)');
        title('b  Waveform fidelity, not a noise-reduction gain');
    case 7
        set(fig,'Position',[80 80 900 670]);
        tiledlayout(2,2,'TileSpacing','loose','Padding','compact');
        limits=R.wavelet.time([1 end]);
        for k=1:2
            nexttile;
            if k==1, S=R.S;label='a  Original STFT';
            else,S=r2_stft(R.outputs(:,3),R.fs);label='b  8 Hz low-pass STFT';end
            spectrum(R,S,label); xlim(limits);ylim([0 4]);
        end
        referencePeak=max(abs(R.wavelet.original),[],'all');
        for k=1:2
            nexttile;
            if k==1,C=R.wavelet.original;label='c  Original CWT';
            else,C=R.wavelet.filtered;label='d  8 Hz low-pass CWT';end
            mag=20*log10(max(abs(C)/referencePeak,1e-6));
            mag(R.wavelet.frequency<R.wavelet.coi(:).')=NaN;
            surface(R.wavelet.time,R.wavelet.frequency/1000,zeros(size(C)),mag, ...
                'EdgeColor','none');view(0,90);axis tight;
            set(gca,'YScale','log');ylim([.08 4]);clim([-60 0]);
            hold on;plot3(R.wavelet.time,R.wavelet.coi/1000,ones(size(R.wavelet.time)), ...
                'w--','LineWidth',1);
            xlim(limits);xlabel('Time in utterance (s)');ylabel('Frequency (kHz, log scale)');
            yticks([.1 .25 .5 1 2 4]);title(label);
            cb=colorbar;ylabel(cb,'Relative CWT magnitude (dB)');
        end
    otherwise
        error('Unknown report figure.');
end
colormap(fig,parula);
folder=fileparts(mfilename('fullpath'));
destination=fullfile(folder,'generated');
if ~isfolder(destination),mkdir(destination);end
exportgraphics(fig,fullfile(destination,sprintf('figure%d.png',number)),'Resolution',200);
end

function spectrum(R,S,label)
imagesc(R.meta.time,R.meta.frequency/1000,20*log10(max(abs(S),R.floorMagnitude)));
axis xy;xlim([0 numel(R.x)/R.fs]);ylim([0 8]);
peak=max(R.logMagnitude,[],'all');clim([peak-75 peak]);
xlabel('Time in utterance (s)');ylabel('Frequency (kHz)');title(label);
cb=colorbar;ylabel(cb,'STFT magnitude (dB re 1)');
end
