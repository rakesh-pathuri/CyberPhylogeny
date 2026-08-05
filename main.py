import argparse
import sys
from rich.console import Console
from rich.table import Table

from src.database import init_db
from src.parser import fetch_mitre_data, parse_mitre_to_genomes
from src.ingest import save_to_db
from src.similarity import SimilarityEngine
from src.prediction import PredictionEngine
from src.evolution import EvolutionEngine

console = Console()

def cmd_ingest():
    engine, session = init_db()
    data = fetch_mitre_data()
    genes, genomes = parse_mitre_to_genomes(data)
    save_to_db(session, genes, genomes)

def cmd_cluster(eps: float, min_samples: int):
    # For this prototype we'll just re-parse in memory instead of DB lookup for simplicity
    data = fetch_mitre_data()
    _, genomes = parse_mitre_to_genomes(data)
    
    sim_engine = SimilarityEngine(genomes)
    f1, f2, f3 = sim_engine.run_multi_stage_pipeline(eps, min_samples)
    
    def print_families(families, stage_name):
        console.print(f"\n[bold]{stage_name} Families[/bold]")
        
        orphans = families.get(-1, [])
        if orphans:
            console.print(f"\n[red]Noise (Unclustered Orphans) - {len(orphans)} attacks[/red]")
            
        for label, family in families.items():
            if label == -1: continue
                
            console.print(f"\n[green]Family {label} - {len(family)} attacks[/green]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Attack / Group ID", style="dim", width=12)
            table.add_column("Name")
            table.add_column("Genome Length")
            
            for g in family:
                table.add_row(g.id, g.name, str(len(g.genes)))
            console.print(table)
            
    print_families(f1, "STAGE 1: Strict Evolutionary (Levenshtein)")
    if f2 and len(f2) > 1: # More than just orphans
        print_families(f2, "STAGE 2: Unordered Motif (Jaccard)")
    if f3 and len(f3) > 1:
        print_families(f3, "STAGE 3: Taxonomic Zooming (Tactics)")

def cmd_evolution(eps: float, min_samples: int, target_family: int):
    """Clusters the attacks, then traces mutations within a specific family."""
    data = fetch_mitre_data()
    _, genomes = parse_mitre_to_genomes(data)
    
    sim_engine = SimilarityEngine(genomes)
    families = sim_engine.cluster_families(eps, min_samples)
    
    if target_family not in families:
        console.print(f"[red]Family {target_family} not found.[/red]")
        return
        
    family_genomes = families[target_family]
    evo_engine = EvolutionEngine(genomes)
    
    console.print(f"\n[bold cyan]Tracing Evolution for Family {target_family} ({len(family_genomes)} attacks)[/bold cyan]")
    
    history = evo_engine.analyze_family_evolution(family_genomes)
    
    for ancestor, descendant, mutations in history:
        console.print(f"\n[bold yellow]Evolution: {ancestor.name} -> {descendant.name}[/bold yellow]")
        if not mutations:
            console.print("[dim]No structural mutations (Identical Genome)[/dim]")
        for m in mutations:
            console.print(f"  - {m}")

def cmd_predict(sequence_str: str, top_k: int = 5):
    """Predicts the next behavior using KNN and Sliding Window Suffix Alignment."""
    data = fetch_mitre_data()
    _, genomes = parse_mitre_to_genomes(data)
    
    seq = [s.strip() for s in sequence_str.split(',')]
    
    console.print(f"\n[bold cyan]Ongoing Attack Sequence:[/bold cyan] {seq}")
    
    engine = PredictionEngine(genomes)
    predictions = engine.predict_next(seq, top_k=top_k)
    
    if not predictions:
        console.print("[yellow]Not enough historical data to predict the next step with confidence.[/yellow]")
        return
        
    console.print("\n[bold]Most Probable Next Behaviors:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Predicted Technique ID", style="dim", width=20)
    table.add_column("Implementation")
    table.add_column("Behavior", style="italic")
    table.add_column("Probability", justify="right")
    table.add_column("Confidence Score", justify="right", style="green")
    
    for gene, prob, confidence in predictions:
        table.add_row(
            gene.technique_id,
            gene.implementation,
            gene.behavior,
            f"{prob*100:.1f}%",
            f"{confidence:.2f}x"
        )
        
    console.print(table)
    console.print("[dim italic]* Confidence Score represents the mathematical similarity of the historical sequence matched (1.0 = perfect suffix alignment).[/dim italic]")

def cmd_tree(eps: float, min_samples: int, target_family: int):
    """Generates a Mermaid.js Phylogenetic Tree for a family."""
    data = fetch_mitre_data()
    _, genomes = parse_mitre_to_genomes(data)
    
    sim_engine = SimilarityEngine(genomes)
    families = sim_engine._cluster_with_metric(genomes, metric_type="levenshtein_genes", eps=eps, min_samples=min_samples)
    
    if target_family not in families:
        console.print(f"[red]Family {target_family} not found in Stage 1.[/red]")
        return
        
    family_genomes = families[target_family]
    evo_engine = EvolutionEngine(genomes)
    
    console.print(f"\n[bold cyan]Phylogenetic Tree for Family {target_family} ({len(family_genomes)} variants)[/bold cyan]")
    
    # 1. Print the rich terminal tree
    terminal_tree = evo_engine.build_terminal_tree(family_genomes)
    console.print(terminal_tree)
    console.print()
    
    # 2. Generate the PyVis/Mermaid files in the background
    evo_engine.build_phylogenetic_tree(family_genomes)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CyberPhylogeny Framework CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # Ingest command
    subparsers.add_parser("ingest", help="Fetch MITRE CTI data and populate database")
    
    # Cluster command
    cluster_parser = subparsers.add_parser("cluster", help="Cluster attacks into structural families")
    cluster_parser.add_argument("--eps", type=float, default=0.25, help="DBSCAN epsilon distance (0.0 to 1.0)")
    cluster_parser.add_argument("--min_samples", type=int, default=2, help="DBSCAN min samples")
    
    # Evolution command
    evo_parser = subparsers.add_parser("evolution", help="Trace mutations within a specific attack family")
    evo_parser.add_argument("--eps", type=float, default=0.6, help="DBSCAN epsilon distance (0.0 to 1.0)")
    evo_parser.add_argument("--min_samples", type=int, default=2, help="DBSCAN min samples")
    evo_parser.add_argument("family", type=int, help="The ID of the family to trace (e.g. 1)")
    
    # Tree command
    tree_parser = subparsers.add_parser("tree", help="Generate a Phylogenetic Tree (Mermaid graph) for a family")
    tree_parser.add_argument("--eps", type=float, default=0.6, help="DBSCAN epsilon distance (0.0 to 1.0)")
    tree_parser.add_argument("--min_samples", type=int, default=2, help="DBSCAN min samples")
    tree_parser.add_argument("family", type=int, help="The ID of the family to visualize (e.g. 15)")
    
    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Predict next behavior using KNN Sequence Alignment")
    predict_parser.add_argument("sequence", type=str, help="Comma separated list of Gene IDs e.g. T1190,T1003")
    predict_parser.add_argument("--k", type=int, default=5, help="Number of nearest neighbors to calculate against")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        cmd_ingest()
    elif args.command == "cluster":
        cmd_cluster(args.eps, args.min_samples)
    elif args.command == "evolution":
        cmd_evolution(args.eps, args.min_samples, args.family)
    elif args.command == "tree":
        cmd_tree(args.eps, args.min_samples, args.family)
    elif args.command == "predict":
        cmd_predict(args.sequence, args.k)
    else:
        parser.print_help()
        sys.exit(1)
