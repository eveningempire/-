"""Choose the complete simulation archive, or the bundled real sample set."""
import os
from pathlib import Path


def simulation_archive(root):
    override = os.environ.get('HEALTH_SIMULATION_ARCHIVE')
    if override:
        return Path(override)
    directory = Path(root) / 'integrations' / 'simulation_assets'
    complete = directory / 'simulate_data_+1.zip'
    return complete if complete.is_file() else directory / 'simulation_samples.zip'
