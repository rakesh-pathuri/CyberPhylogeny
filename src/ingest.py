from sqlalchemy.orm import Session
from typing import List, Tuple
from datetime import datetime
from rich.console import Console

from .models import Gene, Genome
from .database import DBGene, DBGenome, DBGenomeGene

console = Console()

def save_to_db(session: Session, genes: List[Gene], genomes: List[Genome]):
    """Saves parsed Genes and Genomes into the SQLite database."""
    console.print(f"[cyan]Saving {len(genes)} Genes and {len(genomes)} Genomes to DB...[/cyan]")
    
    # Insert Genes
    for g in genes:
        gene_id = f"{g.source_technique_id}->{g.target_technique_id}"
        db_gene = session.query(DBGene).filter_by(id=gene_id).first()
        if not db_gene:
            db_gene = DBGene(
                id=gene_id, 
                source_technique_id=g.source_technique_id,
                target_technique_id=g.target_technique_id,
                source_implementation=g.source_implementation,
                target_implementation=g.target_implementation,
                source_tactic=g.source_tactic,
                target_tactic=g.target_tactic
            )
            session.add(db_gene)
    
    session.commit()
    
    # Insert Genomes
    for gnm in genomes:
        db_genome = session.query(DBGenome).filter_by(id=gnm.id).first()
        if not db_genome:
            db_genome = DBGenome(
                id=gnm.id, 
                name=gnm.name, 
                description=gnm.description,
                created=gnm.created.isoformat()
            )
            session.add(db_genome)
            
            # Insert sequence
            for idx, gene in enumerate(gnm.genes):
                db_link = DBGenomeGene(
                    genome_id=gnm.id,
                    gene_id=f"{gene.source_technique_id}->{gene.target_technique_id}",
                    sequence_order=idx
                )
                session.add(db_link)
    
    session.commit()
    console.print("[green]Successfully populated database![/green]")

def load_from_db(session: Session) -> Tuple[List[Gene], List[Genome]]:
    """Loads parsed Genes and Genomes from the SQLite database."""
    db_genomes = session.query(DBGenome).all()
    if not db_genomes:
        return [], []
        
    genomes = []
    all_genes = []
    
    with console.status(f"[cyan]Loading {len(db_genomes)} Genomes from local DB cache...[/cyan]", spinner="dots"):
        # Load all genes to cache
        db_genes = session.query(DBGene).all()
        gene_map = {}
        for dbg in db_genes:
            g = Gene(
                source_technique_id=dbg.source_technique_id,
                target_technique_id=dbg.target_technique_id,
                source_implementation=dbg.source_implementation,
                target_implementation=dbg.target_implementation,
                source_tactic=dbg.source_tactic,
                target_tactic=dbg.target_tactic
            )
            gene_map[dbg.id] = g
            all_genes.append(g)
            
        for dbg in db_genomes:
            # DBGenomeGene automatically orders by sequence_order
            sequence = []
            for link in dbg.genes:
                sequence.append(gene_map[link.gene_id])
                
            genome = Genome(
                id=dbg.id,
                name=dbg.name,
                created=datetime.fromisoformat(dbg.created) if dbg.created else datetime.now()
            )
            genome.description = dbg.description
            genome.genes = sequence
            genome.family_id = dbg.family_id
            genome.stage = dbg.stage
            genomes.append(genome)
        
    return all_genes, genomes

def update_genome_families(session: Session, genomes: List[Genome]):
    """Updates the family_id and stage of the given genomes in the DB."""
    for gnm in genomes:
        db_genome = session.query(DBGenome).filter_by(id=gnm.id).first()
        if db_genome:
            db_genome.family_id = gnm.family_id
            db_genome.stage = gnm.stage
    session.commit()

