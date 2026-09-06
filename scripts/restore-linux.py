"""Restore a verified LocalSend snapshot into empty local PostgreSQL databases.

Run after docker compose up -d postgres. Refuses databases containing user rows.
No production/remote connection is used; all commands execute inside a container.
"""
import argparse
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("handoff", type=Path)
parser.add_argument("--container", default="googlemapsscraping-postgres-1")
parser.add_argument("--user", default="gmaps_scraper")
args = parser.parse_args()
base = ["docker", "exec", args.container]

def sql(db, query):
    return subprocess.check_output(base + ["psql", "-X", "-v", "ON_ERROR_STOP=1",
        "-U", args.user, "-d", db, "-Atc", query], text=True).strip()

guard = """
do $$ declare t record; occupied boolean; begin
  for t in select schemaname, tablename from pg_tables
    where schemaname not in ('pg_catalog', 'information_schema') loop
    execute format('select exists(select 1 from %I.%I limit 1)',
      t.schemaname, t.tablename) into occupied;
    if occupied then raise exception 'Refusing nonempty database: %.%',
      t.schemaname, t.tablename; end if;
  end loop;
end $$;
"""
databases = ["lead_warehouse", "gmaps_scraper"]
for db in databases:
    archive = args.handoff.resolve() / "postgres" / (db + ".dump")
    if not archive.is_file():
        raise SystemExit(f"Missing archive: {archive}")
    if sql("postgres", f"select 1 from pg_database where datname='{db}'"):
        sql(db, guard)

for db in databases:
    if not sql("postgres", f"select 1 from pg_database where datname='{db}'"):
        subprocess.run(base + ["createdb", "-U", args.user, "-T", "template0", db], check=True)
    archive = args.handoff.resolve() / "postgres" / (db + ".dump")
    print(f"Restoring {db}...", flush=True)
    with archive.open("rb") as stream:
        subprocess.run(["docker", "exec", "-i", args.container, "pg_restore",
            "-U", args.user, "-d", db, "--exit-on-error", "--clean", "--if-exists",
            "--no-owner", "--no-privileges"], stdin=stream, check=True)
    print(f"Restored {db}.", flush=True)
print("Restore complete. Run the status commands in LINUX_HANDOFF.md.")
