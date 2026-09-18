"""Build a missing warehouse from repository CSVs, once per workspace."""
from pathlib import Path
import fcntl
import os
import subprocess
import sys
import tempfile

import duckdb
import yaml

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / 'Gasstation_dw_duckdb'
TABLES = ('Customer', 'Employee', 'GasStation', 'InventoryTransaction',
          'Invoice', 'InvoiceDetail', 'Product', 'StorageTank')


def prepare_warehouse(find_database):
    # An explicitly chosen database must never be silently replaced.
    if os.environ.get('GASSTATION_DB'):
        return find_database()
    with (ROOT / '.warehouse-build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            return find_database()
        except RuntimeError:
            pass
        destination = PROJECT / 'dev.duckdb'
        if destination.exists():
            raise RuntimeError(
                f'{destination} exists but is incomplete. Back it up and rebuild it with dbt; '
                'automatic setup will not overwrite an existing database.'
            )
        sources = {name: PROJECT / 'Datasets' / f'{name}.csv' for name in TABLES}
        missing = [str(path) for path in sources.values() if not path.is_file()]
        if missing:
            raise RuntimeError('Missing source CSV files: ' + ', '.join(missing))
        dbt = Path(sys.executable).parent / 'dbt'
        if not dbt.is_file():
            raise RuntimeError('Install dependencies: python3 -m pip install -r requirements.txt')
        with tempfile.TemporaryDirectory(prefix='.warehouse-build-', dir=ROOT) as temp:
            temp = Path(temp)
            database = temp / 'dev.duckdb'
            with duckdb.connect(str(database)) as connection:
                for name, path in sources.items():
                    connection.execute(
                        f'CREATE TABLE "{name}" AS SELECT * FROM read_csv_auto(?)', [str(path)]
                    )
            profile = {'gasstation_dw': {'target': 'dev', 'outputs': {'dev': {
                'type': 'duckdb', 'path': str(database), 'threads': 1
            }}}}
            (temp / 'profiles.yml').write_text(yaml.safe_dump(profile), encoding='utf-8')
            for command, selection in [('seed', 'station_region_map'),
                                       ('run', 'staging datawarehouse')]:
                result = subprocess.run(
                    [str(dbt), command, '--project-dir', str(PROJECT),
                     '--profiles-dir', str(temp), '--select', *selection.split()],
                    cwd=PROJECT, capture_output=True, text=True,
                )
                if result.returncode:
                    raise RuntimeError(f'dbt {command} failed:\n{result.stdout}\n{result.stderr}')
            # Publish only after every dbt command succeeds.
            database.replace(destination)
        return find_database()
