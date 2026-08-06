import argparse
import sys
import os
from rich.console import Console
from rich.table import Table

from src.database import init_db
from src.parser import fetch_mitre_data, parse_mitre_to_genomes
from src.ingest import save_to_db, load_from_db
from src.similarity import SimilarityEngine
from src.prediction import PredictionEngine
from src.evolution import EvolutionEngine

console = Console()

def get_cached_genomes():
    engine, session = init_db()
    
    # Try to load from DB
    _, genomes = load_from_db(session)
    
    # If empty, fetch from web and parse
    if not genomes:
        data = fetch_mitre_data()
        genes, genomes = parse_mitre_to_genomes(data)
        save_to_db(session, genes, genomes)
        
    return genomes

def cmd_ingest():
    console.print("[yellow]The 'ingest' command is deprecated. The system now automatically caches genomes on first run.[/yellow]")

def cmd_clean():
    """Deletes the local SQLite cache."""
    if os.path.exists("genomes.db"):
        os.remove("genomes.db")
        console.print("[green]Successfully deleted local cache (genomes.db).[/green]")
    else:
        console.print("[dim]Cache does not exist. Nothing to clean.[/dim]")


def cmd_cluster(eps: float, min_samples: int, eps_s3: float = 0.65):
    genomes = get_cached_genomes()
    
    sim_engine = SimilarityEngine(genomes)
    f1, f2, f3, f4, score_s1 = sim_engine.run_multi_stage_pipeline(eps, min_samples, eps_s3)
    
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
            
    print_families(f1, "STAGE 1: Evolutionary Ancestry (Weighted Sequence Alignment)")
    if len(f2) > 1 or (len(f2) == 1 and -1 not in f2):
        print_families(f2, "STAGE 2: Unordered Motif (Jaccard)")
    if len(f3) > 1 or (len(f3) == 1 and -1 not in f3):
        print_families(f3, "STAGE 3: Taxonomic Zooming (Tactics)")
    if len(f4) > 1 or (len(f4) == 1 and -1 not in f4):
        print_families(f4, "STAGE 4: Taxonomic Motif (Jaccard)")
        
    num_fams = sum(len(f)-1 for f in [f1, f2, f3, f4] if -1 in f) + sum(len(f) for f in [f1, f2, f3, f4] if -1 not in f)
    import numpy as np
    largest_family = max([len(v) for f in [f1, f2, f3, f4] for k,v in f.items() if k != -1], default=0)
    median_size = int(np.median([len(v) for f in [f1, f2, f3, f4] for k,v in f.items() if k != -1])) if num_fams > 0 else 0
    
    # Extract final noise from f4
    final_noise = len(f4.get(-1, []))
    
    console.print(f"\n[bold cyan]Clustering Summary[/bold cyan]")
    console.print(f"Attacks analyzed : {len(genomes)}")
    console.print(f"Families found   : {num_fams} (Across all stages)")
    console.print(f"Largest family   : {largest_family}")
    console.print(f"Median family size: {median_size}")
    console.print(f"Final Noise      : {final_noise}")
    console.print(f"Stage 1 Silhouette: {score_s1:.2f}\n")
    
    # Save assignments to database
    console.print("[cyan]Saving cluster assignments to database...[/cyan]")
    for stage_idx, families in enumerate([f1, f2, f3, f4], 1):
        for label, g_list in families.items():
            if label == -1: continue
            for g in g_list:
                g.family_id = str(label)
                g.stage = stage_idx
                
    # Handle final orphans
    for g in f4.get(-1, []):
        g.family_id = "-1"
        g.stage = -1
        
    from src.database import init_db
    from src.ingest import update_genome_families
    _, session = init_db()
    update_genome_families(session, genomes)
    console.print("[green]Cluster cache updated.[/green]")

