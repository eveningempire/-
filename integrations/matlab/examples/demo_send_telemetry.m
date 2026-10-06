function response = demo_send_telemetry(ingestUrl, token)
%DEMO_SEND_TELEMETRY Send a small deterministic telemetry batch to PHM.
%
% Compatible with MATLAB 2012 and newer.  Create a MATLAB realtime session
% in the web UI first, then copy its URL and token into this function call.

if nargin ~= 2 || ~ischar(ingestUrl) || ~ischar(token) || ...
        isempty(ingestUrl) || isempty(token)
    error('PHM:Usage', 'Call demo_send_telemetry(ingestUrl, token).');
end

samples = repmat(struct('time', 0, 'pressure', 0, 'temperature', 0), 1, 20);
for k = 1:numel(samples)
    t = (k - 1) * 0.1;
    samples(k).time = t;
    samples(k).pressure = 1.2 + 0.05 * sin(t);
    samples(k).temperature = 300 + 2 * cos(t);
end

response = phm_send_telemetry(ingestUrl, token, samples);
disp(response);
end
