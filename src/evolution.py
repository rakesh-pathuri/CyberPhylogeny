import numpy as np
from typing import List, Dict, Tuple
from rich.console import Console

from .models import Genome, Gene
from .similarity import levenshtein_distance

console = Console()

class EvolutionEngine:
    def __init__(self, genomes: List[Genome]):
        self.genomes = genomes
        
    def analyze_family_evolution(self, family_genomes: List[Genome]) -> List[Tuple[Genome, Genome, List[str]]]:
        """
        Analyzes a family of genomes and identifies the specific mutations
        (substitutions, insertions, deletions) that occurred between them.
        Returns a list of (GenomeA, GenomeB, [Mutation Details])
        """
        if len(family_genomes) < 2:
            console.print("[yellow]Not enough genomes in family to track evolution.[/yellow]")
            return []
            
        # Sort genomes by length as a naive proxy for "time" (assuming attacks get more complex)
        # In a real system, you'd sort by the actual timestamp of the threat report
        sorted_family = sorted(family_genomes, key=lambda g: len(g.genes))
        
        mutations_history = []
        
        for i in range(len(sorted_family) - 1):
            ancestor = sorted_family[i]
            descendant = sorted_family[i+1]
            
            mutations = self._calculate_mutations(ancestor, descendant)
            mutations_history.append((ancestor, descendant, mutations))
            
        return mutations_history
        
    def _calculate_mutations(self, ancestor: Genome, descendant: Genome) -> List[str]:
        """
        Uses dynamic programming traceback to find exactly which genes
        were inserted, deleted, or substituted.
        """
        seq1 = ancestor.to_sequence()
        seq2 = descendant.to_sequence()
        
        # Build Levenshtein matrix
        n, m = len(seq1), len(seq2)
        dp = np.zeros((n + 1, m + 1), dtype=int)
        for i in range(n + 1): dp[i][0] = i
        for j in range(m + 1): dp[0][j] = j
            
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = 0 if seq1[i-1] == seq2[j-1] else 1
                dp[i][j] = min(
                    dp[i-1][j] + 1,      # deletion
                    dp[i][j-1] + 1,      # insertion
                    dp[i-1][j-1] + cost  # substitution
                )
                
        # Traceback to find operations
        mutations = []
        i, j = n, m
        
        while i > 0 or j > 0:
            if i > 0 and j > 0 and seq1[i-1] == seq2[j-1]:
                # Match
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
                # Substitution
                old_gene = ancestor.genes[i-1]
                new_gene = descendant.genes[j-1]
                mutations.append(f"Gene Mutated: {old_gene.tactic.upper()} [{old_gene.name} -> {new_gene.name}]")
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                # Deletion
                old_gene = ancestor.genes[i-1]
                mutations.append(f"Gene Dropped: [{old_gene.name}]")
                i -= 1
            else:
                # Insertion
                new_gene = descendant.genes[j-1]
                mutations.append(f"Gene Inserted: [{new_gene.name}]")
                j -= 1
                
        # Traceback builds the path backwards, so reverse it
        return mutations[::-1]
