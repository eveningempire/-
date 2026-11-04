"""Download and verify the complete real simulation archive from GitHub Release."""
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    root = Path(__file__).resolve().parent
    directory = root / 'integrations/simulation_assets'
    expected = json.loads((directory / 'simulation_samples.json').read_text(encoding='utf-8'))['source_sha256']
    target = directory / 'simulate_data_+1.zip'
    if target.is_file():
        with target.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else _digest(stream)
        if digest == expected:
            print('Complete simulation archive already verified. Restart PHM to use it.')
            return
        raise RuntimeError('An existing archive has a different checksum; move it aside before downloading.')
    url = 'https://github.com/eveningempire/-/releases/download/phm-github-20261104/simulate_data_%2B1.zip'
    temporary = target.with_suffix('.zip.partial')
    digest = hashlib.sha256()
    total = 0
    checkpoint = 0
    print('Downloading the complete simulation archive (about 1.05 GiB)...', flush=True)
    try:
        with urllib.request.urlopen(url, timeout=120) as response, temporary.open('wb') as output:
            for chunk in iter(lambda: response.read(1024 * 1024), b''):
                output.write(chunk)
                digest.update(chunk)
                total += len(chunk)
                if total - checkpoint >= 64 * 1024 * 1024:
                    checkpoint = total
                    print(f'{total / 1048576:.0f} MiB received', flush=True)
        if digest.hexdigest() != expected:
            raise RuntimeError('Downloaded archive checksum mismatch; rerun the download.')
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    print('Verified. Restart PHM and run import_sample_data.bat to import all CSVs.')


def _digest(stream):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(chunk)
    return digest.hexdigest()


if __name__ == '__main__':
    main()
