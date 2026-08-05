import numpy as np
from typing import List
from sklearn.cluster import DBSCAN
from rich.console import Console
from rich.progress import Progress

from .models import Genome

console = Console()

def levenshtein_distance(seq1: List[str], seq2: List[str]) -> int:
    """Calculates the minimum edit distance between two Gene sequences (Needleman-Wunsch style sequence alignment)."""
    if len(seq1) < len(seq2):
        return levenshtein_distance(seq2, seq1)

    if len(seq2) == 0:
        return len(seq1)

    previous_row = list(range(len(seq2) + 1))
    for i, c1 in enumerate(seq1):
        current_row = [i + 1]
        for j, c2 in enumerate(seq2):
            insertions = previous_row[j + 1] + 1 
            deletions = current_row[j] + 1       
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def calculate_similarity(genome1: Genome, genome2: Genome) -> float:
    """Returns a similarity score between 0.0 (completely different) and 1.0 (identical)."""
    seq1 = genome1.to_sequence()
    seq2 = genome2.to_sequence()
    
    max_len = max(len(seq1), len(seq2))
    if max_len == 0: return 1.0
    
    dist = levenshtein_distance(seq1, seq2)
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
            seqs = [g.to_sequence() for g in genomes]
        elif metric_type == "jaccard_genes":
            seqs = [g.to_gene_set() for g in genomes]
        elif metric_type == "levenshtein_tactics":
            seqs = [g.to_tactic_sequence() for g in genomes]
            
        with Progress() as progress:
            display_name = {
                "levenshtein_genes": "Sequence Alignment",
                "jaccard_genes": "Jaccard Motif Matching",
                "levenshtein_tactics": "Taxonomic Zooming"
            }.get(metric_type, metric_type)
            
            task = progress.add_task(f"[cyan]Calculating distances ({display_name})...", total=n)
            
            for i in range(n):
                seq_i = seqs[i]
                for j in range(i+1, n):
                    seq_j = seqs[j]
                    
                    if metric_type == "jaccard_genes":
                        dist = jaccard_distance(seq_i, seq_j)
                    else:
                        max_len = max(len(seq_i), len(seq_j))
                        dist = 0.0 if max_len == 0 else levenshtein_distance(seq_i, seq_j) / max_len
                        
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
