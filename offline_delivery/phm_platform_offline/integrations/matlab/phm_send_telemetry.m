function response = phm_send_telemetry(ingestUrl, token, samples)
%PHM_SEND_TELEMETRY Send telemetry using MATLAB's built-in Java HTTP client.
%
% This implementation intentionally uses only APIs available in MATLAB
% 2012 (java.net.HttpURLConnection and a small JSON encoder). It does not
% require MATLAB Engine or any network package.

    if nargin ~= 3
        error('PHM:Usage', 'Call phm_send_telemetry(ingestUrl, token, samples).');
    end
    if ~ischar(ingestUrl) || isempty(ingestUrl)
        error('PHM:InvalidUrl', 'ingestUrl must be a nonempty character vector.');
    end
    if ~ischar(token) || isempty(token)
        error('PHM:InvalidToken', 'token must be a nonempty character vector.');
    end
    if ~isstruct(samples) || isempty(samples)
        error('PHM:InvalidSamples', 'samples must be a nonempty struct array.');
    end
    if ~usejava('jvm')
        error('PHM:JavaRequired', 'MATLAB Java virtual machine is required for HTTP access.');
    end

    payload = struct();
    payload.samples = num2cell(samples(:));
    requestBody = phm_json_encode(payload);

    conn = [];
    inputStream = [];
    try
        url = java.net.URL(ingestUrl);
        conn = url.openConnection();
        conn.setRequestMethod('POST');
        conn.setDoOutput(true);
        conn.setConnectTimeout(10000);
        conn.setReadTimeout(10000);
        conn.setRequestProperty('Content-Type', 'application/json; charset=UTF-8');
        conn.setRequestProperty('Accept', 'application/json');
        conn.setRequestProperty('Authorization', ['Bearer ' token]);

        outputStream = conn.getOutputStream();
        bodyBytes = java.lang.String(requestBody).getBytes('UTF-8');
        outputStream.write(bodyBytes);
        outputStream.flush();
        outputStream.close();

        statusCode = conn.getResponseCode();
        if statusCode >= 400
            inputStream = conn.getErrorStream();
        else
            inputStream = conn.getInputStream();
        end
        raw = phm_read_java_stream(inputStream);
        if ~isempty(inputStream)
            inputStream.close();
        end
        conn.disconnect();
    catch
        % MATLAB 2012 accepts catch without an exception variable.  Read the
        % last error explicitly for compatibility with older releases.
        exception = lasterror;
        if ~isempty(inputStream)
            try
                inputStream.close();
            catch
                ignored = lasterror; %#ok<NASGU>
            end
        end
        if ~isempty(conn)
            try
                conn.disconnect();
            catch
                ignored = lasterror; %#ok<NASGU>
            end
        end
        error('PHM:HTTP', 'Unable to send telemetry: %s', exception.message);
    end

    response = struct();
    response.status_code = statusCode;
    response.raw = raw;
    response.ok = statusCode >= 200 && statusCode < 300;
    response.accepted = phm_json_number(raw, 'accepted', 0);
    response.alarms = phm_json_number(raw, 'alarms', 0);
    response.last_time = phm_json_number(raw, 'last_time', NaN);
    response.monitoring_enabled = phm_json_boolean(raw, 'monitoring_enabled', false);
    if ~response.ok
        response.error = phm_json_text(raw, 'detail', 'HTTP request failed');
    else
        response.error = '';
    end
end

function raw = phm_read_java_stream(inputStream)
    if isempty(inputStream)
        raw = '';
        return;
    end
    reader = java.io.BufferedReader(java.io.InputStreamReader(inputStream, 'UTF-8'));
    parts = {};
    line = reader.readLine();
    while ~isempty(line)
        parts{end + 1} = char(line); %#ok<AGROW>
        line = reader.readLine();
    end
    reader.close();
    raw = '';
    for k = 1:numel(parts)
        if k > 1
            raw = [raw sprintf('\n')]; %#ok<AGROW>
        end
        raw = [raw parts{k}]; %#ok<AGROW>
    end
end

function value = phm_json_number(raw, name, defaultValue)
    pattern = ['"' name '"\s*:\s*([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)'];
    tokens = regexp(raw, pattern, 'tokens', 'once');
    if isempty(tokens)
        value = defaultValue;
    else
        value = str2double(tokens{1});
    end
end

function value = phm_json_boolean(raw, name, defaultValue)
    pattern = ['"' name '"\s*:\s*(true|false)'];
    tokens = regexp(raw, pattern, 'tokens', 'once');
    if isempty(tokens)
        value = defaultValue;
    else
        value = strcmp(tokens{1}, 'true');
    end
end

function value = phm_json_text(raw, name, defaultValue)
    pattern = ['"' name '"\s*:\s*"((\\.|[^"\\])*)"'];
    tokens = regexp(raw, pattern, 'tokens', 'once');
    if isempty(tokens)
        value = defaultValue;
    else
        value = tokens{1};
    end
end

function text = phm_json_encode(value)
    if isstruct(value)
        if numel(value) ~= 1
            parts = cell(1, numel(value));
            for k = 1:numel(value)
                parts{k} = phm_json_encode(value(k));
            end
            text = ['[' phm_join(parts) ']'];
            return;
        end
        names = fieldnames(value);
        parts = cell(1, numel(names));
        for k = 1:numel(names)
            fieldName = names{k};
            parts{k} = [phm_json_encode(fieldName) ':' phm_json_encode(value.(fieldName))];
        end
        text = ['{' phm_join(parts) '}'];
    elseif iscell(value)
        parts = cell(1, numel(value));
        for k = 1:numel(value)
            parts{k} = phm_json_encode(value{k});
        end
        text = ['[' phm_join(parts) ']'];
    elseif ischar(value)
        text = ['"' phm_json_escape(value) '"'];
    elseif islogical(value)
        if isempty(value)
            text = 'null';
        elseif numel(value) == 1
            if value
                text = 'true';
            else
                text = 'false';
            end
        else
            parts = cell(1, numel(value));
            for k = 1:numel(value)
                parts{k} = phm_json_encode(value(k));
            end
            text = ['[' phm_join(parts) ']'];
        end
    elseif isnumeric(value)
        if isempty(value)
            text = 'null';
        elseif numel(value) ~= 1
            parts = cell(1, numel(value));
            for k = 1:numel(value)
                parts{k} = phm_json_encode(value(k));
            end
            text = ['[' phm_join(parts) ']'];
        elseif ~isfinite(value)
            error('PHM:InvalidSamples', 'Telemetry values must be finite numbers.');
        else
            text = sprintf('%.17g', value);
        end
    else
        error('PHM:InvalidSamples', 'Unsupported telemetry value type: %s.', class(value));
    end
end

function escaped = phm_json_escape(value)
    escaped = strrep(value, '\', '\\');
    escaped = strrep(escaped, '"', '\"');
    escaped = strrep(escaped, sprintf('\b'), '\b');
    escaped = strrep(escaped, sprintf('\f'), '\f');
    escaped = strrep(escaped, sprintf('\n'), '\n');
    escaped = strrep(escaped, sprintf('\r'), '\r');
    escaped = strrep(escaped, sprintf('\t'), '\t');
end

function text = phm_join(parts)
    text = '';
    for k = 1:numel(parts)
        if k > 1
            text = [text ',']; %#ok<AGROW>
        end
        text = [text parts{k}]; %#ok<AGROW>
    end
end

