import argparse
import sys
import os
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
    table.add_column("Behavior")
    table.add_column("Tactic", style="italic")
    table.add_column("Probability", justify="right")
    table.add_column("Confidence Score", justify="right", style="green")
    
    for gene, prob, confidence in predictions:
        table.add_row(
            gene.technique_id,
            gene.implementation,
            gene.behavior,
            gene.tactic,
            f"{prob*100:.1f}%",
            f"{confidence:.2f}x"
        )
        
    console.print(table)
    console.print("[dim italic]* Confidence Score represents the mathematical similarity of the historical sequence matched (1.0 = perfect suffix alignment).[/dim italic]")

def cmd_genome(attack_id: str):
    """Displays the genome sequence for a specific attack ID."""
    data = fetch_mitre_data()
    _, genomes = parse_mitre_to_genomes(data)
    
    # Allow case-insensitive search
    target = next((g for g in genomes if g.id.lower() == attack_id.lower()), None)
    if not target:
        console.print(f"[red]Attack ID '{attack_id}' not found in the Threat Database.[/red]")
        return
        
    console.print(f"\n[bold cyan]Genome Profile: {target.name} ({target.id})[/bold cyan]")
    if target.description:
        desc = target.description.split("\n")[0] # Just the first line/sentence
        desc = desc[:200] + "..." if len(desc) > 200 else desc
        console.print(f"[dim]{desc}[/dim]\n")
        
    console.print(f"[bold]Genetic Sequence ({len(target.genes)} Genes)[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Index", style="dim", width=5)
    table.add_column("Technique ID", style="dim", width=15)
    table.add_column("Implementation")
    table.add_column("Behavior")
    table.add_column("Tactic", style="italic")
    
    for i, gene in enumerate(target.genes, 1):
        table.add_row(
            str(i),
            gene.technique_id,
            gene.implementation,
            gene.behavior,
            gene.tactic
        )
        
    console.print(table)

def cmd_tree(eps: float, min_samples: int, target_family: int, algo: str):
    """Generates a Phylogenetic Tree for a family."""
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
    console.print(f"[dim]Algorithm: {algo.upper()}[/dim]")
    
    if algo.lower() == "upgma":
        tree = evo_engine.build_upgma_tree(family_genomes)
        console.print(tree)
    else:
        tree = evo_engine.build_terminal_tree(family_genomes)
        console.print(tree)

def cmd_diff(ancestor_id: str, descendant_id: str):
    """Shows tactic-grouped mutations between two attacks (like git diff)."""
    data = fetch_mitre_data()
    _, genomes = parse_mitre_to_genomes(data)
    
    ancestor = next((g for g in genomes if g.id.lower() == ancestor_id.lower()), None)
    descendant = next((g for g in genomes if g.id.lower() == descendant_id.lower()), None)
    
    if not ancestor:
        console.print(f"[red]Ancestor ID '{ancestor_id}' not found.[/red]")
        return
    if not descendant:
        console.print(f"[red]Descendant ID '{descendant_id}' not found.[/red]")
        return
        
    evo_engine = EvolutionEngine(genomes)
    grouped_mutations, score = evo_engine.get_tactic_grouped_mutations(ancestor, descendant)
    
    console.print(f"\n[bold cyan]Attack : {descendant.id} ({descendant.name})[/bold cyan]")
    console.print(f"[bold red]Mutation Score : {score}[/bold red]\n")
    console.print("[bold]Mutations[/bold]")
    
    if not grouped_mutations:
        console.print("[dim]No structural mutations (Identical Genome)[/dim]")
        return
        
    for tactic, ops in grouped_mutations.items():
        console.print(f"\n[bold magenta]{tactic.title()}[/bold magenta]")
        console.print("--------------")
        for op in ops:
            console.print(op + "\n")

