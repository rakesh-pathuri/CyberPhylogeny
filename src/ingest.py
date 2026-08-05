from sqlalchemy.orm import Session
from typing import List
from rich.console import Console

from .models import Gene, Genome
from .database import DBGene, DBGenome, DBGenomeGene

console = Console()

def save_to_db(session: Session, genes: List[Gene], genomes: List[Genome]):
    """Saves parsed Genes and Genomes into the SQLite database."""
    console.print(f"[cyan]Saving {len(genes)} Genes and {len(genomes)} Genomes to DB...[/cyan]")
    
    # Insert Genes
    for g in genes:
        db_gene = session.query(DBGene).filter_by(id=g.id).first()
        if not db_gene:
            db_gene = DBGene(id=g.id, name=g.name, tactic=g.tactic, description=g.description)
            session.add(db_gene)
    
    session.commit()
    
    # Insert Genomes
    for gnm in genomes:
        db_genome = session.query(DBGenome).filter_by(id=gnm.id).first()
        if not db_genome:
            db_genome = DBGenome(id=gnm.id, name=gnm.name, description=gnm.description)
            session.add(db_genome)
            
            # Insert sequence
            for idx, gene in enumerate(gnm.genes):
                db_link = DBGenomeGene(
                    genome_id=gnm.id,
                    gene_id=gene.id,
                    sequence_order=idx
                )
                session.add(db_link)
    
    session.commit()
    console.print("[green]Successfully populated database![/green]")
