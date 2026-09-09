# PHM Offline Runtime Install

This migration package includes the installers required by an offline destination computer:

- `runtime-installers/python-3.10.11-amd64.exe`
- `runtime-installers/node-v22.18.0-x64.msi`
- `runtime-installers/mysql-installer-community-8.0.43.msi` (optional)

Run `install_runtime_offline.bat` first. It installs Python 3.10.11 and Node.js 22.18.0 from local files. Reopen the terminal, then run `setup_migration.ps1`.

`setup_migration.ps1` installs Python packages with `--no-index` from `offline/python`. Frontend packages are already bundled in `frontend/node_modules`, so npm does not need internet access.

