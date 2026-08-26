from sqlalchemy import text, select
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd

from portal_core.constants import (
    submissions_table,
    postgres_engine,
    files_table
)

from portal_core.models import DashboardUser, File, Submission, OadsMetadata


def delete_file(file_id):
    with Session(postgres_engine) as session:
        #DEBUG print(file_id)
        file_to_delete = session.query(File).where(File.id==file_id).one()
        session.delete(file_to_delete)
        session.commit()


def delete_submission(submission, dashboard_user):
    with Session(postgres_engine) as session:
        submission = session.query(Submission).where(Submission.id==submission).one()
        session.delete(submission)
        session.commit()

def get_data_files(submission, category):
    # SELECT * FROM file JOIN submission ON submission_id=file.submission_id WHERE file.submission_id=1;
    # Brynn added category as an input so gets data files by category
    data_files = text(f"""
        SELECT f.id as id, f.filename as filename, f.created as modified, f.category as category, s.id as submission_id, s.dashboard_user_id as dashboard_user_id, s.date_submitted_to_ncei FROM {files_table} f
        JOIN {submissions_table} s ON s.id=f.submission_id
            WHERE f.submission_id='{submission}' AND f.category='{category}'            
    """)
    df = pd.read_sql(data_files, postgres_engine)
    # DEBUG print(data_files)
    df["delete"] = "Delete"
    return df


def file_exists(submission_id, filename, category):
    with Session(postgres_engine) as session:
        stmt = select(File).where(File.submission_id==submission_id).where(File.filename==filename).where(File.category==category)
        files = session.scalars(stmt).all()
        if len(files) >= 1:
            return True
        else:
            return False


def lookup_use_by_email(dashboard_user_email):
    session = Session(postgres_engine)
    stmt = select(DashboardUser).where(DashboardUser.email==dashboard_user_email)
    persons = session.scalars(stmt).all()
    if len(persons) == 1:
        return persons[0]
    else:
        if len(persons) > 1:
            # Shouldn't happend as there is a unique constraint on the mail field of submitter
            print(str(len(persons)), '**Error: USERS FOUND WITH THE SAME EMAIL', dashboard_user_email, '!!!')
        return None

def get_submissions_with_file_lists(dashboard_user_id, metadata_url):
    data_select = """
        SELECT 
            a.id,
            a.created,
            a.submitted_to_ncei,
            a.date_submitted_to_ncei,
            b.filename AS filename,
            b.category AS category
        FROM {} a
            LEFT JOIN {} b
            ON a.id = b.submission_id
        WHERE a.dashboard_user_id = '{}'
    """.format(
        submissions_table, files_table, dashboard_user_id
    )
    with postgres_engine.begin() as conn:
        df = pd.read_sql_query(data_select, conn)
    if not df.empty:
        df = df.groupby(
            ['id', 'created', 'submitted_to_ncei', 'date_submitted_to_ncei', 'category'], 
            dropna=False # CRITICAL: Keeps rows where grouping keys are NaN/Empty
        )['filename'].apply(list).reset_index()
        df = df.pivot(
            index=['id', 'created', 'submitted_to_ncei', 'date_submitted_to_ncei'], 
            columns='category', 
            values='filename'
        ).reset_index()

        # Optional: Remove the name of the columns index ('category') for cleaner output
        df.columns.name = None
        df = df.rename(columns={'data':'data_files', 'supplemental': 'supp_files', 'created': 'date_created'})
        df["edit"] = "Edit"
        df["delete"] = "Delete"
        df['submit'] = 'Submit to NCEI'
        df['date_created'] = pd.to_datetime(df['date_created']).dt.strftime('%Y-%m-%d') # get only the date and remove the time stamp
    else: # If empty (no submissions, will return empty df)
        df = pd.DataFrame(columns=['id', 'date_created', 'submitted_to_ncei', 'date_submitted_to_ncei', 'data_files', 'supp_files', 'edit', 'delete', 'submit'])
    return df

    
def get_submissions_with_counts(dashboard_user_id, metadata_url):
    data_select = """
        SELECT 
            a.id,
            a.submitted_to_ncei,
            a.date_submitted_to_ncei,
            COUNT(b.filename) AS data_count
        FROM {} a
            LEFT JOIN {} b
            ON a.id = b.submission_id
        WHERE a.dashboard_user_id = '{}'
        GROUP BY a.id
    """.format(
        submissions_table, files_table, dashboard_user_id
    )
  
    # DEBUG print(data_select)
    # https://stackoverflow.com/questions/71082494/getting-a-warning-when-using-a-pyodbc-connection-object-with-pandas
    with postgres_engine.begin() as conn:
        df = pd.read_sql_query(data_select, conn)

    if not df.empty:
        df["edit"] = "Edit"
        df["edit_metadata"] = '[Edit Metadata](' + metadata_url + df['id'].astype(str) + ')'
        df["delete"] = "Delete"
        df['preview'] = "Preview"
        df['submit'] = 'Submit to NCEI'
    return df


def insert_file(submission_id, filename, mime, category):
    with Session(postgres_engine) as session:
        file = File(submission_id=submission_id, filename=filename, mime=mime, category=category)
        session.add(file)
        session.commit()

def insert_submission(submission, dashboard_user_id):
    with postgres_engine.connect() as conn:
        insert = """
            INSERT INTO {} (
                id,
                dashboard_user_id
            )
            VALUES (
                $${}$$,
                $${}$$
            ) ON CONFLICT DO NOTHING
        """
        conn.execute(text(
            insert.format(
                submissions_table,
                submission,
                dashboard_user_id,
            )
        ))

def get_or_create_oads_metadata_id(session: Session, submission_id: str) -> int:
    """
    Return OadsMetadata.id for a submission, creating a blank row
    if needed
    """
    oads = session.query(OadsMetadata).filter_by(submission_id=submission_id).first()

    if oads is None:
        oads = OadsMetadata(submission_id=submission_id)
        session.add(oads)
        session.flush() # gets oads.id before using it as FK

    
    return oads.id

def get_oads_metadata_id(session, submission_id: str) -> Optional[int]:
    """
    Read-only lookup -- does NOT create a row if one doesn't exist yet
    (unlike get_or_creaet_oads_metadadta_id, which is for the save_path for 
    Ocean Sites)
    """
    stmt = select(OadsMetadata.id).where (OadsMetadata.submission_id == submission_id)
    return session.execute(stmt).scalar_one_or_none()