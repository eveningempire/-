function responses = demo_realtime_fault_injection(ingestUrl, token, injectionTime, duration, samplePeriod)
% Send normal telemetry first, then return abnormal telemetry after the
% platform-selected injection time. The platform performs live detection.
if nargin < 3
    injectionTime = 3.0;
end
if nargin < 4
    duration = 60.0;
end
if nargin < 5
    samplePeriod = 0.25;
end
if duration <= 0 || samplePeriod <= 0
    error('PHM:InvalidDemoParameters', 'duration and samplePeriod must be positive');
end
times = 0:samplePeriod:duration;
responses = cell(1, numel(times));
for k = 1:numel(times)
    t = times(k);
    sample = struct('time', t, ...
        'pressure', 1.0 + 0.01 * sin(t), ...
        'temperature', 0.4 + 0.01 * cos(t), ...
        'attitude_error', 0.005 * sin(t), ...
        'control_error', 0.02 + 0.005 * cos(t));
    if t >= injectionTime
        % The platform selects a pressure-leak injection. MATLAB returns
        % pressure data below the live alarm threshold.
        sample.pressure = 0.65 - 0.01 * (t - injectionTime);
    end
    responses{k} = phm_send_telemetry(ingestUrl, token, sample);
    fprintf('PHM sample t=%.1f pressure=%.4f accepted=%d alarms=%d\n', ...
        t, sample.pressure, responses{k}.accepted, responses{k}.alarms);
    pause(min(samplePeriod * 0.6, 0.15));
end
end
