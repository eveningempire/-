# MySQL to SQLite data migration

The current `db.sqlite3` contains the converted records from the supplied DBeaver dump. The old `database-source/` SQL and JSON export copies were removed during workspace cleanup; they are not used when running the platform. Keep the current database and `media/` together when making a backup.

On the computer that can reach the original MySQL server, run from this package directory:

```powershell
.\export_mysql_data.ps1 -Host 127.0.0.1 -Port 3306 -Database cmg_db -User Kaimol -Password YOUR_PASSWORD -Output mysql_export.json
```

Copy `mysql_export.json` to the offline computer. After running `setup_migration.ps1`, import it with:

```powershell
.\import_sqlite_data.ps1 -Input mysql_export.json
```

This uses Django fixtures and does not require MySQL on the destination. Large telemetry tables can produce a large JSON fixture; preserve the file until import succeeds. Uploaded files are separate from SQL and must be copied from the source `media` directory.

The export script requires valid MySQL connectivity and credentials. It is useful for refreshing the package if the source database changes.
