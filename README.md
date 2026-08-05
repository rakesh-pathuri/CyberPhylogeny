# CyberPhylogeny: Attack Genome Engine

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Cybersecurity](https://img.shields.io/badge/Domain-Cybersecurity-red)]()
[![Machine Learning](https://img.shields.io/badge/Domain-Machine_Learning-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Abstract
Traditional cybersecurity detection relies on rigid, signature-based indicators (IOCs). However, when threat actors slightly mutate their tools or techniques, these signatures fail. 

**CyberPhylogeny** introduces a biological approach to cyber defense. By extracting the fundamental behaviors (Techniques) of an attack and treating them as structural "DNA Genomes", this engine can mathematically align, cluster, and predict cyberattacks using algorithms originally designed for computational biology (like Levenshtein distance, Jaccard Similarity, and K-Nearest Neighbors). 

This allows the engine to accurately trace how malware mutates over time and probabilistically predict an attacker's next move, even if they intentionally deviate from historical patterns.

## Core Biological Concepts
The engine translates MITRE ATT&CK concepts into biological equivalents:
- **Gene**: A single, distinct behavior (e.g., `T1566.001 Spearphishing`).
- **Genome**: The complete, ordered sequence of genes representing an entire cyberattack campaign.
- **Family**: A mathematical cluster of Genomes (threat groups or malware) proven to share a common structural ancestor.
- **Mutation**: The insertion, deletion, or substitution of a specific gene across generations of an attack.

## Research Areas & Domains
This project sits at the intersection of computational biology, data science, and threat intelligence:
1. **Bioinformatics & Sequence Alignment**: Utilizing Global Levenshtein and Subsequence Alignment to calculate the structural distance between malware genomes.
2. **Unsupervised Machine Learning**: Deploying DBSCAN density-based clustering to automatically discover evolutionary families from raw behavioral data.
3. **Probabilistic Prediction**: Utilizing Distance-Weighted K-Nearest Neighbors (KNN) to mathematically predict the highest probability next-steps of an ongoing attack.

## Project Architecture (Multi-Stage Pipeline)

```mermaid
graph TD
    A[Raw STIX Data] -->|Parser| B(Genome Database)
    
    %% Clustering Pipeline
    B -->|Stage 1: Strict Evolution| C[Primary Families]
    C -->|Stage 2: Unordered Jaccard| D[Motif Families]
    D -->|Stage 3: Taxonomic Zooming| E[Strategic Families]
    
    %% Evolution Pipeline
    C -->|Dynamic Programming Traceback| I(Evolution & Mutation Tracker)
    
    %% Prediction Pipeline
    F[Ongoing Attack Sequence] -->|Suffix Alignment| G(KNN Prediction Engine)
    B -->|Raw Historical Sequences| G
    G -->|Distance-Weighted Voting| H[Probabilistic Next Steps]
    
    style B fill:#8338ec,stroke:#333,stroke-width:2px,color:#fff
    style C fill:#3a86ff,stroke:#333,stroke-width:2px,color:#fff
    style E fill:#ff006e,stroke:#333,stroke-width:2px,color:#fff
    style H fill:#06d6a0,stroke:#333,stroke-width:2px,color:#black
    style I fill:#ffb703,stroke:#333,stroke-width:2px,color:#black
```

## Core Features

- **Multi-Stage Classification Pipeline**: Handles complex "Orphan" attacks by filtering them through three biological lenses (Strict Sequence, Jaccard Bag-of-Genes, and Tactic-level Zooming).
- **Probabilistic Prediction Engine**: Utilizes a **Distance-Weighted KNN with Sliding Window Alignment**. Instead of equal voting, it multiplies predictions by their mathematical suffix similarity, generating rigorous Confidence Multipliers to eliminate false positives.
- **Dynamic Evolution Traceback**: Maps exactly how and where an attack mutated from its evolutionary ancestor (identifying specific gene insertions, deletions, and substitutions).

## Technical Stack
- **Data Processing**: `numpy`, `scikit-learn`
- **Visualization**: `rich` (Terminal UI)
- **Database**: `SQLite3`
- **Threat Intelligence**: `MITRE ATT&CK STIX Framework`

## Installation & Usage

### Local Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/rakesh-pathuri/CyberPhylogeny.git
   cd CyberPhylogeny
   ```
2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
3. **Install Dependencies:**
   ```bash
   pip install rich scikit-learn numpy pydantic
   ```

### Command Line Interface & Examples

**1. Multi-Stage Clustering** 
Groups attacks into families based on structural similarity.
```bash
python main.py cluster --eps 0.6 --min_samples 2
```
*Example Output:*
```text
STAGE 1: Strict Evolutionary (Levenshtein) Families

Family 24 - 5 attacks
+------------------------------------------------+
| Attack /     |                 |               |
| Group ID     | Name            | Genome Length |
|--------------+-----------------+---------------|
| S0390        | SQLRat          | 8             |
| S0360        | BONDUPDATER     | 7             |
| G0133        | Nomadic Octopus | 7             |
| G0079        | DarkHydrus      | 7             |
| G0084        | Gallmaker       | 6             |
+------------------------------------------------+
```

**2. Trace Evolution** 
Visualizes the specific genetic mutations between ancestors and descendants in a family.
```bash
python main.py evolution --eps 0.6 --min_samples 2 15
```
*Example Output:*
```text
Tracing Evolution for Family 15 (5 attacks)

Evolution: Trojan.Mebromi -> Hacking Team UEFI Rootkit
  - Gene Inserted: [Rootkit]

Evolution: Hacking Team UEFI Rootkit -> Zeroaccess
  - Gene Mutated: STEALTH [System Firmware -> NTFS File Attributes]
```

**3. Predict Next Steps** 
Predicts the attacker's next move based on mathematical sequence alignment.
```bash
python main.py predict T1566.001,T1059.001
```
*Example Output:*
```text
Ongoing Attack Sequence: ['T1566.001', 'T1059.001']

Most Probable Next Behaviors:
+-------------------------------------------------------------------------+
| Predicted Gene ID | Name                  | Tactic    | Probability | Confidence |
|-------------------+-----------------------+-----------+-------------+------------|
| T1059.003         | Windows Command Shell | execution |       80.0% |      4.00x |
| T1059.007         | JavaScript            | execution |       20.0% |      1.00x |
+-------------------------------------------------------------------------+
```

---
### Authorship & Contributions
**Author:** Rakesh Pathuri

*This engine was architected and built independently by Rakesh Pathuri inspired by biological sequence analysis and an attempt to adapt it for proactive cyber defense.*
