from src.parser import fetch_mitre_data, parse_mitre_to_genomes
from src.similarity import calculate_similarity

data = fetch_mitre_data()
_, genomes = parse_mitre_to_genomes(data)

best_sim = 0.0
best_pair = None

for i in range(len(genomes)):
    for j in range(i+1, len(genomes)):
        sim = calculate_similarity(genomes[i], genomes[j])
        if sim > best_sim:
            best_sim = sim
            best_pair = (genomes[i], genomes[j])

if best_pair:
    print(f"Best similarity is {best_sim:.4f} between {best_pair[0].name} and {best_pair[1].name}")
else:
    print("No pairs found.")