def cmd_evolution(eps: float, min_samples: int, target_family: int):
    """Clusters the attacks, then traces mutations within a specific family."""
    genomes = get_cached_genomes()
    
    sim_engine = SimilarityEngine(genomes)
    families, _ = sim_engine._cluster_with_metric(genomes, metric_type="alignment_genes", eps=eps, min_samples=min_samples)
    
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
    genomes = get_cached_genomes()
    
    seq = [s.strip() for s in sequence_str.split(',')]
    
    if len(seq) < 2:
        console.print("[yellow]Please provide at least 2 techniques to form a transition sequence.[/yellow]")
        return
        
    transitions = []
    for i in range(len(seq) - 1):
        transitions.append(f"{seq[i]}->{seq[i+1]}")
    
    console.print(f"\n[bold cyan]Ongoing Attack Sequence (Transitions):[/bold cyan] {transitions}")
    
    engine = PredictionEngine(genomes)
    predictions = engine.predict_next(transitions, top_k=top_k)
    
    if not predictions:
        console.print("[yellow]Not enough historical data to predict the next step with confidence.[/yellow]")
        return
        
    console.print("\n[bold]Most Probable Next Behaviors:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Predicted Transition", style="dim", width=25)
    table.add_column("Implementation Transition")
    table.add_column("Tactical Flow", style="italic")
    table.add_column("Probability", justify="right")
    table.add_column("Confidence Score", justify="right", style="green")
    
    for gene, prob, confidence in predictions:
        table.add_row(
            f"{gene.source_technique_id}->{gene.target_technique_id}",
            f"{gene.source_implementation} -> {gene.target_implementation}",
            f"{gene.source_tactic}->{gene.target_tactic}",
            f"{prob*100:.1f}%",
            f"{confidence:.2f}x"
        )
        
    console.print(table)
    console.print("[dim italic]* Confidence Score represents the mathematical similarity of the historical sequence matched (1.0 = perfect suffix alignment).[/dim italic]")

def cmd_genome(attack_id: str):
    """Displays the genome sequence for a specific attack ID."""
    genomes = get_cached_genomes()
    
    target = next((g for g in genomes if g.id.lower() == attack_id.lower()), None)
    if not target:
        console.print(f"[red]Attack ID '{attack_id}' not found in the Threat Database.[/red]")
        return
        
    console.print(f"\n[bold cyan]Attack Genome : {target.name} ({target.id})[/bold cyan]\n")
    
    from rich.tree import Tree
    
    # Group genes by source_tactic
    tactics = {}
    for gene in target.genes:
        tactics.setdefault(gene.source_tactic, []).append(gene)
        
    for i, (tactic, genes) in enumerate(tactics.items()):
        tactic_node = Tree(f"[bold magenta]{tactic.title()}[/bold magenta]")
        for gene in genes:
            tactic_node.add(f"[cyan]{gene.source_implementation} -> {gene.target_implementation}[/cyan] [dim](-> {gene.target_tactic})[/dim]")
        console.print(tactic_node)
        if i < len(tactics) - 1:
            console.print()
            
    console.print(f"\n[bold]Genome Size[/bold] : {len(target.genes)} Genes")
    
    # Check cache for family
    family_id = target.family_id
    stage = target.stage
    
    if not family_id:
        console.print("\n[yellow]Clustering cache not found. Please run 'python main.py cluster' first.[/yellow]")
        return
        
    if str(family_id) == "-1":
        console.print("[bold yellow]Status[/bold yellow] : Orphan (No Evolutionary Ancestry Found)")
        return
        
    target_family = [g for g in genomes if str(g.family_id) == str(family_id) and str(g.stage) == str(stage)]
    
    if target_family and str(family_id) != "-1":
        n = len(target_family)
        import numpy as np
        from src.similarity import sequence_alignment_distance
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                d = sequence_alignment_distance(target_family[i].genes, target_family[j].genes, is_string_match=False)
                dist_matrix[i][j] = dist_matrix[j][i] = d
                
        root_idx = min(range(n), key=lambda idx: target_family[idx].created)
        target_idx = target_family.index(target)
        
        visited = {root_idx}
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
                parents[v] = u
                
        # Find path to calculate generation and parent distance
        path = []
        curr = target_idx
        while curr is not None:
            path.append(target_family[curr])
            curr = parents.get(curr)
            
        generation = len(path)
        
        if generation > 1:
            parent_idx = target_family.index(path[1]) # path is reversed, so path[1] is parent
            mutation_index = dist_matrix[parent_idx][target_idx]
            console.print(f"[bold]Mutation Index[/bold] : {mutation_index:.1f}")
            
        console.print(f"[bold]Family[/bold] : {family_id} (Stage {stage})")
        console.print(f"[bold]Generation[/bold] : {generation}")

