"""
Seed the shared base tables: ROR resesarch organization and metadata roles. 

Run AFTER init_db() has created the tables:

    from portal_core.db_setup import init_db
    from portal_core.seed import seed_ror_and_roles
    init_db(Engine())
    seed_ror_and_roles("/path/to/ror-data.csv")

or from the command line, from the portal repo:

    python -m portal_core.seed_ror_and_roles --ror-csv /path/to/ror-data.csv

"""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from portal_core.constants import postgres_engine
from portal_core.models import MetadataRole, ResearchOrganization
from portal_core.utils import app_logger as log

# path to ror csv in portal_core as of 8/24/2026 : /home/workspaceuser/mount/ror/v1.58-2024-12-11-ror-data_schema_v2.csv
DEFAULT_ROLES = ("Data Submitter", "Investigator")

def seed_ror_and_roles(ror_csv, roles=DEFAULT_ROLES, session=None):
    "Idempotent: skips organizations and roles that already exist."

    ror_csv = Path(ror_csv)
    if not ror_csv.is_file():
        raise FileNotFoundError(f"ROR CSV not found: {ror_csv}")

    owns_session = session is None
    session = session or Session(postgres_engine)
    try:
        have_roles = set(session.scalars(select(MetadataRole.name)))
        new_roles = [MetadataRole(name=r) for r in roles if r not in have_roles]
        session.add_all(new_roles)

        have_orgs = set(session.scalars(select(ResearchOrganization.id)))
        df = (
            pd.read_csv(ror_csv, low_memory=False)
            .rename(columns={"names.types.ror_display": "display_name"})
            [["id", "display_name"]]
            .dropna()
            .sort_values("display_name")
        )
        rows = [
            {"id": i, "display_name": d}
            for i, d in zip(df["id"], df["display_name"])
            if i not in have_orgs
        ]
        if rows:
            session.execute(insert(ResearchOrganization), rows)

        session.commit()
        log.info("Seeded %d organizations, %d roles", len(rows), len(new_roles))
        return len(rows), len(new_roles)
    finally:
        if owns_session:
            session.close()

def main(argv=None):
    p = argparse.ArgumentParser(description="Seed base ROR and role tables.")
    p.add_argument("--ror-csv", required=True, type=Path)
    args = p.parse_args(argv)
    seed_ror_and_roles(args.ror_csv)

if __name__ == "__main__":
    main()

# # ---------- Seed ROR organization ---------------
# # ROR_CSV = Path(__file__).resolve().parents[2] / "mount" / "ror" / "v1.58-2024-12-11-ror-data_schema_v2.csv"

# ror = pd.read_csv(ROR_CSV, low_memory=False)
# ror.sort_values(['names.types.ror_display'], inplace=True)

# with Session(constants.postgres_engine) as session:
#     for index, row  in ror.iterrows():
#         rid = row['id']
#         display = row['names.types.ror_display']
#         session.add(ResearchOrganization(id=rid, display_name=display))

#     session.add(MetadataRole(name="Data Submitter"))
#     session.add(MetadataRole(name='Investigator'))

#     session.commit()

# print(f"Done. Seeded {len(ror)} ROR organizations and 2 metadata roles.")