def cmd_lineage(attack_id: str):
    """Traces the evolutionary chain of a specific attack back to its root."""
    data = fetch_mitre_data()
    _, genomes = parse_mitre_to_genomes(data)
    
    target = next((g for g in genomes if g.id.lower() == attack_id.lower()), None)
    if not target:
        console.print(f"[red]Attack ID '{attack_id}' not found.[/red]")
        return
        
    sim_engine = SimilarityEngine(genomes)
    # We must cluster to find its family and the MST path
    families = sim_engine._cluster_with_metric(genomes, metric_type="levenshtein_genes", eps=0.6, min_samples=2)
    
    target_family = None
    for label, family in families.items():
        if target in family:
            target_family = family
            break
            
    if not target_family:
        console.print(f"[red]Attack ID '{attack_id}' is an orphan (not in any evolutionary family).[/red]")
        return
        
    # Rebuild MST logic to find path
    n = len(target_family)
    import numpy as np
    from src.similarity import sequence_alignment_distance
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1, n):
            d = sequence_alignment_distance(target_family[i].genes, target_family[j].genes, is_tactic=False)
            dist_matrix[i][j] = dist_matrix[j][i] = d
            
    root_idx = min(range(n), key=lambda idx: target_family[idx].created)
    target_idx = target_family.index(target)
    
    visited = {root_idx}
    children = {i: [] for i in range(n)}
    parents = {root_idx: None}
    
    while len(visited) < n:
        min_dist = float('inf')
        best_edge = None
        for u in visited:
            for v in range(n):
                if v not in visited and dist_matrix[u][v] < min_dist:
                    min_dist = dist_matrix[u][v]
                    best_edge = (u, v)
        if best_edge:
            u, v = best_edge
            visited.add(v)
            children[u].append(v)
            parents[v] = u
            
    # Trace path back from target to root
    path = []
    curr = target_idx
    while curr is not None:
        path.append(target_family[curr])
        curr = parents.get(curr)
        
    path.reverse()
    
    from rich.tree import Tree
    console.print(f"\n[bold cyan]Lineage for {target.id}[/bold cyan]")
    
    if len(path) == 1:
        console.print(f"[bold cyan]Root: {target.id} ({target.name})[/bold cyan]")
        return
        
    lineage_tree = Tree(f"[bold cyan]Root: {path[0].id} ({path[0].name})[/bold cyan]")
    curr_branch = lineage_tree
    
    for i in range(1, len(path)):
        node = path[i]
        label = f"[bold magenta]{node.id} ({node.name})[/bold magenta]"
        curr_branch = curr_branch.add(label)
        
    console.print(lineage_tree)
    



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CyberPhylogeny Framework CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # 1. Ingest
    parser_ingest = subparsers.add_parser("ingest", help="Ingest MITRE STIX data into Genome DB")
    
    # 2. Genome Profile
    parser_genome = subparsers.add_parser("genome", help="View the genetic sequence of a specific attack")
    parser_genome.add_argument("attack_id", type=str, help="Attack ID (e.g., 'S0039')")
    
    # 3. Cluster
    parser_cluster = subparsers.add_parser("cluster", help="Cluster attacks into Evolutionary Families")
    parser_cluster.add_argument("--eps", type=float, default=0.6, help="DBSCAN epsilon distance (0.0 to 1.0)")
    parser_cluster.add_argument("--min_samples", type=int, default=2, help="Minimum attacks to form a family")
    
    # 4. Tree
    parser_tree = subparsers.add_parser("tree", help="Build a Phylogenetic Tree for a specific family")
    parser_tree.add_argument("family", type=str, help="Family ID to trace (e.g., '24')")
    parser_tree.add_argument("--algo", type=str, default="mst", choices=["mst", "upgma"], help="Algorithm to build tree (mst or upgma)")
    parser_tree.add_argument("--eps", type=float, default=0.6, help="DBSCAN epsilon used for clustering")
    parser_tree.add_argument("--min_samples", type=int, default=2, help="Minimum samples used for clustering")
    
    # 5. Predict
    parser_predict = subparsers.add_parser("predict", help="Predict next steps of an ongoing attack")
    parser_predict.add_argument("sequence", type=str, help="Comma-separated list of Technique IDs (e.g., 'T1566.001,T1059.001')")
    parser_predict.add_argument("--k", type=int, default=3, help="Number of nearest neighbors to consider")
    
    # 6. Diff
    parser_diff = subparsers.add_parser("diff", help="Show tactic-grouped mutations between two attacks")
    parser_diff.add_argument("ancestor", type=str, help="Ancestor Attack ID (e.g., 'S0347')")
    parser_diff.add_argument("descendant", type=str, help="Descendant Attack ID (e.g., 'S0527')")
    
    # 7. Lineage
    parser_lineage = subparsers.add_parser("lineage", help="Trace the evolutionary chain of a specific attack")
    parser_lineage.add_argument("attack_id", type=str, help="Target Attack ID (e.g., 'S0527')")

    args = parser.parse_args()
    
    if args.command == "ingest":
        cmd_ingest()
    elif args.command == "genome":
        cmd_genome(args.attack_id)
    elif args.command == "cluster":
        cmd_cluster(args.eps, args.min_samples)
    elif args.command == "tree":
        cmd_tree(args.eps, args.min_samples, int(args.family), args.algo)
    elif args.command == "predict":
        cmd_predict(args.sequence, args.k)
    elif args.command == "diff":
        cmd_diff(args.ancestor, args.descendant)
    elif args.command == "lineage":
        cmd_lineage(args.attack_id)

    else:
        parser.print_help()
        sys.exit(1)
