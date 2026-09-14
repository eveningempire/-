function response = phm_send_telemetry(ingestUrl, token, samples)
% Send actual scalar signal samples from a MATLAB/Simulink callback.
% samples: scalar struct or struct array; time in simulation seconds,
% other fields are finite numeric signals. Same fields per session.
% Batch calls to reduce HTTP overhead. Errors propagate to caller.
    if ~isstruct(samples) || isempty(samples)
        error('PHM:InvalidSamples', 'samples must be a nonempty struct array');
    end
    payload = struct();
    payload.samples = num2cell(samples(:));
    options = weboptions('MediaType', 'application/json', ...
        'HeaderFields', {'Authorization', ['Bearer ' char(token)]}, ...
        'Timeout', 10, 'ContentType', 'json');
    response = webwrite(char(ingestUrl), payload, options);
end
