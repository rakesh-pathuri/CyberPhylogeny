import argparse
import sys
import json
import http.server
import socketserver
import os
import urllib.parse
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

def cmd_dashboard():
    """Boots the native REST API Server for the SPA Dashboard."""
    console.print("[cyan]Loading Knowledge Base for API Server...[/cyan]")
    data = fetch_mitre_data()
    _, genomes = parse_mitre_to_genomes(data)
    
    sim_engine = SimilarityEngine(genomes)
    evo_engine = EvolutionEngine(genomes)
    pred_engine = PredictionEngine(genomes)
    
    # Pre-cluster for speed
    families = sim_engine._cluster_with_metric(genomes, metric_type="levenshtein_genes", eps=0.6, min_samples=2)
    
    class APIHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/api/"):
                parsed_path = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed_path.query)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response_data = {}
                try:
                    if parsed_path.path == "/api/genome":
                        attack_id = query.get("id", [""])[0]
                        genome = next((g for g in genomes if g.id.lower() == attack_id.lower()), None)
                        if genome:
                            genes = []
                            for g in genome.genes:
                                genes.append({
                                    "technique_id": g.technique_id,
                                    "implementation": g.implementation,
                                    "behavior": g.behavior,
                                    "tactic": g.tactic
                                })
                            response_data = {"name": genome.name, "genes": genes}
                        else:
                            response_data = {"error": "Genome not found"}
                            
                    elif parsed_path.path == "/api/cluster":
                        resp = []
                        for label, family in families.items():
                            if label != -1 and len(family) >= 2:
                                resp.append({"id": str(label), "size": len(family)})
                        response_data = {"families": resp}
                        
                    elif parsed_path.path == "/api/tree":
                        fid = int(query.get("family", [-1])[0])
                        if fid in families:
                            fam = families[fid]
                            # Clean rich tags from ASCII tree for raw text display
                            from rich.text import Text
                            raw_tree = evo_engine.build_terminal_tree(fam)
                            if isinstance(raw_tree, Text):
                                raw_tree = raw_tree.plain
                            # Also remove any ANSI codes just in case
                            import re
                            ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
                            ascii_str = ansi_escape.sub('', str(raw_tree))
                            
                            mermaid_str = evo_engine.build_phylogenetic_tree(fam)
                            response_data = {"ascii": ascii_str, "mermaid": mermaid_str}
                        else:
                            response_data = {"error": "Family not found"}
                            
                    elif parsed_path.path == "/api/predict":
                        seq_str = query.get("seq", [""])[0]
                        seq_list = [s.strip().upper() for s in seq_str.split(",") if s.strip()]
                        predictions = pred_engine.predict_next(seq_list, top_k=3)
                        res = []
                        for gene, prob, conf in predictions:
                            res.append({
                                "technique_id": gene.technique_id,
                                "implementation": gene.implementation,
                                "behavior": gene.behavior,
                                "tactic": gene.tactic,
                                "probability": f"{prob*100:.1f}%",
                                "confidence": f"{conf:.2f}x"
                            })
                        response_data = {"predictions": res}
                        
                except Exception as e:
                    response_data = {"error": str(e)}
                    
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
                return
                
            # Serve static files
            return super().do_GET()

    PORT = 8080
    web_dir = os.path.join(os.getcwd(), "dashboard")
    os.chdir(web_dir)
    
    # Enable SO_REUSEADDR
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), APIHandler) as httpd:
        console.print(f"\n[bold cyan]Serving Dashboard & API at http://localhost:{PORT}[/bold cyan]")
        console.print("[dim]Press Ctrl+C to stop.[/dim]")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

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
    parser_tree.add_argument("--eps", type=float, default=0.6, help="DBSCAN epsilon used for clustering")
    parser_tree.add_argument("--min_samples", type=int, default=2, help="Minimum samples used for clustering")
    
    # 5. Predict
    parser_predict = subparsers.add_parser("predict", help="Predict next steps of an ongoing attack")
    parser_predict.add_argument("sequence", type=str, help="Comma-separated list of Technique IDs (e.g., 'T1566.001,T1059.001')")
    parser_predict.add_argument("--k", type=int, default=3, help="Number of nearest neighbors to consider")

    # 6. Dashboard
    parser_dashboard = subparsers.add_parser("dashboard", help="Launch the Web Application Dashboard")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        cmd_ingest()
    elif args.command == "genome":
        cmd_genome(args.attack_id)
    elif args.command == "cluster":
        cmd_cluster(args.eps, args.min_samples)
    elif args.command == "tree":
        cmd_tree(args.eps, args.min_samples, int(args.family))
    elif args.command == "predict":
        cmd_predict(args.sequence, args.k)
    elif args.command == "dashboard":
        cmd_dashboard()
    else:
        parser.print_help()
        sys.exit(1)
