# database.py
from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite local database creation
engine = create_engine("sqlite:///finance.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, index=True)
    date = Column(DateTime)
    description = Column(String)
    counterparty = Column(String)
    amount = Column(Float)
    method = Column(String)
    
    # AI assigned category
    category = Column(String, nullable=True) 
    needs_review = Column(Boolean, default=False)

# Create the tables
Base.metadata.create_all(bind=engine)