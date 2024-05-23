import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, LargeBinary, JSON, Index
from sqlalchemy.orm import declarative_base, relationship
from cryptography.fernet import Fernet

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from tools.logging_manager import LoggingManager

Base = declarative_base()
logger = LoggingManager(logger_name='ORMbase').get_logger()

load_dotenv()
cipher_suite = Fernet(json.loads(os.getenv("SECRET_KEY"))["key"])

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index('idx_email', 'email', unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    additional_info = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    accounts = relationship("Account", back_populates="user")

    def set_password(self, password):
        """
        Encrypts the password using the secret key.
        """
        self.password_hash = cipher_suite.encrypt(password.encode()).decode()

    def check_password(self, password):
        """
        Checks whether the provided password matches the encrypted password.
        """
        if self.password_hash:
            try:
                decrypted_password = cipher_suite.decrypt(self.password_hash.encode()).decode()
                return decrypted_password == password
            except Exception as e:
                logger.error(f"Error decrypting password: {e}")
                return False
        else:
            logger.warning("Password hash is empty")
            return False


    def decrypt_password(self):
        """
        Decrypts the password using the secret key.
        """
        if self.password_hash:
            try:
                decrypted_password = cipher_suite.decrypt(self.password_hash).decode()
                return decrypted_password
            except Exception as e:
                logger.error(f"Error decrypting password: {e}")
                return None
        else:
            logger.warning("Password hash is empty")
            return None


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        Index('idx_platform', 'platform'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String, nullable=False, index=True)
    cookies = Column(LargeBinary)
    status = Column(Boolean, default=True)
    user = relationship("User", back_populates="accounts")


class JobsBaseInfo(Base):
    __tablename__ = "jobs_base_info"
    __table_args__ = (
        Index('idx_company', 'company'),
        Index('idx_location', 'location'),
        Index('idx_work_format', 'work_format'),
    )

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False, index=True)
    work_format = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False, unique=True)
    processed = Column(Boolean, default=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    processing_date = Column(DateTime)
