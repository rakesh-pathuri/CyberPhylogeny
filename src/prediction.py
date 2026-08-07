from typing import List, Tuple
from rich.console import Console

from .models import Genome, Gene
import numpy as np

console = Console()

class PredictionEngine:
    def __init__(self, genomes: List[Genome]):
        self.genomes = genomes
        self.gene_lookup = {}
        self._build_lookup()
        
    def _build_lookup(self):
        """Builds a lookup table for all known Genes for fast retrieval."""
        for genome in self.genomes:
            for gene in genome.genes:
                self.gene_lookup[f"{gene.source_technique_id}->{gene.target_technique_id}"] = gene
                
    def predict_next(self, current_sequence: List[str], top_k: int = 5) -> List[Tuple[Gene, float, float]]:
        """
        Probabilistic Prediction Engine.
        Uses Suffix Sequence Matching and Distance-Weighted Voting.
        Returns: [(Gene, Probability Percentage, Confidence Multiplier)]
        """
        if not current_sequence:
            return []
            
        # Resolve string IDs to Gene objects
        curr_genes = []
        for gid in current_sequence:
            g = self.gene_lookup.get(gid)
            if g: curr_genes.append(g)
            
        if not curr_genes:
            return []
            
        current_len = len(curr_genes)
        distances = []
        
        for genome in self.genomes:
            hist_genes = genome.genes
            if len(hist_genes) <= 1:
                continue
                
            # SMITH-WATERMAN LOCAL ALIGNMENT
            n = len(hist_genes)
            m = current_len
            dp = np.zeros((n + 1, m + 1), dtype=float)
            
            max_score = 0.0
            best_next_gene = None
            
            for i in range(1, n + 1):
                for j in range(1, m + 1):
                    h_gene = hist_genes[i-1]
                    c_gene = curr_genes[j-1]
                    
                    if h_gene.source_technique_id == c_gene.source_technique_id and h_gene.target_technique_id == c_gene.target_technique_id:
                        score = 3.0
                    elif h_gene.source_tactic == c_gene.source_tactic and h_gene.target_tactic == c_gene.target_tactic:
                        score = 1.0
                    else:
                        score = -2.0
                        
                    val = max(
                        0.0,
                        dp[i-1][j-1] + score,
                        dp[i-1][j] - 1.0,
                        dp[i][j-1] - 1.0
                    )
                    dp[i][j] = val
                    
                    # Track the best local match that HAS a continuation
                    if val > max_score and i < n:
                        max_score = val
                        best_next_gene = hist_genes[i]
                            
            if best_next_gene and max_score > 0:
                normalized_score = max_score / (m * 3.0)
                distances.append((normalized_score, best_next_gene, genome.id))
                
        if not distances:
            return []
            
        # Sort by highest local alignment score
        distances.sort(key=lambda x: x[0], reverse=True)
        
        # Take the K closest mathematical neighbors
        nearest_neighbors = distances[:top_k]
        
        # Calculate true probability multipliers
        prediction_weights = {}
        prediction_counts = {}
        total_weight = 0.0
        
        for score, next_gene, _ in nearest_neighbors:
            # Score-Weighted Voting
            weight = score
            if weight > 0:
                transition_id = f"{next_gene.source_technique_id}->{next_gene.target_technique_id}"
                prediction_weights[transition_id] = prediction_weights.get(transition_id, 0.0) + weight
                prediction_counts[transition_id] = prediction_counts.get(transition_id, 0) + 1
                total_weight += weight
                
        if total_weight == 0:
            return []
            
        predictions = []
        for next_id, weight in prediction_weights.items():
            prob = weight / total_weight
            gene = self.gene_lookup.get(next_id)
            if gene:
                # Confidence Multiplier is the average weight for this specific prediction branch
                # e.g., if a prediction came from two perfect matches (weight 1.0 + 1.0), confidence is 1.0
                avg_confidence = weight / prediction_counts[next_id]
                predictions.append((gene, prob, avg_confidence))
                
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions
