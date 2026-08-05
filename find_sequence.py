from src.parser import fetch_mitre_data, parse_mitre_to_genomes
from src.prediction import PredictionEngine

data = fetch_mitre_data()
_, genomes = parse_mitre_to_genomes(data)
pe = PredictionEngine(genomes, n_gram=2)

top = sorted(pe.transition_counts.items(), key=lambda x: sum(x[1].values()), reverse=True)
for context, next_genes in top[:5]:
    print(f"Sequence {context} -> Next Genes: {next_genes}")
