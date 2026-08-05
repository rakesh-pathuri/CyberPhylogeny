from typing import List, Tuple
from rich.console import Console

from .models import Genome, Gene
from .similarity import levenshtein_distance

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
                self.gene_lookup[gene.id] = gene
                
    def predict_next(self, current_sequence: List[str], top_k: int = 5) -> List[Tuple[Gene, float, float]]:
        """
        V3 IDS/XDR Grade Prediction Engine.
        Uses Sliding Window Suffix Alignment and Distance-Weighted Voting.
        Returns: [(Gene, Probability Percentage, Confidence Multiplier)]
        """
        if not current_sequence:
            return []
            
        current_len = len(current_sequence)
        distances = []
        
        for genome in self.genomes:
            seq = genome.to_sequence()
            if len(seq) <= 1:
                continue
                
            # SLIDING WINDOW ALIGNMENT
            # Find the minimum mutation distance between the ongoing sequence 
            # and ANY continuous subsequence of the same length in the historical genome.
            min_dist = float('inf')
            best_next_gene = None
            
            # Slide window across the historical sequence
            for i in range(len(seq) - current_len + 1):
                window = seq[i : i + current_len]
                # If this window is the very end of the sequence, there is no "next step" to predict
                if i + current_len >= len(seq):
                    continue
                    
                dist = levenshtein_distance(current_sequence, window)
                if dist < min_dist:
                    min_dist = dist
                    best_next_gene = seq[i + current_len]
                    
            if best_next_gene:
                distances.append((min_dist, best_next_gene, genome.id))
                
        if not distances:
            return []
            
        # Sort by shortest structural distance (least mutations)
        distances.sort(key=lambda x: x[0])
        
        # Take the K closest mathematical neighbors
        nearest_neighbors = distances[:top_k]
        
        # Calculate true probability multipliers
        prediction_weights = {}
        total_weight = 0.0
        
        for dist, next_gene_id, _ in nearest_neighbors:
            # Distance-Weighted Voting:
            # Perfect match (dist=0) gets weight 1.0
            # 1 mutation (dist=1) gets lower weight, etc.
            normalized_dist = dist / current_len
            weight = max(0.0, 1.0 - normalized_dist)
            
            if weight > 0:
                prediction_weights[next_gene_id] = prediction_weights.get(next_gene_id, 0.0) + weight
                total_weight += weight
                
        if total_weight == 0:
            return []
            
        predictions = []
        for next_id, weight in prediction_weights.items():
            prob = weight / total_weight
            gene = self.gene_lookup.get(next_id)
            if gene:
                # Store (Gene, Probability, Confidence Multiplier)
                # Confidence Multiplier is the average weight for this specific prediction branch
                # e.g., if a prediction came from two perfect matches (weight 1.0 + 1.0), confidence is 1.0
                predictions.append((gene, prob, weight))
                
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions
