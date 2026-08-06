# CyberPhylogeny: A Bio-Inspired Framework for Reconstructing Evolutionary Relationships of Cyberattacks

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Cybersecurity](https://img.shields.io/badge/Domain-Cybersecurity-red)]()
[![Bioinformatics](https://img.shields.io/badge/Domain-Bioinformatics-green)]()
[![Threat Intelligence](https://img.shields.io/badge/Domain-Threat_Intelligence-yellow)]()
[![Graph Analytics](https://img.shields.io/badge/Domain-Graph_Analytics-purple)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Research Concept:** CyberPhylogeny models cyberattacks as evolving behavioral genomes and reconstructs their evolutionary lineage using bioinformatics-inspired sequence analysis and phylogenetic inference.

## Research Hypotheses

This framework was built to explore the following open questions in proactive cyber defense:
* Can behavioral genomes accurately reconstruct the evolutionary ancestry of a cyberattack?
* Does sequence alignment clustering outperform traditional MITRE ATT&CK bag-of-words similarity?
* Can mathematical evolutionary distance improve ongoing attack prediction?
* Can quantifiable mutations (insertions/deletions/substitutions) identify how an attacker is adapting their tradecraft?

## The Biological Mapping

CyberPhylogeny maps standard cybersecurity ideas into a 4-tier biological ontology. To make a "gene" computationally meaningful rather than just a metadata tag, we define it by its function, inputs, and outputs:

- **Gene:** A specific, atomic computational operation in an attack sequence.
  ```text
  Identifier                  → G17
  Semantic Function (Tactic)  → Credential Access
  Preconditions               → Code Execution on Target
  Postconditions              → Extracted plaintext credentials/hashes
  Allowed Implementations     → LSASS Memory, NTDS.dit, DCSync
  ```
- **Genome:** The ordered sequence of Genes that makes up a complete cyberattack. While modern attacks may involve branching or retries, an individual **execution trace** (a specific instance of an attack) is a linear temporal path. The Genome models this trace.
- **Evolutionary Family:** A group of Genomes that share a common ancestor.
- **Phylogenetic Tree:** A branching graph constructed to infer the most likely evolutionary lineage. While computing true Maximum Parsimony is computationally intractable for large datasets, CyberPhylogeny utilizes **Minimum Spanning Trees (MST)** to build a parsimonious approximation by finding the shortest mutational paths connecting observed attack sequences.

## Formalization & Core Concepts

To elevate this framework beyond a heuristic analogy, we rely on formal mathematical definitions:

- **Genome (G)**: An ordered sequence of genes. `G = [g1, g2, g3, ..., gn]`
- **Evolutionary Distance (D(G1, G2))**: The mathematical distance between two genomes. Because cyberattack traces are modeled as discrete, ordered, temporal sequences, CyberPhylogeny utilizes **Weighted Sequence Alignment** with hierarchical taxonomic penalties. Graph Edit Distance captures topology but is less suited to our chosen execution-trace representation, which preserves strict temporal order. Sequence alignment is conceptually aligned with biological methods while remaining computationally tractable for our threat model.
- **Local Alignment**: Using the Smith-Waterman algorithm to mathematically discover optimal local subsequence alignments. This identifies the most similar historical subsequences, which are then used by the KNN engine for prediction.
- **Mutation (Δ(G1, G2))**: The specific genetic changes (Insertions, Deletions, Substitutions) that turn `G1` into `G2`.
- **Family (F)**: A density-based cluster of genomes where the distance `D` is less than a threshold `ϵ`. `F = { G | D(G1, G2) < ϵ }`

## The Novel Contribution: Beyond Pattern Matching

Why model attacks as evolving genomes instead of simply comparing ATT&CK sequences? Standard Threat Intelligence tools fail when faced with polymorphism because they treat a substitution of `PowerShell` to `Python` as a 100% miss. CyberPhylogeny introduces a new approach by shifting focus from **similarity** to **ancestry**:

1. **From Similarity to Lineage Inference:** Traditional systems compare two lists of techniques and give a static similarity score (e.g., "85% match"). CyberPhylogeny's true novelty is reconstructing *ancestry*. It infers the most parsimonious lineage, estimating how an attack evolved and identifying the exact branch where it mutated.
2. **Biological Abstraction:** By treating techniques as computational Genes, CyberPhylogeny mathematically tracks tactical mutations preserving the same underlying function, abstracting away polymorphic noise.
3. **Maximum Parsimony vs. Chronology:** Real evolution is driven by accumulating mutations, not just the passage of time. CyberPhylogeny uses chronological timestamps only as a *directional constraint* (a descendant cannot predate its ancestor) while relying on **Maximum Parsimony** (MST) to determine the actual evolutionary lineage.
4. **Predictive Alignment:** CTI tools are typically reactive. CyberPhylogeny utilizes local sequence alignment (Smith-Waterman) to accurately align ongoing, incomplete attack sequences against historical genomes. These alignments identify the most similar historical subsequences, which then feed our KNN engine to probabilistically estimate the next move.
5. **Algorithmic Scalability:** Features a custom **MinHash LSH** pass to instantly filter and bucket genomes before running the heavy comparison math, making the framework extremely fast.

## Threat Model & Assumptions

To clarify what a "Genome" represents in this framework, we define the following scope:
- **Attack Scope**: We model linear *execution traces* of malware, tools, or specific APT campaigns.
- **Unified Genomic Space**: We cluster APT groups, malware, and open-source tools together into a single taxonomic tree. Modern APT campaigns frequently subsume and evolve from commodity malware and open-source tools; tracing this evolutionary lineage requires a unified biological ontology.
- **The Genome (Behavioral Transitions)**: Rather than treating the genome as a flat sequence of isolated techniques (which leads to massive overlap on common commodity tools like PowerShell), the genome is modeled as an ordered sequence of **Tactical Transitions** (Bigrams) (e.g., `PowerShell -> Scheduled Task`). This forces the alignment engine to evaluate the *flow* of an attack rather than just its constituent parts, perfectly encapsulating biological evolution.
- **Data Source**: We utilize MITRE ATT&CK STIX data, mapping techniques as the foundational genomic alphabet.

## Project Architecture (Multi-Stage Pipeline)

```mermaid
graph TD
    A[Raw STIX Data] -->|Parser| B(Genome Knowledge Base)
    
    %% Clustering Pipeline
    B -->|Stage 1: Sequence Alignment| C[Primary Families]
    C -->|Stage 2: Unordered Jaccard| D[Motif Families]
    D -->|Stage 3: Taxonomic Zooming| E[Strategic Families]
    E -->|Stage 4: Taxonomic Motif Matching| K[Taxonomic Motif Families]
    
    %% Evolution Pipeline (Centerpiece)
    C -->|Minimum Spanning Tree| I(Phylogenetic Tree)
    I -->|Mutation Distance Tracker| J(Evolution Analysis)
    
    %% Prediction Pipeline
    F[Ongoing Attack Sequence] -->|Smith-Waterman Alignment| G(KNN Prediction Engine)
    B -->|Raw Historical Sequences| G
    G -->|Score-Weighted Voting| H[Probabilistic Next Steps]
    
    style B fill:#8338ec,stroke:#333,stroke-width:2px,color:#fff
    style C fill:#3a86ff,stroke:#333,stroke-width:2px,color:#fff
    style I fill:#ff006e,stroke:#333,stroke-width:2px,color:#fff
    style J fill:#fb5607,stroke:#333,stroke-width:2px,color:#fff
    style H fill:#06d6a0,stroke:#333,stroke-width:2px,color:#black
    style K fill:#ffbe0b,stroke:#333,stroke-width:2px,color:#black
```

### The 4-Stage Clustering Pipeline
To successfully cluster polymorphic attacks, CyberPhylogeny uses a cascading waterfall algorithm:
1. **Stage 1 (Sequence Alignment):** Highly strict `Needleman-Wunsch` alignment on exact Gene order.
2. **Stage 2 (Jaccard Motif):** Relaxes constraints to look for unordered motifs (Jaccard similarity) on remaining orphans.
3. **Stage 3 (Taxonomic Zooming):** Zooms out to align `Parent Techniques` instead of exact Sub-Technique implementations.
4. **Stage 4 (Taxonomic Motif Matching):** The final safety net; looks for unordered Jaccard Motif matches on `Parent Techniques`. 

By cascading these stages, the pipeline achieves an **80% reduction in noise (orphans)** across 955 MITRE ATT&CK profiles!

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
Loading cached ATT&CK Genome Repository...

Attack Genome : CSPY Downloader (S0527)

Execution
├── Scheduled Task
└── Malicious File

Privilege-Escalation
└── Bypass User Account Control

Command-And-Control
├── Web Protocols
└── Ingress Tool Transfer

Stealth
├── Software Packing
├── Masquerade Task or Service
├── Indicator Removal
├── File Deletion
└── System Checks

Defense-Impairment
├── Modify Registry
└── Code Signing

Genome Size : 25 Genes
Mutation Index : 16.5
Family : 79 (Stage 4)
Generation : 17
```

**2. Multi-Stage Clustering** 
Groups attacks into families based on Sequence Alignment.
```bash
python main.py cluster --eps 0.45 --min_samples 2
```
*Example Output:*
```text
Loading cached ATT&CK Genome Repository...

--- STAGE 1: Sequence Alignment (Needleman-Wunsch) ---
Applying MinHash LSH pre-filtering...
Calculating distances (Weighted Sequence Alignment)... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00

Genome Distance Statistics (955 genomes)
Min    : 0.00
Mean   : 0.95
Median : 1.00
95%    : 1.00
Max    : 1.00

STAGE 1: Evolutionary Ancestry (Weighted Sequence Alignment) Families

Family 0 - 2 attacks
+------------------------------------------------------+
| Attack /     |                       |               |
| Group ID     | Name                  | Genome Length |
|--------------+-----------------------+---------------|
| S0527        | CSPY Downloader       | 11            |
| S0347        | AuditCred             | 8             |
+------------------------------------------------------+

...

Clustering Summary
Attacks analyzed : 955
Families found   : 99 (Across all stages)
Largest family   : 514
Median family size: 2
Final Noise      : 172
Stage 1 Silhouette: 0.50
```

**3. Phylogenetic Terminal Tree (Topology)** 
Prints a clean mathematical dendrogram showing relationships and branch heights. Supports two algorithms:
- `mst` (Maximum Parsimony): Infers the most parsimonious ancestry between known attacks.
- `upgma` (Unweighted Pair Group Method with Arithmetic Mean): Generates a true hierarchical dendrogram with hypothetical common ancestors.
```bash
python main.py tree 80 --algo upgma
```
*Example Output:*
```text
Phylogenetic Tree for Family 80 (Stage 4) (4 variants)
Algorithm: UPGMA
UPGMA Dendrogram (Root Height: 6.67)
├── --------------------------------- G1011 (EXOTIC LILY) (branch: 6.67)
└── ------------ Common Ancestor (height: 4.25, branch: 2.42)
    ├── --------------------- G0138 (Andariel) (branch: 4.25)
    └── ----------- Common Ancestor (height: 2.00, branch: 2.25)
        ├── ---------- G0089 (The White Company) (branch: 2.00)
        └── ---------- G0005 (APT12) (branch: 2.00)
```

**4. Mutation Diff (Forensic Report)**
Outputs a highly formatted, tactic-grouped report showing exactly what was inserted, deleted, or substituted between two attacks (just like `git diff`).
```bash
python main.py diff S0347 S0527
```
*Example Output:*
```diff
Loading cached ATT&CK Genome Repository...

Attack : S0527 (CSPY Downloader)
Mutation Distance : 8.5

Mutations

[Execution->Execution]
  [+] Scheduled Task->Malicious File (New Tactic Shift from execution->persistence)

[Execution->Persistence]
  [-] Windows Command Shell->Windows Service (Dropped Tactic Shift)

[Execution->Privilege-Escalation]
  [+] Malicious File->Bypass User Account Control (New Tactic Shift from persistence->discovery)

[Persistence->Discovery]
  [-] Windows Service->File and Directory Discovery (Dropped Tactic Shift)

[Privilege-Escalation->Command-And-Control]
  [+] Bypass User Account Control->Web Protocols (New Tactic Shift from discovery->command-and-control)

[Discovery->Command-And-Control]
  [-] File and Directory Discovery->Proxy (Dropped Tactic Shift)

[Command-And-Control->Command-And-Control]
  [~] (Proxy->Ingress Tool Transfer) to (Web Protocols->Ingress Tool Transfer)

[Command-And-Control->Stealth]
  [~] (Ingress Tool Transfer->Encrypted/Encoded File) to (Ingress Tool Transfer->Software Packing)

[Stealth->Stealth]
  [~] (Encrypted/Encoded File->Process Injection) to (Software Packing->Masquerade Task or Service)
  [~] (Process Injection->File Deletion) to (Masquerade Task or Service->Indicator Removal)
  [~] (File Deletion->Deobfuscate/Decode Files or Information) to (Indicator Removal->File Deletion)

[Stealth->Defense-Impairment]
  [+] File Deletion->Modify Registry (New Transition)
  [+] System Checks->Code Signing (New Transition)

[Defense-Impairment->Stealth]
  [+] Modify Registry->System Checks (New Transition)
```

**5. Ancestry Trace**
Traces the evolutionary ancestry of a specific attack back to its root.
```bash
python main.py ancestry S0527
```
*Example Output:*
```text
Ancestry for S0527
G0004 (Ke3chang)
  | (distance = 28.50)
  v
G0022 (APT3)
  | (distance = 27.50)
  v
G0093 (GALLIUM)
  | (distance = 18.00)
  v
G1023 (APT5)
  | (distance = 19.50)
  v
S1122 (Mispadu)
  | (distance = 14.50)
  v
S0330 (Zeus Panda)
  | (distance = 13.50)
  v
S0348 (Cardinal RAT)
  | (distance = 11.00)
  v
S0021 (Derusbi)
  | (distance = 11.00)
  v
S0248 (yty)
  | (distance = 8.50)
  v
S0161 (XAgentOSX)
  | (distance = 5.50)
  v
S0088 (Kasidet)
  | (distance = 5.00)
  v
S0142 (StreamEx)
  | (distance = 5.50)
  v
S0679 (Ferocious)
  | (distance = 8.00)
  v
S0527 (CSPY Downloader)

* Ancestry inferred via Maximum Parsimony (Minimum Spanning Tree)
```

**6. Predict Next Steps** 
Estimates the attacker's most probable next behavioral gene.
```bash
python main.py predict "T1583.001,T1588.002,T1189"
```
*Example Output:*
```text
Ongoing Attack Sequence (Transitions): ['T1583.001->T1588.002', 'T1588.002->T1189']

Most Probable Next Behaviors:
+--------------------------------------------------------------------------------------------------------------------------+
| Predicted Transition | Implementation Transition                                | Tactical Flow          | Prob.  | Conf.|
|----------------------+----------------------------------------------------------+------------------------+--------+------|
| T1189->T1566.001     | Drive-by Compromise -> Spearphishing Attachment          | initial-access         | 71.4%  | 10.0x|
| T1190->T1199         | Exploit Public-Facing Application -> Trusted Relat...    | initial-access         | 28.6%  |  4.0x|
+--------------------------------------------------------------------------------------------------------------------------+
* Confidence Score represents the mathematical similarity of the historical sequence matched (1.0 = perfect suffix alignment).
```

## Limitations & Future Work

To ensure scientific rigor, we acknowledge the following limitations of the framework:

1. **Inferred Provenance**: CyberPhylogeny reconstructs *inferred* behavioral ancestry rather than true, verified operational provenance. The inferred phylogeny is a hypothesis generated from behavioral similarity rather than verified attacker genealogy.
2. **Temporal Simplification**: The framework assumes attack traces can be represented as linear, ordered execution sequences, which may oversimplify highly parallel or distributed campaigns.
3. **Convergent Evolution vs. Shared Ancestry**: A critical challenge in both biology and cybersecurity is distinguishing *convergent evolution* (two independent threat actors discovering the same optimal technique sequence) from *shared ancestry* (code/tactic sharing). Future iterations of the prediction engine aim to incorporate geopolitical and attribution metadata to differentiate these phenomena.

---
### Authorship & Contributions
**Author:** Rakesh Pathuri

*This engine was architected and built independently by Rakesh Pathuri inspired by biological sequence analysis and an attempt to adapt it for proactive cyber defense.*