def cmd_tree(target_family: int, algo: str):
    """Generates a Phylogenetic Tree for a family."""
    genomes = get_cached_genomes()
    
    family_genomes = [g for g in genomes if str(g.family_id) == str(target_family)]
    
    if not family_genomes:
        console.print(f"[red]Family {target_family} not found in cache. Run 'python main.py cluster' first.[/red]")
        return
        
    if str(target_family) == "-1":
        console.print("[red]Cannot generate a phylogenetic tree for the Noise/Orphan cluster (-1).[/red]")
        return
        
    with console.status(f"[cyan]Calculating Evolutionary Tree for Family {target_family}...[/cyan]", spinner="dots"):
        evo_engine = EvolutionEngine(genomes)
        
        # Grab the stage from the first genome to display in the header
        stage = family_genomes[0].stage
        
        if algo.lower() == "upgma":
            tree = evo_engine.build_upgma_tree(family_genomes)
        else:
            tree = evo_engine.build_terminal_tree(family_genomes)
            
    console.print(f"\n[bold cyan]Phylogenetic Tree for Family {target_family} (Stage {stage}) ({len(family_genomes)} variants)[/bold cyan]")
    console.print(f"[dim]Algorithm: {algo.upper()}[/dim]")
    console.print(tree)

def cmd_diff(ancestor_id: str, descendant_id: str):
    """Shows tactic-grouped mutations between two attacks (like git diff)."""
    genomes = get_cached_genomes()
    
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
    console.print(f"[bold red]Mutation Distance : {score}[/bold red]\n")
    console.print("[bold]Mutations[/bold]")
    
    if not grouped_mutations:
        console.print("[dim]No structural mutations (Identical Genome)[/dim]")
        return
        
    for tactic, ops in grouped_mutations.items():
        console.print(f"\n[bold magenta]\\[{tactic.title()}][/bold magenta]")
        for op in ops:
            console.print("  " + op)

