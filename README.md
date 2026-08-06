# CyberPhylogeny: A Bio-Inspired Framework for Reconstructing Evolutionary Relationships of Cyberattacks

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Cybersecurity](https://img.shields.io/badge/Domain-Cybersecurity-red)]()
[![Bioinformatics](https://img.shields.io/badge/Domain-Bioinformatics-green)]()
[![Threat Intelligence](https://img.shields.io/badge/Domain-Threat_Intelligence-yellow)]()
[![Graph Analytics](https://img.shields.io/badge/Domain-Graph_Analytics-purple)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Research Concept:** CyberPhylogeny models cyberattacks as evolving behavioral genomes and reconstructs their evolutionary lineage using bioinformatics-inspired sequence analysis and phylogenetic inference.

## Current Research Questions

This framework was built to explore the following open questions in proactive cyber defense:
* Can behavioral genomes accurately reconstruct the evolutionary ancestry of a cyberattack?
* Does sequence alignment clustering outperform traditional MITRE ATT&CK bag-of-words similarity?
* Can mathematical evolutionary distance improve ongoing attack prediction?
* Can quantifiable mutations (insertions/deletions/substitutions) identify how an attacker is adapting their tradecraft?

## The Biological Mapping

CyberPhylogeny maps standard cybersecurity ideas into a 4-tier biological ontology. To make a "gene" computationally meaningful rather than just a metadata tag, we define it by its function, inputs, and outputs:

- **Gene:** A specific, atomic operation in an attack sequence.
  ```text
  Function (Tactic)             → Credential Access
  Inputs/Outputs (Behavior)     → OS Credential Dumping
  Execution (Implementation)    → LSASS Memory
  MITRE ID (Reference)          → T1003.001
  ```
- **Genome:** The ordered sequence of Genes that makes up a complete cyberattack. While modern attacks may involve branching or retries, an individual **execution trace** (a specific instance of an attack) is a linear temporal path. The Genome models this trace.
- **Evolutionary Family:** A group of Genomes that share a common ancestor.
- **Phylogenetic Tree:** A branching graph constructed using **Maximum Parsimony** (approximated via Minimum Spanning Trees) to infer the most likely evolutionary lineage by minimizing the total number of required mutations.

## Formalization & Core Concepts

To elevate this framework beyond a heuristic analogy, we rely on formal mathematical definitions:

- **Genome (G)**: An ordered sequence of genes. `G = [g1, g2, g3, ..., gn]`
- **Distance (D(G1, G2))**: The mathematical distance between two genomes using a Weighted Sequence Alignment algorithm with hierarchical taxonomic penalties.
- **Local Alignment (Prediction)**: Using the Smith-Waterman algorithm to mathematically discover optimal local subsequence matches to predict subsequent evolutionary steps.
- **Mutation (Δ(G1, G2))**: The specific genetic changes (Insertions, Deletions, Substitutions) that turn `G1` into `G2`.
- **Family (F)**: A density-based cluster of genomes where the distance `D` is less than a threshold `ϵ`. `F = { G | D(G1, G2) < ϵ }`

## The Novel Contribution: Beyond Pattern Matching

Why model attacks as evolving genomes instead of simply comparing ATT&CK sequences? Standard Threat Intelligence tools fail when faced with polymorphism because they treat a substitution of `PowerShell` to `Python` as a 100% miss. CyberPhylogeny introduces a new approach by shifting focus from **similarity** to **ancestry**:

1. **From Similarity to Ancestry:** Traditional systems compare two lists of techniques and give a similarity score (e.g., "85% match"). CyberPhylogeny reconstructs *ancestry*: "Attack B evolved from Attack A, and here is the exact branch where it mutated."
2. **Biological Abstraction:** By treating techniques as computational Genes, CyberPhylogeny mathematically understands that changing PowerShell to Python is *not* a new attack—it is just a tactical **mutation** preserving the same underlying function.
3. **Maximum Parsimony vs. Chronology:** Real evolution is driven by accumulating mutations, not just the passage of time. CyberPhylogeny uses chronological timestamps only as a *directional constraint* (a descendant cannot predate its ancestor) while relying on **Maximum Parsimony** (MST) to determine the actual evolutionary lineage.
4. **Predictive Alignment:** CTI tools are reactive. CyberPhylogeny utilizes local sequence alignment (Smith-Waterman) to accurately align ongoing, incomplete attack sequences against historical genomes, which feeds our KNN engine to predict the next move even if the attacker skips steps.
5. **Algorithmic Scalability:** Features a custom **MinHash LSH** pass to instantly filter and bucket genomes before running the heavy comparison math, making the framework extremely fast.

## Project Architecture (Multi-Stage Pipeline)

```mermaid
graph TD
    A[Raw STIX Data] -->|Parser| B(Genome Knowledge Base)
    
    %% Clustering Pipeline
    B -->|Sequence Alignment| C[Primary Families]
    C -->|Unordered Jaccard| D[Motif Families]
    D -->|Taxonomic Zooming| E[Strategic Families]
    
    %% Evolution Pipeline (Centerpiece)
    C -->|Minimum Spanning Tree| I(Phylogenetic Tree)
    I -->|Mutation Score Tracker| J(Evolution Analysis)
    
    %% Prediction Pipeline
    F[Ongoing Attack Sequence] -->|Smith-Waterman Alignment| G(KNN Prediction Engine)
    B -->|Raw Historical Sequences| G
    G -->|Score-Weighted Voting| H[Probabilistic Next Steps]
    
    style B fill:#8338ec,stroke:#333,stroke-width:2px,color:#fff
    style C fill:#3a86ff,stroke:#333,stroke-width:2px,color:#fff
    style I fill:#ff006e,stroke:#333,stroke-width:2px,color:#fff
    style J fill:#fb5607,stroke:#333,stroke-width:2px,color:#fff
    style H fill:#06d6a0,stroke:#333,stroke-width:2px,color:#black
```

## Evaluation Metrics

To validate the framework's efficacy against traditional CTI, CyberPhylogeny utilizes the following evaluation framework:
* **Similarity Accuracy**: Benchmarking Sequence Alignment vs raw Jaccard similarity.
* **Family Reconstruction Accuracy**: Validating cluster purity against ground truth datasets, including known MITRE ATT&CK Group overlaps and specific APT threat intelligence reports (e.g., isolating distinct APT29 evolutionary branches).
* **Prediction Accuracy**: Cross-validating the KNN prediction engine's ability to estimate the next gene in historical data despite active insertions/deletions.
* **Mutation Detection Accuracy**: Tracking how accurately substitutions identify polymorphic malware variants.
* **Phylogenetic Consistency**: Validating the Maximum Parsimony tree structure against temporal CTI reports.

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
   pip install rich scikit-learn numpy pydantic requests
   ```

### Command Line Interface & Examples

**1. Inspect an Attack Genome**
Pulls the complete genetic sequence of a specific attack.
```bash
python main.py genome S0697
```
*Example Output:*
```text
Genome Profile: HermeticWiper (S0697)
[HermeticWiper](https://attack.mitre.org/software/S0697) is a data wiper that 
has been used since at least early 2022, primarily against Ukraine...

Genetic Sequence (26 Genes)
+-------------------------------------------------------------------------------------------------+
| Index | Technique ID | Implementation        | Behavior              | Tactic                   |
|-------+--------------+-----------------------+-----------------------+--------------------------|
| 1     | T1053.005    | Scheduled Task        | Scheduled Task/Job    | execution                |
| 2     | T1059.003    | Windows Command Shell | Command and Scripting | execution                |
| 3     | T1106        | Native API            | Native API            | execution                |
| ...   | ...          | ...                   | ...                   | ...                      |
+-------------------------------------------------------------------------------------------------+
```

**2. Multi-Stage Clustering** 
Groups attacks into families based on Sequence Alignment.
```bash
python main.py cluster --eps 0.6 --min_samples 2
```

**3. Phylogenetic Terminal Tree (Topology)** 
Prints a clean mathematical dendrogram showing relationships and branch heights. Supports two algorithms:
- `mst` (Maximum Parsimony): Traces exact descent between known attacks.
- `upgma` (Unweighted Pair Group Method with Arithmetic Mean): Generates a true hierarchical dendrogram with hypothetical common ancestors.
```bash
python main.py tree 24 --algo upgma
```
*Example Output:*
```text
Phylogenetic Tree for Family 24 (3 variants)
Algorithm: UPGMA
UPGMA Dendrogram (Root Height: 3.88)
+-- S0527 (CSPY Downloader) (branch: 3.88)
`-- Common Ancestor (height: 3.50, branch: 0.38)
    +-- S0347 (AuditCred) (branch: 3.50)
    `-- S0263 (TYPEFRAME) (branch: 3.50)
```

**4. Mutation Diff (Forensic Report)**
Outputs a highly formatted, tactic-grouped report showing exactly what was inserted, deleted, or substituted between two attacks (just like `git diff`).
```bash
python main.py diff S0347 S0527
```
*Example Output:*
```text
Attack : S0527 (CSPY Downloader)
Mutation Score : 7.5

Mutations

[Execution]
  [~] Windows Command Shell -> Scheduled Task
  [~] Windows Service (from persistence) -> Malicious File

[Privilege-Escalation]
  [~] File and Directory Discovery (from discovery) -> Bypass User Account Control
```

**5. Lineage Trace**
Traces the evolutionary chain of a specific attack back to its root.
```bash
python main.py lineage S0527
```
*Example Output:*
```text
Lineage for S0527
Root: S0263 (TYPEFRAME)
`-- S0347 (AuditCred)
    `-- S0527 (CSPY Downloader)
```

**6. Predict Next Steps** 
Estimates the attacker's most probable next behavioral gene.
```bash
python main.py predict T1566.001,T1059.001
```
*Example Output:*
```text
Ongoing Attack Sequence: ['T1566.001', 'T1059.001']

Most Probable Next Behaviors:
+-------------------------------------------------------------------------------------------------+
| Technique ID | Implementation        | Behavior              | Tactic    | Prob   | Confidence  |
|--------------+-----------------------+-----------------------+-----------+--------+-------------|
| T1059.003    | Windows Command Shell | Command and Scripting | execution | 33.3%  | 6.00x       |
| T1204.002    | Malicious File        | User Execution        | execution | 33.3%  | 6.00x       |
| T1059.005    | Visual Basic          | Command and Scripting | execution | 33.3%  | 6.00x       |
+-------------------------------------------------------------------------------------------------+
* Confidence Score represents the mathematical similarity of the historical sequence matched.
```

---
### Authorship & Contributions
**Author:** Rakesh Pathuri

*This engine was architected and built independently by Rakesh Pathuri inspired by biological sequence analysis and an attempt to adapt it for proactive cyber defense.*
