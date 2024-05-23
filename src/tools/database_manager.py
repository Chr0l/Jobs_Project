import json
import os
import sys
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from tools.logging_manager import LoggingManager
from utils.orm_base import Base

class DatabaseManager:
    def __init__(self):
        db_url = json.loads(os.getenv("DATABASE_CONFIG"))["url"]
        if not db_url:
            raise ValueError("URL_BD not found in environment variables.")
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.logger = LoggingManager(logger_name="DatabaseManager").get_logger()

    @contextmanager
    def session_scope(self):
        """Manages the database session scope."""
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
        """Creates all tables if they do not exist."""
        self.logger.info("Creating tables...")
        Base.metadata.create_all(bind=self.engine)

    def add_entry(self, entry, table_class):
        """Adds a new entry to the database."""
        with self.session_scope() as session:
            session.add(entry)
            self.logger.info(f"Added entry to {table_class.__tablename__}")

    def get_entries(self, table_class, conditions=None):
        """Gets table entries based on optional conditions."""
        with self.session_scope() as session:
            query = session.query(table_class)
            if conditions:
                query = query.filter_by(**conditions)
            entries = query.all()
            self.logger.info(
                f"Retrieved {len(entries)} entries from {table_class.__tablename__}"
            )
            return entries

    def update_entry(self, table_class, entry_id, updated_data):
        """Updates an entry in the database."""
        with self.session_scope() as session:
            entry = session.query(table_class).get(entry_id)
            if entry:
                try:
                    for key, value in updated_data.items():
                        setattr(entry, key, value)
                    self.logger.info(f"Updated entry in {table_class.__tablename__}")
                except IntegrityError as e:
                    self.logger.error(f"Integrity error updating entry: {e}")
            else:
                self.logger.warning(
                    f"Entry with id {entry_id} not found in {table_class.__tablename__}."
                )

    def delete_entry(self, table_class, entry_id):
        """Deletes an entry from the database."""
        with self.session_scope() as session:
            entry = session.query(table_class).get(entry_id)
            if entry:
                session.delete(entry)
                self.logger.info(f"Deleted entry from {table_class.__tablename__}")
            else:
                self.logger.warning(
                    f"Entry with id {entry_id} not found in {table_class.__tablename__}."
                )
