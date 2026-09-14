function response = demo_send_telemetry(ingestUrl, token)
%DEMO_SEND_TELEMETRY Send a small deterministic telemetry batch to PHM.
%
% Example:
%   demo_send_telemetry( ...
%       'http://127.0.0.1:8000/api/v1/phm/telemetry/sessions/<id>/ingest/', ...
%       '<token-from-the-web-page>');
%
% Create a MATLAB realtime session in the web UI first.  The session token
% is shown only once.  This demo sends 20 samples with three numeric fields.

if nargin ~= 2 || ~(ischar(ingestUrl) || isstring(ingestUrl)) || ...
        ~(ischar(token) || isstring(token))
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
