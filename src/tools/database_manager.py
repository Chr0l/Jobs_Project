from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .logging_manager import LoggingManager
from ..utils.orm_base import Base, JobsBaseInfo

class DatabaseManager:
    def __init__(self, db_url="sqlite:///data/db.sqlite"):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.logger = LoggingManager(logger_name='DatabaseManager').get_logger()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        self.logger.debug("Opened database session")
        try:
            yield session
            session.commit()
            self.logger.debug("Committed database session")
        except Exception as e:
            session.rollback()
            self.logger.error(f"Rolled back database session due to error: {e}")
            raise
        finally:
            session.close()
            self.logger.debug("Closed database session")

    def create_tables(self):
        """Create all tables if they don't exist."""
        self.logger.info("Creating tables...")
        Base.metadata.create_all(bind=self.engine)

    def add_job(self, job_data):
        """Add a new job to the database."""
        with self.session_scope() as session:
            new_job = JobsBaseInfo(**job_data)
            session.add(new_job)
            self.logger.info(f"Added job: {new_job.title} ({new_job.company})")

    def get_unprocessed_jobs(self):
        """Get all unprocessed jobs."""
        with self.session_scope() as session:
            jobs = session.query(JobsBaseInfo).filter_by(processed=False).all()
            self.logger.info(f"Retrieved {len(jobs)} unprocessed jobs")
            return jobs

    def update_job(self, job_id, updated_data):
        """Update a job in the database."""
        with self.session_scope() as session:
            job = session.query(JobsBaseInfo).get(job_id)
            if job:
                for key, value in updated_data.items():
                    setattr(job, key, value)
                self.logger.info(f"Updated job: {job.title} ({job.company})")
            else:
                self.logger.warning(f"Job with id {job_id} not found.")
