import numpy as np
import hashlib
from collections import defaultdict
from typing import List, Set
from sklearn.cluster import DBSCAN
from rich.console import Console
from rich.progress import Progress

from .models import Genome, Gene

console = Console()

def sequence_alignment_distance(seq1: List, seq2: List, is_tactic: bool = False) -> float:
    """Calculates weighted Needleman-Wunsch sequence alignment distance."""
    if len(seq1) < len(seq2):
        return sequence_alignment_distance(seq2, seq1, is_tactic)

    if len(seq2) == 0:
        return float(len(seq1))

    previous_row = [float(i) for i in range(len(seq2) + 1)]
    for i, c1 in enumerate(seq1):
        current_row = [float(i + 1)]
        for j, c2 in enumerate(seq2):
            insertions = previous_row[j + 1] + 1.0
            deletions = current_row[j] + 1.0
            
            if is_tactic:
                cost = 0.0 if c1 == c2 else 1.0
            else:
                if c1.technique_id == c2.technique_id:
                    cost = 0.0
                elif c1.tactic == c2.tactic:
                    cost = 0.5
                else:
                    cost = 1.0
                    
            substitutions = previous_row[j] + cost
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def get_minhash_signature(gene_set: Set[str], num_hashes: int = 20) -> List[int]:
    """Generates a MinHash signature for LSH pre-filtering."""
    signature = [float('inf')] * num_hashes
    for gene in gene_set:
        for i in range(num_hashes):
            h = int(hashlib.md5(f"{gene}{i}".encode()).hexdigest(), 16)
            if h < signature[i]:
                signature[i] = h
    return signature

def calculate_similarity(genome1: Genome, genome2: Genome) -> float:
    """Returns a similarity score between 0.0 (completely different) and 1.0 (identical)."""
    seq1 = genome1.genes
    seq2 = genome2.genes
    
    max_len = max(len(seq1), len(seq2))
    if max_len == 0: return 1.0
    
    dist = sequence_alignment_distance(seq1, seq2, is_tactic=False)
    similarity = 1.0 - (dist / max_len)
    return max(0.0, similarity)

def jaccard_distance(set1: set, set2: set) -> float:
    """Calculates Jaccard distance between two sets (0.0 means identical, 1.0 means no overlap)."""
    if not set1 and not set2: return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return 1.0 - (intersection / union)

class SimilarityEngine:
    def __init__(self, genomes: List[Genome]):
        self.genomes = genomes
        
    def run_multi_stage_pipeline(self, eps: float = 0.6, min_samples: int = 2):
        """Runs the 3-stage classification pipeline to classify genomes and mathematically handle orphans."""
        console.print(f"\n[bold green]--- STAGE 1: Sequence Alignment (Needleman-Wunsch) ---[/bold green]")
        families_s1 = self._cluster_with_metric(self.genomes, metric_type="levenshtein_genes", eps=eps, min_samples=min_samples)
        
        # Extract orphans from Stage 1 (label -1)
        orphans_s1 = families_s1.get(-1, [])
        if orphans_s1:
            console.print(f"\n[bold yellow]--- STAGE 2: Unordered Motif Matching (Jaccard Similarity) ---[/bold yellow]")
            console.print(f"[dim]Analyzing {len(orphans_s1)} orphans from Stage 1...[/dim]")
            families_s2 = self._cluster_with_metric(orphans_s1, metric_type="jaccard_genes", eps=eps, min_samples=min_samples)
        else:
            families_s2 = {-1: []}
            
        # Extract orphans from Stage 2 (label -1)
        orphans_s2 = families_s2.get(-1, [])
        if orphans_s2:
            console.print(f"\n[bold cyan]--- STAGE 3: Taxonomic Zooming (Tactic Alignment) ---[/bold cyan]")
            console.print(f"[dim]Analyzing {len(orphans_s2)} orphans from Stage 2...[/dim]")
            families_s3 = self._cluster_with_metric(orphans_s2, metric_type="levenshtein_tactics", eps=eps, min_samples=min_samples)
        else:
            families_s3 = {-1: []}
            
        return families_s1, families_s2, families_s3

    def _cluster_with_metric(self, genomes: List[Genome], metric_type: str, eps: float, min_samples: int):
        n = len(genomes)
        if n < min_samples:
            return {-1: genomes}
            
        dist_matrix = np.zeros((n, n))
        
        # Precompute sequences to avoid half a million function calls
        if metric_type == "levenshtein_genes":
            seqs = [g.genes for g in genomes]
        elif metric_type == "jaccard_genes":
            seqs = [g.to_gene_set() for g in genomes]
        elif metric_type == "levenshtein_tactics":
            seqs = [g.to_tactic_sequence() for g in genomes]
            
        # LSH Pre-filtering
        candidates = set()
        if metric_type == "levenshtein_genes":
            console.print("[dim]Applying MinHash LSH pre-filtering...[/dim]")
            num_hashes = 20
            bands = 5
            rows = num_hashes // bands
            buckets = defaultdict(list)
            for i in range(n):
                sig = get_minhash_signature({g.technique_id for g in genomes[i].genes}, num_hashes)
                for b in range(bands):
                    buckets[(b, tuple(sig[b*rows:(b+1)*rows]))].append(i)
                    
            for indices in buckets.values():
                for i in range(len(indices)):
                    for j in range(i+1, len(indices)):
                        candidates.add((indices[i], indices[j]))
        else:
            candidates = set((i, j) for i in range(n) for j in range(i+1, n))
            
        with Progress() as progress:
            display_name = {
                "levenshtein_genes": "Weighted Sequence Alignment",
                "jaccard_genes": "Jaccard Motif Matching",
                "levenshtein_tactics": "Taxonomic Zooming"
            }.get(metric_type, metric_type)
            
            task = progress.add_task(f"[cyan]Calculating distances ({display_name})...", total=n)
            
            for i in range(n):
                seq_i = seqs[i]
                for j in range(i+1, n):
                    if (i, j) not in candidates:
                        # Skip expensive calculation, assume maximum distance
                        dist_matrix[i][j] = dist_matrix[j][i] = 1.0
                        continue
                        
                    seq_j = seqs[j]
                    if metric_type == "jaccard_genes":
                        dist = jaccard_distance(seq_i, seq_j)
                    else:
                        max_len = max(len(seq_i), len(seq_j))
                        is_tactic = (metric_type == "levenshtein_tactics")
                        dist = 0.0 if max_len == 0 else sequence_alignment_distance(seq_i, seq_j, is_tactic) / max_len
                        
                    dist_matrix[i][j] = dist
                    dist_matrix[j][i] = dist
                    
                # Advance only once per genome to keep the clock perfectly stable
                progress.advance(task)
                
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
        labels = clustering.fit_predict(dist_matrix)
        
        # Group by label
        families = {}
        for idx, label in enumerate(labels):
            if label not in families:
                families[label] = []
            families[label].append(genomes[idx])
            
        return families
