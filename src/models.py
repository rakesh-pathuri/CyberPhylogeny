from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Gene(BaseModel):
    """A single atomic action in an attack. Modeled as a 3-tier hierarchy."""
    technique_id: str  # e.g., 'T1003'
    implementation: str # e.g., 'OS Credential Dumping'
    behavior: str # e.g., 'credential-access'
    description: Optional[str] = None

class Genome(BaseModel):
    """An ordered sequence of genes representing a specific attack or group."""
    id: str # e.g., 'G0016' (APT29)
    name: str
    description: Optional[str] = None
    genes: List[Gene] = Field(default_factory=list)
    
    def to_sequence(self) -> List[str]:
        """Returns ordered list of Gene IDs."""
        return [g.technique_id for g in self.genes]
        
    def to_gene_set(self) -> set:
        """Returns an unordered set of Gene IDs (Stage 2: Bag of Genes)."""
        return {g.technique_id for g in self.genes}
        
    def to_tactic_sequence(self) -> List[str]:
        """Returns ordered list of Behaviors (Stage 3: Taxonomic Zooming)."""
        return [g.behavior for g in self.genes]
