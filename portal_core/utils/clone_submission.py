from portal_core.models import (
    OadsMetadata,
    OadsMetadataInvestigators,
    Submission,
    OadsMetadataDataSubmitter,
    RelatedDataset
)
from portal_core.constants import postgres_engine
from sqlalchemy.orm import Session
from portal_core.utils import (
    create_submission_id,
    app_logger as log
)

def clone_submission(original_submission_id: str, dashboard_user_id: int, portal):
    """
    Deep clones a Submission and all downstream OadsMetadata data in Base.
    Returns the new submission id on success.
    """ 
    with Session(postgres_engine) as session:
        original = session.query(Submission).filter_by(id=original_submission_id).first()
        if not original:
            log.error(f"Submission {original_submission_id} not found")
            raise ValueError(f"Submission {original_submission_id} not found")

        # 1. New Submission
        new_id = create_submission_id(dashboard_user_id)
        new_submission = Submission(
            id=new_id,
            dashboard_user_id=dashboard_user_id,
            submitted_to_ncei=False,
            date_submitted_to_ncei=None
        )
        session.add(new_submission)
        session.flush()

        # 2. Clone OadsMetadata (if it exists)
        orig_meta = original.oads_metadata
        if orig_meta:
            new_meta = OadsMetadata(
                submission_id=new_submission.id,
                submission_date=orig_meta.submission_date,
                title=f"Copy of {orig_meta.title}" if orig_meta.title else None,
                abstract=orig_meta.abstract,
                doi=None,
                doi_requested=False,
                use_limitation=orig_meta.use_limitation,
                purpose=orig_meta.purpose,
                data_license=orig_meta.data_license,
                publication_year=orig_meta.publication_year,
                dataset_version=orig_meta.dataset_version,
                publisher_name=orig_meta.publisher_name,
                publisher_location=orig_meta.publisher_location
            )
            session.add(new_meta)
            session.flush()

            # 3. Re-link Investigators and data submitters (existing Person rows)
            for person in orig_meta.investigators:
                session.add(OadsMetadataInvestigators(
                    oads_metadata_id=new_meta.id,
                    person_id=person.id
                ))
            for person in orig_meta.data_submitter:
                session.add(OadsMetadataDataSubmitter(
                    oads_metadata_id=new_meta.id,
                    person_id=person.id
                ))

            # 4. Clone Related Datasets ### NOT CURRENTLY IN USE, but adding just in case it becomes in use ####
            for rd in (orig_meta.related_datasets or []):
                session.add(RelatedDataset(
                    dataset=rd.dataset,
                    link=rd.link,
                    oads_metadata_id=new_meta.id
                ))

            # 5. Portal specific extension tables
            portal.clone_metadata(session, orig_meta, new_meta)
        
        session.commit()
        return new_id