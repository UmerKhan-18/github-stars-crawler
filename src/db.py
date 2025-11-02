from sqlalchemy import create_engine, Column, String, BigInteger, TIMESTAMP, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Repo(Base):
    __tablename__ = "repos"

    repo_id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    stargazers_count = Column(BigInteger)
    last_crawled = Column(TIMESTAMP, default=datetime.utcnow)
    metadata_json = Column("metadata", JSON, default={})

DATABASE_URL = f"postgresql://{os.getenv('PGUSER', 'postgres')}:{os.getenv('PGPASSWORD', 'postgres')}@{os.getenv('PGHOST', 'localhost')}/{os.getenv('PGDATABASE', 'crawler')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)  

def create_schema():
    Base.metadata.create_all(engine)
