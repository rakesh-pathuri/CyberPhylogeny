from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Gene(BaseModel):
    """A behavioral transition (edge) between two atomic actions in an attack."""
    source_technique_id: str
    target_technique_id: str
    source_implementation: str
    target_implementation: str
    source_tactic: str
    target_tactic: str
    
    def __eq__(self, other):
        if not isinstance(other, Gene):
            return False
        return (self.source_technique_id == other.source_technique_id and 
                self.target_technique_id == other.target_technique_id)
                
    def __hash__(self):
        return hash((self.source_technique_id, self.target_technique_id))

class Genome(BaseModel):
    """An ordered sequence of genes representing a specific attack or group."""
    id: str # e.g., 'G0016' (APT29)
    name: str
    description: Optional[str] = None
    created: datetime
    genes: List[Gene] = Field(default_factory=list)
    
    def to_sequence(self) -> List[str]:
        """Returns ordered list of Gene transition signatures."""
        return [f"{g.source_technique_id}->{g.target_technique_id}" for g in self.genes]
        
    def to_gene_set(self) -> set:
        """Returns an unordered set of Gene transitions (Stage 2: Bag of Genes)."""
        return {f"{g.source_technique_id}->{g.target_technique_id}" for g in self.genes}
        
    def to_tactic_sequence(self) -> List[str]:
        """Returns ordered list of Tactic transitions."""
        return [f"{g.source_tactic}->{g.target_tactic}" for g in self.genes]
        
    def to_parent_technique_sequence(self) -> List[str]:
        """Returns ordered list of Parent Technique transitions (Stage 3: Taxonomic Zooming)."""
        return [f"{g.source_technique_id.split('.')[0]}->{g.target_technique_id.split('.')[0]}" for g in self.genes]
