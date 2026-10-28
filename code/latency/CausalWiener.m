classdef CausalWiener < handle
    % Stateful left-aligned STFT/OLA. step() receives only arrived samples.
    properties (SetAccess = private)
        cfg
        window
        pending
        history
        overlap
        overlapWeight
        noiseSum
        noiseCount = 0
        previousPower
        received = 0
        frames = 0
    end
    methods
        function obj = CausalWiener(cfg)
            obj.cfg = cfg;
            L = cfg.windowLength; H = cfg.hopLength;
            assert(L == 2*H, 'This Hann/OLA implementation uses 50 percent overlap.');
            obj.window = hann(L,'periodic');
            obj.pending = zeros(0,1);
            obj.history = zeros(L-H,1);
            obj.overlap = zeros(L,1);
            obj.overlapWeight = zeros(L,1);
            obj.noiseSum = zeros(cfg.fftLength,1);
            obj.previousPower = zeros(cfg.fftLength,1);
        end

        function [output, schedule, gains] = step(obj, arrived)
            validateattributes(arrived,{'double'},{'column','real','finite'});
            obj.pending = [obj.pending; arrived];
            H = obj.cfg.hopLength; L = obj.cfg.windowLength;
            count = floor(numel(obj.pending)/H);
            output = zeros(count*H,1);
            % Columns: input samples consumed, logical block start (zero-based).
            schedule = zeros(count,2);
            capture = isfield(obj.cfg,'captureDiagnostics') && obj.cfg.captureDiagnostics;
            if capture
                gains = zeros(obj.cfg.fftLength/2+1,count);
            else
                gains = zeros(0,0);
            end
            for block = 1:count
                incoming = obj.pending(1:H);
                obj.pending(1:H) = [];
                frame = [obj.history; incoming];
                obj.history = frame(H+1:end);
                obj.received = obj.received+H;
                obj.frames = obj.frames+1;
                startSample = obj.received-L;
                Y = fft(frame.*obj.window,obj.cfg.fftLength);
                power = abs(Y).^2;
                calibrationEnd = round(obj.cfg.calibrationSeconds*obj.cfg.fs);
                if startSample >= 0 && obj.received <= calibrationEnd
                    obj.noiseSum = obj.noiseSum+power;
                    obj.noiseCount = obj.noiseCount+1;
                end
                if obj.cfg.bypassGain || obj.received <= calibrationEnd
                    gain = ones(size(power));
                else
                    assert(obj.noiseCount >= 2,'Not enough complete calibration frames.');
                    noisePSD = obj.noiseSum/obj.noiseCount;
                    noisePSD = max(noisePSD,max(max(noisePSD)*1e-12,realmin));
                    posterior = power./noisePSD;
                    alpha = exp(-H/(obj.cfg.fs*obj.cfg.smoothingSeconds));
                    prior = alpha*obj.previousPower./noisePSD ...
                        + (1-alpha)*max(posterior-1,0);
                    gain = max(obj.cfg.minimumGain,prior./(1+prior));
                end
                obj.previousPower = gain.^2.*power;
                if capture, gains(:,block) = gain(1:obj.cfg.fftLength/2+1); end
                timeFrame = real(ifft(gain.*Y,obj.cfg.fftLength));
                obj.overlap = obj.overlap+timeFrame(1:L);
                obj.overlapWeight = obj.overlapWeight+obj.window;
                emitted = obj.overlap(1:H)./max(obj.overlapWeight(1:H),eps);
                if obj.frames == 1
                    emitted(:) = 0; % Past-only padding represents startup silence.
                end
                output((block-1)*H+(1:H)) = emitted;
                schedule(block,:) = [obj.received,startSample];
                obj.overlap = [obj.overlap(H+1:end); zeros(H,1)];
                obj.overlapWeight = [obj.overlapWeight(H+1:end); zeros(H,1)];
            end
        end
    end
end
