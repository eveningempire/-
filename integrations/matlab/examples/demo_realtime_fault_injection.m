function responses = demo_realtime_fault_injection(ingestUrl, token, injectionTime)
% Send normal telemetry first, then return abnormal telemetry after the
% platform-selected injection time. The platform performs live detection.
if nargin < 3
    injectionTime = 3.0;
end
responses = cell(1, 20);
for k = 1:20
    t = (k - 1) * 0.5;
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
    pause(0.15);
end
end
