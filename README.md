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

* **Genome ($G$)**: An ordered sequence of computationally meaningful genes: $G = [g_1, g_2, \dots, g_n]$.
* **Mutation ($\Delta(G_1, G_2)$)**: The specific genetic changes (Insertions, Deletions, Substitutions) required to transform $G_1$ into $G_2$.
* **Distance ($D(G_1, G_2)$)**: The tactical distance between two genomes. Instead of binary pattern matching, we calculate evolutionary distance using a biological **Weighted Sequence Alignment** algorithm. 
  * *Score Calculation:* `0.0` (Exact Match), `0.5` (Same-Tactic Substitution), `1.0` (Insertion/Deletion/Cross-Tactic Substitution).
* **Prediction**: Using the **Smith-Waterman** algorithm for optimal local sequence alignment to generate distance metrics, which are then fed into a **k-Nearest Neighbors (KNN)** probabilistic prediction engine to estimate the attacker's next move.
* **Family ($F$)**: A density-based cluster of genomes where the distance $D$ is less than a threshold $\epsilon$: $F = \{ G \mid D(G_1, G_2) < \epsilon \}$.

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

**3. Phylogenetic Terminal Tree (Core Feature)** 
Prints a branching evolutionary tree with Mutation Scores.
```bash
python main.py tree 24
```
*Example Output:*
```text
Phylogenetic Tree for Family 24 (2 variants)
Evolutionary Tree
├── Ancestor: S0263 (TYPEFRAME)
│   ├── [execution] Command and Scripting Interpreter: Windows Command Shell
│   ├── [execution] User Execution: Malicious File
│   ├── [persistence] Create or Modify System Process: Windows Service
│   └── [discovery] File and Directory Discovery: File and Directory Discovery
└── Descendant: S0527 (CSPY Downloader) (Evolved from S0263)
    ├── Mutation Score: 7.5
    ├── Type: Substitution | [execution] Scheduled Task/Job: Scheduled Task <-- Mutated (from Windows Command Shell)
    ├── Type: Tactic Shift | [execution] User Execution: Malicious File <-- Tactic Shift (from [persistence] Windows Service)
    ├── Type: Tactic Shift | [privilege-escalation] Abuse Elevation Control Mechanism: Bypass User Account Control <-- Tactic Shift (from [discovery] File and Directory Discovery)
    └── Type: Insertion    | [defense-impairment] Subvert Trust Controls: Code Signing <-- New Gene
* Score Calculation: 0.0 (Exact Match) | 0.5 (Substitution within same Tactic) | 1.0 (Insertion / Deletion / Cross-Tactic Substitution)
```

**4. Predict Next Steps** 
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