def cmd_ancestry(attack_id: str):
    """Traces the evolutionary ancestry of a specific attack back to its root."""
    genomes = get_cached_genomes()
    
    target = next((g for g in genomes if g.id.lower() == attack_id.lower()), None)
    if not target:
        console.print(f"[red]Attack ID '{attack_id}' not found.[/red]")
        return
        
    family_id = target.family_id
    
    if not family_id:
        console.print(f"\n[yellow]Clustering cache not found. Please run 'python main.py cluster' first.[/yellow]")
        return
        
    if str(family_id) == "-1":
        console.print(f"[red]Attack ID '{attack_id}' is an orphan (not in any evolutionary family).[/red]")
        return
        
    target_family = [g for g in genomes if str(g.family_id) == str(family_id)]
    
    if not target_family:
        console.print(f"[red]Attack ID '{attack_id}' family '{family_id}' not found in cache.[/red]")
        return
        
    n = len(target_family)
    with console.status(f"[cyan]Tracing evolutionary ancestry for {target.name}...[/cyan]", spinner="dots"):
        import numpy as np
        from src.similarity import sequence_alignment_distance
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                d = sequence_alignment_distance(target_family[i].genes, target_family[j].genes, is_string_match=False)
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
                
        path = []
        curr = target_idx
        while curr is not None:
            path.append(target_family[curr])
            curr = parents.get(curr)
            
        path.reverse()
    
    console.print(f"\n[bold cyan]Ancestry for {target.id}[/bold cyan]")
    
    root_label = path[0].get_behavioral_label()
    console.print(f"[bold cyan]{path[0].id} ({path[0].name})[/bold cyan] [dim][{root_label}][/dim]")
    
    for i in range(1, len(path)):
        node = path[i]
        parent_idx_in_family = target_family.index(path[i-1])
        node_idx_in_family = target_family.index(node)
        d = dist_matrix[parent_idx_in_family][node_idx_in_family]
        
        console.print(f"[dim]  | (distance = {d:.2f})[/dim]")
        console.print("[dim]  v[/dim]")
        label = node.get_behavioral_label()
        console.print(f"[bold magenta]{node.id} ({node.name})[/bold magenta] [dim][{label}][/dim]")
        
    console.print("\n[dim italic]* Ancestry inferred via Maximum Parsimony (Minimum Spanning Tree)[/dim italic]\n")
    



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CyberPhylogeny Framework CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # 1. Ingest
    parser_ingest = subparsers.add_parser("ingest", help="Ingest MITRE STIX data into Genome DB")
    
    # 2. Genome Profile
    parser_genome = subparsers.add_parser("genome", help="View the genetic sequence of a specific attack")
    parser_genome.add_argument("attack_id", type=str, help="Attack ID (e.g., 'S0039')")
    
    # 3. Cluster
    parser_cluster = subparsers.add_parser("cluster", help="Run multi-stage phylogenetic clustering")
    parser_cluster.add_argument("--eps", type=float, default=0.45, help="DBSCAN epsilon threshold for Stages 1 & 2 (default: 0.45)")
    parser_cluster.add_argument("--eps3", type=float, default=0.65, help="DBSCAN epsilon threshold for Stage 3 Taxonomic Zooming (default: 0.65)")
    parser_cluster.add_argument("--min_samples", type=int, default=2, help="DBSCAN min_samples threshold (default: 2)")
    
    # 4. Tree
    parser_tree = subparsers.add_parser("tree", help="Build a Phylogenetic Tree for a specific family")
    parser_tree.add_argument("family", type=str, help="Family ID to trace (e.g., '24')")
    parser_tree.add_argument("--algo", type=str, default="mst", choices=["mst", "upgma"], help="Algorithm to build tree (mst or upgma)")
    
    # 5. Predict
    parser_predict = subparsers.add_parser("predict", help="Predict next steps of an ongoing attack")
    parser_predict.add_argument("sequence", type=str, help="Comma-separated list of Technique IDs (e.g., 'T1566.001,T1059.001')")
    parser_predict.add_argument("--k", type=int, default=3, help="Number of nearest neighbors to consider")
    
    # 6. Diff
    parser_diff = subparsers.add_parser("diff", help="Show tactic-grouped mutations between two attacks")
    parser_diff.add_argument("ancestor", type=str, help="Ancestor Attack ID (e.g., 'S0347')")
    parser_diff.add_argument("descendant", type=str, help="Descendant Attack ID (e.g., 'S0527')")
    
    # 7. Ancestry
    parser_ancestry = subparsers.add_parser("ancestry", help="Trace the evolutionary ancestry of a specific attack")
    parser_ancestry.add_argument("attack_id", help="The attack ID to trace (e.g. 'S0697')")
    
    # clean command
    parser_clean = subparsers.add_parser("clean", help="Resets the local database cache")

    args = parser.parse_args()
    
    if args.command == "ingest":
        cmd_ingest()
    elif args.command == "cluster":
        cmd_cluster(args.eps, args.min_samples, args.eps3)
    elif args.command == "genome":
        cmd_genome(args.attack_id)
    elif args.command == "tree":
        cmd_tree(int(args.family), args.algo)
    elif args.command == "predict":
        cmd_predict(args.sequence, args.k)
    elif args.command == "diff":
        cmd_diff(args.ancestor, args.descendant)
    elif args.command == "ancestry":
        cmd_ancestry(args.attack_id)
    elif args.command == "clean":
        cmd_clean()
    else:
        parser.print_help()
        sys.exit(1)
