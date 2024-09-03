import os

from sqlalchemy import create_engine, Column, Integer, Text, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")  # Example: "postgresql://user:password@localhost/dbname"

Base = declarative_base()


class BroadcastModel(Base):
    __tablename__ = 'loopai_broadcast'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sessionid = Column(Text, nullable=False)
    stepid = Column(Text, nullable=False)
    modelid = Column(Text, nullable=False)
    request = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())


# Set up the database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine)


# Dependency to get a session
def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
