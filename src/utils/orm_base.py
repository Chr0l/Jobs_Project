from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class JobsBaseInfo(Base):
    __tablename__ = "jobs_base_info"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    processed = Column(Boolean, default=False)
    description = Column(Text)  # Adicionando coluna para descrição
    registration_date = Column(DateTime, default=datetime.utcnow)
    processing_date = Column(DateTime)
