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

CyberPhylogeny maps standard cybersecurity ideas into a 4-tier biological ontology:

- **Gene:** A single atomic action in an attack.
  ```text
  Tactic (e.g., Credential Access)
      ↓
  Behavior (e.g., OS Credential Dumping)
      ↓
  Implementation (e.g., LSASS Memory)
      ↓
  MITRE Technique (e.g., T1003.001)
  ```
- **Genome:** The ordered sequence of Genes that makes up a complete cyberattack.
- **Evolutionary Family:** A group of Genomes that share a common ancestor.
- **Phylogenetic Tree:** A branching graph showing exactly how a new attack evolved from an older one.

## Core Concepts

This research framework relies on the following core concepts to model attacks:

* **Genome**: The complete, ordered sequence of genes (techniques) that makes up an entire cyberattack.
* **Distance**: How different two genomes are from each other. Instead of just checking if they match exactly, we use a biological "Weighted Sequence Alignment" algorithm to score them based on how closely related their tactics and behaviors are. The **Score Calculation** is as follows: `0.0` for an Exact Match, `0.5` for a Substitution within the same Tactic, and `1.0` for an Insertion, Deletion, or cross-Tactic Substitution.
* **Prediction**: Using a biological algorithm called "Smith-Waterman" to find the strongest matching patterns in historical attacks, which allows us to predict what the attacker might do next.
* **Mutation**: The exact changes an attacker made to evolve their attack (e.g., Inserting a new technique, Deleting an old one, or Substituting one technique for another).
* **Family**: A group of attacks (genomes) that are grouped together because their "Distance" is very small, meaning they likely share the same origin or threat actor.

## The Novel Contribution: Beyond Pattern Matching

Standard Threat Intelligence tools use MITRE ATT&CK to describe what an attacker did. CyberPhylogeny introduces a new approach by shifting focus from **pattern matching** to **evolutionary reconstruction**:

1. **From Similarity to Ancestry:** Traditional systems compare two lists of techniques and give a simple score (e.g., "85% match"). CyberPhylogeny uses Minimum Spanning Trees (MST) to show *why* they are similar: *"Attack B evolved from Attack A, and here is the exact branch where it mutated."*
2. **Biological Abstraction:** Comparing raw MITRE IDs (like `T1059.001` vs `T1059.006`) treats them as completely different strings. By using the 4-part Gene hierarchy, CyberPhylogeny mathematically understands that changing PowerShell to Python is *not* a new attack—it is just a **mutation** of the same underlying "Execution" gene.
3. **Chronological Evolution vs. Heuristics:** The system parses exact timestamps from threat intelligence reports to map out the evolutionary family tree, tracing real time rather than guessing based on sequence length.
4. **Predictive Alignment vs. Reactive Detection:** CTI tools are reactive (they look at the past). CyberPhylogeny utilizes the **Smith-Waterman** local alignment algorithm to accurately predict the attacker's next move, even if they skip or add new steps mid-attack.
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
* **Family Reconstruction Accuracy**: Validating cluster purity against known threat actor group overlap (e.g., separating distinct APT29 campaigns).
* **Prediction Accuracy**: Cross-validating the Smith-Waterman matcher's ability to estimate the next gene in historical data despite active insertions/deletions.
* **Mutation Detection Accuracy**: Tracking how accurately substitutions identify polymorphic malware variants.
* **Phylogenetic Consistency**: Validating the MST branch structure against temporal cyber threat intelligence reports.

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
├── Ancestor: S1135 (MultiLayer Wiper)
│   ├── [execution] Scheduled Task/Job: Scheduled Task
│   └── [execution] Command and Scripting Interpreter: Windows Command Shell
└── Descendant: S0697 (HermeticWiper) (Evolved from S1135)
    │   Mutation Score: 4.0
    ├── [execution] Scheduled Task/Job: Scheduled Task
    ├── [execution] Command and Scripting Interpreter: Windows Command Shell
    ├── Type: Insertion    | [execution] Native API: Native API [green]<-- New Gene[/green]
    └── Type: Substitution | [stealth] Obfuscated Files: Compression [red]<-- Mutated[/red]
```

**4. Predict Next Steps** 
Estimates the attacker's most probable next behavioral gene.
```bash
python main.py predict T1566.001,T1059.001
```

---
### Authorship & Contributions
**Author:** Rakesh Pathuri

*This engine was architected and built independently by Rakesh Pathuri inspired by biological sequence analysis and an attempt to adapt it for proactive cyber defense.*
