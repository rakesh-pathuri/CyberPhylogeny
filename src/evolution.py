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
                mutations.append(f"Gene Mutated: {old_gene.behavior.upper()} [{old_gene.implementation} -> {new_gene.implementation}]")
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                # Deletion
                old_gene = ancestor.genes[i-1]
                mutations.append(f"Gene Dropped: [{old_gene.implementation}]")
                i -= 1
            else:
                # Insertion
                new_gene = descendant.genes[j-1]
                mutations.append(f"Gene Inserted: [{new_gene.implementation}]")
                j -= 1
                
        # Traceback builds the path backwards, so reverse it
        return mutations[::-1]

    def build_phylogenetic_tree(self, family_genomes: List[Genome]) -> str:
        """
        Builds a true Phylogenetic Tree (Minimum Spanning Tree) using Prim's algorithm.
        Returns a Mermaid.js graph string representing the evolutionary branches.
        """
        n = len(family_genomes)
        if n < 2:
            return "graph TD\n    A[Not enough genomes for a tree]"
            
        # 1. Build Pairwise Distance Matrix
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            seq_i = family_genomes[i].to_sequence()
            for j in range(i+1, n):
                seq_j = family_genomes[j].to_sequence()
                dist = levenshtein_distance(seq_i, seq_j)
                dist_matrix[i][j] = dist
                dist_matrix[j][i] = dist
                
        # 2. Prim's Algorithm for MST
        # Assume the shortest genome is the root ancestor
        root_idx = min(range(n), key=lambda idx: len(family_genomes[idx].genes))
        
        visited = {root_idx}
        edges = []
        
        while len(visited) < n:
            min_dist = float('inf')
            best_edge = None
            
            for u in visited:
                for v in range(n):
                    if v not in visited:
                        if dist_matrix[u][v] < min_dist:
                            min_dist = dist_matrix[u][v]
                            best_edge = (u, v, dist_matrix[u][v])
                            
            if best_edge:
                u, v, dist = best_edge
                visited.add(v)
                edges.append(best_edge)
                
        # 3. Generate Mermaid Graph (Text Output)
        lines = ["graph TD"]
        for u, v, dist in edges:
            node_u = f'{family_genomes[u].id}["{family_genomes[u].name}"]'
            node_v = f'{family_genomes[v].id}["{family_genomes[v].name}"]'
            lines.append(f"    {node_u} -->|Mutations: {int(dist)}| {node_v}")
            
        # Add styles
        lines.append("\n    classDef ancestor fill:#ff9f1c,stroke:#333,stroke-width:2px,color:#fff;")
        lines.append("    classDef descendant fill:#2ec4b6,stroke:#333,stroke-width:2px,color:#fff;")
        lines.append(f"    class {family_genomes[root_idx].id} ancestor;")
        
        for v in range(n):
            if v != root_idx:
                lines.append(f"    class {family_genomes[v].id} descendant;")
                
        # 4. Generate Interactive PyVis HTML Graph
        try:
            from pyvis.network import Network
            
            # Create a directed network graph
            net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", directed=True)
            net.barnes_hut() # Use physics engine for layout
            
            # Add nodes
            for i, genome in enumerate(family_genomes):
                color = "#ff9f1c" if i == root_idx else "#2ec4b6"
                title = f"<b>{genome.id}</b><br>{genome.name}<br>Length: {len(genome.genes)} genes"
                net.add_node(genome.id, label=genome.id, title=title, color=color, size=20 + (len(genome.genes)))
                
            # Add edges
            for u, v, dist in edges:
                # Arrow points from Ancestor to Descendant
                net.add_edge(family_genomes[u].id, family_genomes[v].id, title=f"{int(dist)} Mutations", value=int(dist), color="#777777")
                
            out_file = f"family_{family_genomes[0].id}_phylogeny.html"
            net.save_graph(out_file)
            console.print(f"[bold green]Interactive visual graph saved to: {out_file}[/bold green]")
        except ImportError:
            console.print("[yellow]Hint: 'pip install pyvis' to also generate interactive HTML graphs.[/yellow]")
                
        return "\n".join(lines)
        
    def _get_aligned_genes(self, ancestor: Genome, descendant: Genome) -> List[str]:
        """Runs traceback to generate a formatted list of descendant genes with mutation tags."""
        seq1 = ancestor.to_sequence()
        seq2 = descendant.to_sequence()
        
        n, m = len(seq1), len(seq2)
        dp = np.zeros((n + 1, m + 1), dtype=int)
        for i in range(n + 1): dp[i][0] = i
        for j in range(m + 1): dp[0][j] = j
            
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = 0 if seq1[i-1] == seq2[j-1] else 1
                dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)
                
        aligned = []
        i, j = n, m
        
        while i > 0 or j > 0:
            if i > 0 and j > 0 and seq1[i-1] == seq2[j-1]:
                gene = descendant.genes[j-1]
                aligned.append(f"{gene.behavior}: {gene.implementation}")
                i -= 1; j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
                old_g = ancestor.genes[i-1]
                new_g = descendant.genes[j-1]
                aligned.append(f"{new_g.behavior}: {new_g.implementation} [red]<-- Mutated (from {old_g.implementation})[/red]")
                i -= 1; j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                old_g = ancestor.genes[i-1]
                aligned.append(f"[strike]{old_g.behavior}: {old_g.implementation}[/strike] [yellow]<-- Dropped[/yellow]")
                i -= 1
            else:
                new_g = descendant.genes[j-1]
                aligned.append(f"{new_g.behavior}: {new_g.implementation} [green]<-- New Gene[/green]")
                j -= 1
                
        return aligned[::-1]

    def build_terminal_tree(self, family_genomes: List[Genome]) -> "rich.tree.Tree":
        from rich.tree import Tree
        n = len(family_genomes)
        if n == 0:
            return Tree("Empty Family")
            
        # Recalculate MST (in production we'd cache this)
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                d = levenshtein_distance(family_genomes[i].to_sequence(), family_genomes[j].to_sequence())
                dist_matrix[i][j] = dist_matrix[j][i] = d
                
        root_idx = min(range(n), key=lambda idx: len(family_genomes[idx].genes))
        visited = {root_idx}
        
        # Build adjacency list for tree
        children = {i: [] for i in range(n)}
        
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
                
        # Recursive tree builder
        def add_branches(node_idx, parent_tree, is_root=False):
            genome = family_genomes[node_idx]
            
            if is_root:
                label = f"[bold cyan]Ancestor: {genome.id} ({genome.name})[/bold cyan]"
                current_branch = parent_tree.add(label)
                for gene in genome.genes:
                    current_branch.add(f"{gene.behavior}: {gene.implementation}")
            else:
                # Find parent in our MST
                parent_idx = None
                for p, ch in children.items():
                    if node_idx in ch:
                        parent_idx = p
                        break
                        
                label = f"[bold magenta]Descendant: {genome.id} ({genome.name})[/bold magenta]"
                current_branch = parent_tree.add(label)
                
                # Get annotated genes compared to parent
                annotated_genes = self._get_aligned_genes(family_genomes[parent_idx], genome)
                for line in annotated_genes:
                    current_branch.add(line)
                    
            # Recurse for children
            for child_idx in children[node_idx]:
                add_branches(child_idx, current_branch, is_root=False)
                
        root_tree = Tree(f"[bold white]Evolutionary Tree[/bold white]")
        add_branches(root_idx, root_tree, is_root=True)
        return root_tree
