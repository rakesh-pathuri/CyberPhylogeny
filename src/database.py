from sqlalchemy import create_engine, Column, String, Text, ForeignKey, Integer
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from typing import List

Base = declarative_base()

class DBGenome(Base):
    __tablename__ = 'genomes'
    
    id = Column(String, primary_key=True) # e.g., 'G0016'
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Ordered relationship to genes
    genes = relationship("DBGenomeGene", back_populates="genome", order_by="DBGenomeGene.sequence_order", cascade="all, delete-orphan")

class DBGene(Base):
    __tablename__ = 'genes'
    
    id = Column(String, primary_key=True) # e.g., 'T1003'
    name = Column(String, nullable=False)
    tactic = Column(String, nullable=False)
    description = Column(Text)

class DBGenomeGene(Base):
    """Association table with sequence ordering."""
    __tablename__ = 'genome_genes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    genome_id = Column(String, ForeignKey('genomes.id'))
    gene_id = Column(String, ForeignKey('genes.id'))
    sequence_order = Column(Integer, nullable=False) # 0, 1, 2...
    
    genome = relationship("DBGenome", back_populates="genes")
    gene = relationship("DBGene")

def init_db(db_path: str = "sqlite:///genomes.db"):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session()
