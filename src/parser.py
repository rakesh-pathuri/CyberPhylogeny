import requests
import json
from collections import defaultdict
from typing import List, Dict, Tuple
from rich.console import Console
from .models import Gene, Genome

console = Console()

MITRE_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

KILL_CHAIN_ORDER = {
    "reconnaissance": 1,
    "resource-development": 2,
    "initial-access": 3,
    "execution": 4,
    "persistence": 5,
    "privilege-escalation": 6,
    "defense-evasion": 7,
    "credential-access": 8,
    "discovery": 9,
    "lateral-movement": 10,
    "collection": 11,
    "command-and-control": 12,
    "exfiltration": 13,
    "impact": 14
}

def get_kill_chain_sort_key(tactic_name: str) -> int:
    return KILL_CHAIN_ORDER.get(tactic_name, 99)

def fetch_mitre_data() -> dict:
    """Fetches the latest MITRE ATT&CK Enterprise STIX JSON."""
    console.print("[cyan]Fetching MITRE ATT&CK Enterprise dataset...[/cyan]")
    response = requests.get(MITRE_URL)
    response.raise_for_status()
    return response.json()

def parse_mitre_to_genomes(data: dict) -> Tuple[List[Gene], List[Genome]]:
    """Parses STIX data to extract Attack Patterns (Genes) and Intrusion Sets (Genomes)."""
    objects = data.get("objects", [])
    
    techniques = {}
    groups = {}
    group_to_techniques = defaultdict(list)
    
    # First pass: map objects
    for obj in objects:
        t = obj.get("type")
        if t == "attack-pattern":
            # Get external ID (e.g. T1003)
            ext_id = None
            for ref in obj.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    ext_id = ref.get("external_id")
                    break
            
            if ext_id:
                # Find primary kill chain phase
                kc_phases = obj.get("kill_chain_phases", [])
                primary_tactic = kc_phases[0]["phase_name"] if kc_phases else "unknown"
                
                techniques[obj["id"]] = Gene(
                    id=ext_id,
                    name=obj.get("name", "Unknown"),
                    tactic=primary_tactic,
                    description=obj.get("description")
                )
        elif t in ["intrusion-set", "malware", "tool"]:
            ext_id = None
            for ref in obj.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    ext_id = ref.get("external_id")
                    break
            if ext_id:
                groups[obj["id"]] = {
                    "ext_id": ext_id,
                    "name": obj.get("name", "Unknown"),
                    "description": obj.get("description")
                }
    
    # Second pass: map relationships
    for obj in objects:
        if obj.get("type") == "relationship" and obj.get("relationship_type") == "uses":
            source = obj.get("source_ref")
            target = obj.get("target_ref")
            
            if source in groups and target in techniques:
                group_to_techniques[source].append(techniques[target])
    
    # Build Genomes
    genomes = []
    all_genes = list(techniques.values())
    
    for group_id, group_info in groups.items():
        used_genes = group_to_techniques[group_id]
        if not used_genes:
            continue
            
        # Sort genes to build the Genome sequence according to kill chain
        # If multiple genes have the same tactic, sort by gene ID as a secondary key
        used_genes.sort(key=lambda g: (get_kill_chain_sort_key(g.tactic), g.id))
        
        genomes.append(Genome(
            id=group_info["ext_id"],
            name=group_info["name"],
            description=group_info["description"],
            genes=used_genes
        ))
        
    return all_genes, genomes
