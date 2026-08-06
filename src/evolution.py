import numpy as np
from typing import List, Dict, Tuple
from rich.console import Console

from .models import Genome, Gene
from .similarity import sequence_alignment_distance

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
            
        # Sort genomes by true chronological creation timestamp
        sorted_family = sorted(family_genomes, key=lambda g: g.created)
        
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
        seq1 = ancestor.genes
        seq2 = descendant.genes
        
        # Build Alignment matrix
        n, m = len(seq1), len(seq2)
        dp = np.zeros((n + 1, m + 1), dtype=float)
        for i in range(n + 1): dp[i][0] = float(i)
        for j in range(m + 1): dp[0][j] = float(j)
            
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                c1 = seq1[i-1]
                c2 = seq2[j-1]
                if c1.source_technique_id == c2.source_technique_id and c1.target_technique_id == c2.target_technique_id:
                    cost = 0.0
                elif c1.source_tactic == c2.source_tactic and c1.target_tactic == c2.target_tactic:
                    cost = 0.5
                else:
                    cost = 1.0
                dp[i][j] = min(
                    dp[i-1][j] + 1.0,      # deletion
                    dp[i][j-1] + 1.0,      # insertion
                    dp[i-1][j-1] + cost  # substitution
                )
                
        # Traceback to find operations
        mutations = []
        i, j = n, m
        
        while i > 0 or j > 0:
            if i > 0 and j > 0 and seq1[i-1].source_technique_id == seq2[j-1].source_technique_id and seq1[i-1].target_technique_id == seq2[j-1].target_technique_id:
                # Match
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] < dp[i-1][j] + 1.0 and dp[i][j] < dp[i][j-1] + 1.0:
                # Substitution
                old_gene = ancestor.genes[i-1]
                new_gene = descendant.genes[j-1]
                mutations.append(f"Transition Mutated: [{old_gene.source_implementation}->{old_gene.target_implementation} to {new_gene.source_implementation}->{new_gene.target_implementation}]")
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                # Deletion
                old_gene = ancestor.genes[i-1]
                mutations.append(f"Transition Dropped: [{old_gene.source_implementation}->{old_gene.target_implementation}]")
                i -= 1
            else:
                # Insertion
                new_gene = descendant.genes[j-1]
                mutations.append(f"Transition Inserted: [{new_gene.source_implementation}->{new_gene.target_implementation}]")
                j -= 1
                
        # Traceback builds the path backwards, so reverse it
        return mutations[::-1]


        
    def _get_aligned_genes(self, ancestor: Genome, descendant: Genome) -> List[str]:
        """Runs traceback to generate a formatted list of descendant genes with mutation tags."""
        seq1 = ancestor.genes
        seq2 = descendant.genes
        
        n, m = len(seq1), len(seq2)
        dp = np.zeros((n + 1, m + 1), dtype=float)
        for i in range(n + 1): dp[i][0] = float(i)
        for j in range(m + 1): dp[0][j] = float(j)
            
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                c1 = seq1[i-1]
                c2 = seq2[j-1]
                if c1.source_technique_id == c2.source_technique_id and c1.target_technique_id == c2.target_technique_id:
                    cost = 0.0
                elif c1.source_tactic == c2.source_tactic and c1.target_tactic == c2.target_tactic:
                    cost = 0.5
                else:
                    cost = 1.0
                dp[i][j] = min(dp[i-1][j]+1.0, dp[i][j-1]+1.0, dp[i-1][j-1]+cost)
                
        mutation_distance = 0.0
        aligned = []
        i, j = n, m
        
        while i > 0 or j > 0:
            if i > 0 and j > 0 and seq1[i-1].source_technique_id == seq2[j-1].source_technique_id and seq1[i-1].target_technique_id == seq2[j-1].target_technique_id:
                gene = descendant.genes[j-1]
                aligned.append(f"                   | \\[{gene.source_tactic}->{gene.target_tactic}] {gene.source_implementation}->{gene.target_implementation}")
                i -= 1; j -= 1
            elif i > 0 and j > 0 and dp[i][j] < dp[i-1][j] + 1.0 and dp[i][j] < dp[i][j-1] + 1.0:
                old_g = ancestor.genes[i-1]
                new_g = descendant.genes[j-1]
                if old_g.source_tactic == new_g.source_tactic and old_g.target_tactic == new_g.target_tactic:
                    mutation_distance += 0.5
                    aligned.append(f"Type: Substitution | \\[{new_g.source_tactic}->{new_g.target_tactic}] {new_g.source_implementation}->{new_g.target_implementation} [red]<-- Mutated (from {old_g.source_implementation}->{old_g.target_implementation})[/red]")
                else:
                    mutation_distance += 1.0
                    aligned.append(f"Type: Tactic Shift | \\[{new_g.source_tactic}->{new_g.target_tactic}] {new_g.source_implementation}->{new_g.target_implementation} [red]<-- Tactic Shift (from \\[{old_g.source_tactic}->{old_g.target_tactic}] {old_g.source_implementation}->{old_g.target_implementation})[/red]")
                i -= 1; j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                mutation_distance += 1.0
                old_g = ancestor.genes[i-1]
                aligned.append(f"Type: Deletion     | [strike]\\[{old_g.source_tactic}->{old_g.target_tactic}] {old_g.source_implementation}->{old_g.target_implementation}[/strike] [yellow]<-- Dropped[/yellow]")
                i -= 1
            else:
                mutation_distance += 1.0
                new_g = descendant.genes[j-1]
                aligned.append(f"Type: Insertion    | \\[{new_g.source_tactic}->{new_g.target_tactic}] {new_g.source_implementation}->{new_g.target_implementation} [green]<-- New Transition[/green]")
                j -= 1
                
        return aligned[::-1], mutation_distance

    def build_terminal_tree(self, family_genomes: List[Genome]) -> "rich.tree.Tree":
        from rich.tree import Tree
        n = len(family_genomes)
        if n == 0:
            return Tree("Empty Family")
            
        # Recalculate MST (in production we'd cache this)
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                d = sequence_alignment_distance(family_genomes[i].genes, family_genomes[j].genes, is_tactic=False)
                dist_matrix[i][j] = dist_matrix[j][i] = d
                
        root_idx = min(range(n), key=lambda idx: family_genomes[idx].created)
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
                
        root_tree = Tree(f"[bold white]Evolutionary Tree[/bold white]")
        
        # We traverse the tree but add EVERY genome directly to the root_tree
        # to prevent deep nesting, which makes it look like descendants are just genes.
        def traverse_and_add(node_idx, is_root=False):
            genome = family_genomes[node_idx]
            
            if is_root:
                label = f"[bold cyan]Ancestor: {genome.id} ({genome.name})[/bold cyan]"
                current_branch = root_tree.add(label)
                for gene in genome.genes:
                    current_branch.add(f"\\[{gene.source_tactic}->{gene.target_tactic}] {gene.source_implementation}->{gene.target_implementation}")
            else:
                # Find parent in our MST
                parent_idx = None
                for p, ch in children.items():
                    if node_idx in ch:
                        parent_idx = p
                        break
                        
                parent_genome = family_genomes[parent_idx]
                # Recompute distance for MST branch length
                mutation_distance = sequence_alignment_distance(parent_genome.genes, genome.genes, is_tactic=False)
                label = f"[bold magenta]{genome.id} ({genome.name})[/bold magenta] [dim](+{mutation_distance:.1f})[/dim]"
                current_branch = root_tree.add(label)
                    
            # Recurse for children
            for child_idx in children[node_idx]:
                traverse_and_add(child_idx, is_root=False)
                
        traverse_and_add(root_idx, is_root=True)
        return root_tree

    def build_upgma_tree(self, family_genomes: List[Genome]) -> "rich.tree.Tree":
        from rich.tree import Tree
        n = len(family_genomes)
        if n == 0:
            return Tree("Empty Family")
        if n == 1:
            g = family_genomes[0]
            t = Tree(f"[bold cyan]Genome: {g.id} ({g.name})[/bold cyan]")
            return t
            
        # Initialize distance matrix
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                d = sequence_alignment_distance(family_genomes[i].genes, family_genomes[j].genes, is_tactic=False)
                dist_matrix[i][j] = dist_matrix[j][i] = d

        # UPGMA state tracking
        clusters = {i: {"id": i, "genome": family_genomes[i], "height": 0.0, "children": []} for i in range(n)}
        active_clusters = list(range(n))
        next_cluster_id = n
        
        while len(active_clusters) > 1:
            # Find min distance
            min_dist = float('inf')
            best_pair = None
            for i_idx in range(len(active_clusters)):
                for j_idx in range(i_idx + 1, len(active_clusters)):
                    u = active_clusters[i_idx]
                    v = active_clusters[j_idx]
                    if dist_matrix[u][v] < min_dist:
                        min_dist = dist_matrix[u][v]
                        best_pair = (u, v)
            
            u, v = best_pair
            
            # Infer ancestor genome
            genome_u = clusters[u]["genome"]
            genome_v = clusters[v]["genome"]
            # Ensure chronological order for infer_ancestor (older first)
            if genome_u.created > genome_v.created:
                genome_u, genome_v = genome_v, genome_u
            
            ancestor_genome = self.infer_ancestor(f"Internal-{next_cluster_id}", genome_u, genome_v)
            
            # Create new cluster
            new_height = min_dist / 2.0
            new_cluster = {
                "id": next_cluster_id, 
                "genome": ancestor_genome,
                "height": new_height,
                "children": [clusters[u], clusters[v]],
                "size": clusters[u].get("size", 1) + clusters[v].get("size", 1)
            }
            clusters[next_cluster_id] = new_cluster
            
            # Update distance matrix (we will just grow the matrix)
            dist_matrix = np.pad(dist_matrix, ((0, 1), (0, 1)), mode='constant')
            
            size_u = clusters[u].get("size", 1)
            size_v = clusters[v].get("size", 1)
            size_new = size_u + size_v
            
            for c in active_clusters:
                if c != u and c != v:
                    d = (size_u * dist_matrix[u][c] + size_v * dist_matrix[v][c]) / size_new
                    dist_matrix[next_cluster_id][c] = dist_matrix[c][next_cluster_id] = d
                    
            active_clusters.remove(u)
            active_clusters.remove(v)
            active_clusters.append(next_cluster_id)
            next_cluster_id += 1
            
        root_cluster = clusters[active_clusters[0]]
        
        # Build rich tree
        root_tree = Tree(f"[bold white]UPGMA Dendrogram (Root Height: {root_cluster['height']:.2f})[/bold white]")
        
        def traverse(node: dict, tree_node: "rich.tree.Tree", parent_genome=None, parent_height=0.0):
            branch_len = parent_height - node["height"] if parent_height > 0 else 0.0
            dash_count = max(1, int(branch_len * 5))
            dashes = "-" * dash_count
            
            if len(node["children"]) == 0:
                # Leaf node
                g = node["genome"]
                label = f"[dim]{dashes}[/dim] [bold cyan]{g.id} ({g.name})[/bold cyan] [dim](branch: {branch_len:.2f})[/dim]"
                leaf = tree_node.add(label)
            else:
                # Internal node
                label = f"[dim]{dashes}[/dim] [bold yellow]Common Ancestor[/bold yellow] [dim](height: {node['height']:.2f}, branch: {branch_len:.2f})[/dim]"
                new_branch = tree_node.add(label)
                    
                for child in node["children"]:
                    traverse(child, new_branch, node["genome"], node["height"])
                    
        for child in root_cluster["children"]:
            traverse(child, root_tree, root_cluster["genome"], root_cluster["height"])
            
        return root_tree

    def infer_ancestor(self, ancestor_id: str, g1: Genome, g2: Genome) -> Genome:
        """Infers the hypothetical common ancestor sequence from two child genomes using sequence alignment."""
        seq1 = g1.genes
        seq2 = g2.genes
        
        n, m = len(seq1), len(seq2)
        dp = np.zeros((n + 1, m + 1), dtype=float)
        for i in range(n + 1): dp[i][0] = float(i)
        for j in range(m + 1): dp[0][j] = float(j)
            
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                c1 = seq1[i-1]
                c2 = seq2[j-1]
                if c1.source_technique_id == c2.source_technique_id and c1.target_technique_id == c2.target_technique_id:
                    cost = 0.0
                elif c1.source_tactic == c2.source_tactic and c1.target_tactic == c2.target_tactic:
                    cost = 0.5
                else:
                    cost = 1.0
                dp[i][j] = min(dp[i-1][j]+1.0, dp[i][j-1]+1.0, dp[i-1][j-1]+cost)
                
        # Traceback to build ancestral genes
        ancestral_genes = []
        i, j = n, m
        
        while i > 0 or j > 0:
            if i > 0 and j > 0 and seq1[i-1].source_technique_id == seq2[j-1].source_technique_id and seq1[i-1].target_technique_id == seq2[j-1].target_technique_id:
                ancestral_genes.append(seq1[i-1])
                i -= 1; j -= 1
            elif i > 0 and j > 0 and dp[i][j] < dp[i-1][j] + 1.0 and dp[i][j] < dp[i][j-1] + 1.0:
                if seq1[i-1].source_tactic == seq2[j-1].source_tactic and seq1[i-1].target_tactic == seq2[j-1].target_tactic:
                    ancestral_genes.append(seq1[i-1])
                i -= 1; j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                i -= 1
            else:
                j -= 1
                
        return Genome(
            id=ancestor_id, 
            name="Hypothetical Ancestor", 
            description="Inferred via Ancestral Sequence Reconstruction", 
            created=min(g1.created, g2.created), 
            genes=ancestral_genes[::-1]
        )

    def get_tactic_grouped_mutations(self, ancestor: Genome, descendant: Genome) -> Tuple[Dict[str, List[str]], float]:
        """Calculates mutations and groups them by Tactic for Git-style diff."""
        seq1 = ancestor.genes
        seq2 = descendant.genes
        
        n, m = len(seq1), len(seq2)
        dp = np.zeros((n + 1, m + 1), dtype=float)
        for i in range(n + 1): dp[i][0] = float(i)
        for j in range(m + 1): dp[0][j] = float(j)
            
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                c1 = seq1[i-1]
                c2 = seq2[j-1]
                if c1.source_technique_id == c2.source_technique_id and c1.target_technique_id == c2.target_technique_id:
                    cost = 0.0
                elif c1.source_tactic == c2.source_tactic and c1.target_tactic == c2.target_tactic:
                    cost = 0.5
                else:
                    cost = 1.0
                dp[i][j] = min(dp[i-1][j]+1.0, dp[i][j-1]+1.0, dp[i-1][j-1]+cost)
                
        mutation_score = 0.0
        grouped_mutations = {}
        i, j = n, m
        
        # Traverse and collect backwards
        ops = []
        while i > 0 or j > 0:
            if i > 0 and j > 0 and seq1[i-1].source_technique_id == seq2[j-1].source_technique_id and seq1[i-1].target_technique_id == seq2[j-1].target_technique_id:
                i -= 1; j -= 1
            elif i > 0 and j > 0 and dp[i][j] < dp[i-1][j] + 1.0 and dp[i][j] < dp[i][j-1] + 1.0:
                old_g = ancestor.genes[i-1]
                new_g = descendant.genes[j-1]
                if old_g.source_tactic == new_g.source_tactic and old_g.target_tactic == new_g.target_tactic:
                    mutation_score += 0.5
                    ops.append((f"{new_g.source_tactic}->{new_g.target_tactic}", f"[yellow]\\[~][/yellow] ({old_g.source_implementation}->{old_g.target_implementation}) to ({new_g.source_implementation}->{new_g.target_implementation})"))
                else:
                    mutation_score += 1.0
                    ops.append((f"{old_g.source_tactic}->{old_g.target_tactic}", f"[red]\\[-][/red] {old_g.source_implementation}->{old_g.target_implementation} [dim](Dropped Tactic Shift)[/dim]"))
                    ops.append((f"{new_g.source_tactic}->{new_g.target_tactic}", f"[green]\\[+][/green] {new_g.source_implementation}->{new_g.target_implementation} [dim](New Tactic Shift from {old_g.source_tactic}->{old_g.target_tactic})[/dim]"))
                i -= 1; j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                mutation_score += 1.0
                old_g = ancestor.genes[i-1]
                ops.append((f"{old_g.source_tactic}->{old_g.target_tactic}", f"[red]\\[-][/red] {old_g.source_implementation}->{old_g.target_implementation} [dim](Dropped)[/dim]"))
                i -= 1
            else:
                mutation_score += 1.0
                new_g = descendant.genes[j-1]
                ops.append((f"{new_g.source_tactic}->{new_g.target_tactic}", f"[green]\\[+][/green] {new_g.source_implementation}->{new_g.target_implementation} [dim](New Transition)[/dim]"))
                j -= 1
                
        ops.reverse()
        for tactic, desc in ops:
            grouped_mutations.setdefault(tactic, []).append(desc)
            
        return grouped_mutations, mutation_score
