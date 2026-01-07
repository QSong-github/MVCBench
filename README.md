# MVCBench: A Multimodal Benchmark for Drug-induced Virtual Cell Phenotypes

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](./LICENSE)
[![Preprint](https://img.shields.io/badge/Preprint-bioRxiv-red)](https://www.biorxiv.org/) 

**MVCBench** is a unified multimodal framework designed to rigorously assess representation learning for virtual cell phenotyping. It serves as a methodological foundation for developing the next generation of robust and generalizable virtual cell models.

[**📖 Read the Paper**](link_to_your_paper) | [**🤗 HuggingFace Datasets**](https://huggingface.co/datasets/Boom5426/MVCBench) | [**🚀 Getting Started**](#getting-started)

---

## 🌟 Overview

Realizing a holistic **Virtual Cell** capable of accurately predicting how **chemical perturbations** reshape cellular phenotypes across transcriptional and morphological landscapes is a central goal in drug discovery. **MVCBench** overcomes the limitations of fragmented, modality-specific benchmarks by establishing a standardized methodology involving:

- **1 Million+** paired observations.
- **22 Representation Models** benchmarked (11 Molecular + 11 Single-cell FMs).
- **6 Generalization Tasks** ranging from in-domain to cross-dataset transfer.
- **Multimodal Fusion** protocols and rigoros evaluation metrics (including the **Composite Performance Score**).

### 🗝️ Key Insights
1.  **Performance Asymmetry:** Advanced molecular representations (e.g., UniMolV2, KPGT) excel in morphology but show marginal gains in gene expression tasks compared to simple fingerprints.
2.  **The Foundation Model Paradox:** While perturbation-specific models like **STATE** lead the field, many high-capacity scFMs are more susceptible to technical shifts (batch effects) than simple baselines.
3.  **Generalization Bottleneck:** Out-of-distribution generalization remains the primary challenge, with performance deteriorating sharply in cross-dataset scenarios.
4.  **Multimodal Synergy:** Gene expression and morphology provide orthogonal, synergistic contexts. **Late-stage fusion** and **fixed-ratio loss weighting** consistently outperform complex adaptive schemes.

---

## 🧬 Benchmark Zoo

We evaluate widely used Drug Molecular Representation methods and Gene Representation methods (Single-cell Foundation Models).

### 🧪 Molecule Representation Methods

| Model | Paper | Code | Stars |
| :--- | :--- | :--- | :--- |
| **KPGT** | [Nat. Commun. 2023](https://www.nature.com/articles/s41467-023-43214-1) | [GitHub](https://github.com/lihan97/kpgt) | ![Stars](https://img.shields.io/github/stars/lihan97/kpgt.svg?style=social) |
| **InfoAlign** | [arXiv 2024](https://arxiv.org/abs/2406.12056) | [GitHub](https://github.com/liugangcode/InfoAlign) | ![Stars](https://img.shields.io/github/stars/liugangcode/InfoAlign.svg?style=social) |
| **GeminiMol** | [Adv. Sci. 2024](https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202403998) | [GitHub](https://github.com/Wang-Lin-boop/GeminiMol) | ![Stars](https://img.shields.io/github/stars/Wang-Lin-boop/GeminiMol.svg?style=social) |
| **Ouroboros** | [Advanced Science 2026](https://www.biorxiv.org/content/10.1101/2025.03.18.643899v1) | [GitHub](https://github.com/Wang-Lin-boop/ouroboros) | ![Stars](https://img.shields.io/github/stars/Wang-Lin-boop/ouroboros.svg?style=social) |
| **Mole-BERT** | [ICLR 2023](https://openreview.net/forum?id=jevY-DtiZTR) | [GitHub](https://github.com/junxia97/Mole-BERT) | ![Stars](https://img.shields.io/github/stars/junxia97/Mole-BERT.svg?style=social) |
| **ChemBERTa2**| [arXiv 2022](https://arxiv.org/abs/2209.01712) | [GitHub](https://github.com/seyonechithrananda/bert-loves-chemistry) | ![Stars](https://img.shields.io/github/stars/seyonechithrananda/bert-loves-chemistry.svg?style=social) |
| **MolT5** | [EMNLP 2022](https://arxiv.org/abs/2204.11817) | [GitHub](https://github.com/blender-nlp/molt5) | ![Stars](https://img.shields.io/github/stars/blender-nlp/molt5.svg?style=social) |
| **Chemprop** | [J. Chem. Inf. Model. 2024](https://pubs.acs.org/doi/10.1021/acs.jcim.3c01250) | [GitHub](https://github.com/chemprop/chemprop) | ![Stars](https://img.shields.io/github/stars/chemprop/chemprop.svg?style=social) |
| **MolCLR** | [Nat. Mach. Intell. 2022](https://www.nature.com/articles/s42256-022-00447-x) | [GitHub](https://github.com/yuyangw/MolCLR) | ![Stars](https://img.shields.io/github/stars/yuyangw/MolCLR.svg?style=social) |
| **UniMol** | [ICLR 2023](https://openreview.net/forum?id=6K2RM6wVqKu) | [GitHub](https://github.com/deepmodeling/Uni-Mol) | ![Stars](https://img.shields.io/github/stars/deepmodeling/Uni-Mol.svg?style=social) |
| **UniMol2** | [NIPS 2024](https://openreview.net/forum?id=64V40K2fDv) | [GitHub](https://github.com/deepmodeling/Uni-Mol/tree/main/unimol2) | ![Stars](https://img.shields.io/github/stars/deepmodeling/Uni-Mol.svg?style=social) |

### 🧬 Gene Representation Methods (scFMs)

| Model | Paper | Code | Stars |
| :--- | :--- | :--- | :--- |
| **Geneformer** | [Nature 2023](https://www.nature.com/articles/s41586-023-06139-9) | [HuggingFace](https://huggingface.co/ctheodoris/Geneformer) | ⭐ 270 likes|
| **tGPT** | [bioRxiv 2022](https://www.biorxiv.org/content/10.1101/2022.01.31.478596v1.full) | [GitHub](https://github.com/deeplearningplus/tGPT) | ![Stars](https://img.shields.io/github/stars/deeplearningplus/tGPT.svg?style=social) |
| **UCE** | [bioRxiv 2023](https://www.biorxiv.org/content/10.1101/2023.11.28.568918v2) | [GitHub](https://github.com/snap-stanford/uce) | ![Stars](https://img.shields.io/github/stars/snap-stanford/uce.svg?style=social) |
| **scBERT** | [Nat. Mach. Intell. 2022](https://www.nature.com/articles/s42256-022-00534-z) | [GitHub](https://github.com/TencentAILabHealthcare/scBERT) | ![Stars](https://img.shields.io/github/stars/TencentAILabHealthcare/scBERT.svg?style=social) |
| **CellPLM** | [ICLR 2024](https://openreview.net/forum?id=BKXvPDekud) | [GitHub](https://github.com/OmicsML/CellPLM) | ![Stars](https://img.shields.io/github/stars/OmicsML/CellPLM.svg?style=social) |
| **OpenBioMed** | [arXiv 2023](https://arxiv.org/pdf/2306.04371) | [GitHub](https://github.com/PharMolix/OpenBioMed) | ![Stars](https://img.shields.io/github/stars/PharMolix/OpenBioMed.svg?style=social) |
| **scGPT** | [Nat. Methods 2024](https://www.nature.com/articles/s41592-024-02201-0) | [GitHub](https://github.com/bowang-lab/scGPT) | ![Stars](https://img.shields.io/github/stars/bowang-lab/scGPT.svg?style=social) |
| **scFoundation**| [Nat. Methods 2024](https://www.nature.com/articles/s41592-024-02305-7) | [GitHub](https://github.com/biomap-research/scFoundation)| ![Stars](https://img.shields.io/github/stars/biomap-research/scFoundation.svg?style=social) |
| **SCimilarity** | [Nature 2025](https://doi.org/10.1038/s41586-024-08411-y) | [GitHub](https://github.com/Genentech/scimilarity) | ![Stars](https://img.shields.io/github/stars/Genentech/scimilarity.svg?style=social) |
| **Cell2Sentence**| [ICML 2023](https://icml.cc/virtual/2024/poster/34580) | [GitHub](https://github.com/vandijklab/cell2sentence) | ![Stars](https://img.shields.io/github/stars/vandijklab/cell2sentence.svg?style=social) |
| **STATE** | [bioRxiv 2025](https://www.biorxiv.org/content/10.1101/2025.06.26.661135v2) | [GitHub](https://github.com/ArcInstitute/state) | ![Stars](https://img.shields.io/github/stars/ArcInstitute/state.svg?style=social) |

---

## 💾 Datasets

MVCBench leverages over one million paired observations across transcriptomic and morphological landscapes.

### Gene Expression
- **[CIGS]** (Nat. Methods 2025) - [Dataset Link](https://cigs.iomicscloud.com/)
- **[Tahoe-100M]** (bioRxiv 2025) - [HuggingFace](https://huggingface.co/datasets/tahoebio/Tahoe-100M)
- **[LINCS 2020]** - [Clue.io](https://clue.io/data/CMap2020#LINCS2020)

### Cell Morphology
- **[cpg0016 & cpg0003]** (Cell Painting Gallery) - [AWS Registry](https://registry.opendata.aws/cellpainting-gallery/)

### Multimodal (Paired)
- **CDRP-BBBC047-Bray** & **CDRPBIO-BBBC036-Bray** - Available via the [MVCBench HuggingFace](link_to_your_hf).

The preprocessed dataset used in this paper is available at [MVCBench HuggingFace](https://huggingface.co/datasets/Boom5426/MVCBench).
---


## 🧩 Embedding Extraction

MVCBench provides a unified and easy-to-use interface to extract embeddings using state-of-the-art foundation models.

### Molecular Embeddings (e.g., UniMol2)

You can easily extract molecular features from SMILES strings using our unified `MoleculeEncoder` wrapper.

```python
import torch
from mvcbench.encoders import MoleculeEncoder

# Initialize the encoder (e.g., UniMol V2, KPGT, Chemprop)
encoder = MoleculeEncoder(model_name="UniMolV2")

# Input: Single SMILES or a list of SMILES
smiles_list = [
    "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin
    "CN1C=NC2=C1C(=O)N(C(=O)N2C)C" # Caffeine
]

# Extract embeddings
# The encoder automatically handles tokenization and device placement
embeddings = encoder.encode(smiles_list)

print(f"Embedding shape: {embeddings.shape}")
# Output: torch.Size([2, 1024]) (Dimension depends on the specific model)

```

### Gene Embeddings (e.g., STATE)

Similarly, extract single-cell representations from gene expression profiles using the `GeneEncoder` wrapper.

```python
import torch
from mvcbench.encoders import GeneEncoder

# Initialize the encoder (e.g., STATE, scGPT, Geneformer)
encoder = GeneEncoder(model_name="STATE")

# Input: Gene expression tensor (batch_size, num_genes)
# Note: MVCBench handles the gene vocabulary alignment automatically
gene_expression = torch.randn(4, 19264) # Example normalized expression data

# Extract cell-level embeddings
cell_embeddings = encoder.encode(gene_expression)

print(f"Embedding shape: {cell_embeddings.shape}")
# Output: torch.Size([4, 512])

```



## 🚀 Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/QSong-github/MVCBench.git
cd MVCBench

# Create a virtual environment
conda create -n mvcbench python=3.9
conda activate mvcbench

# Install dependencies
pip install -r requirements.txt

```

### Usage

Run a basic benchmark task (e.g., drug-induced gene expression prediction):

```bash
python main.py --task gene_prediction \
               --molecule_encoder UniMolV2 \
               --gene_encoder STATE \
               --dataset LINCS2020 \
               --split leave_smiles_out

```

For multimodal fusion experiments:

```bash
python main.py --task multimodal_fusion \
               --fusion_strategy late_fusion \
               --loss_weight fixed_ratio

```

---

## 🖊️ Citation

If you find MVCBench useful for your research, please cite our paper:

```bibtex
@article{li2025mvcbench,
  title={MVCBench: A Multimodal Benchmark for Drug-induced Virtual Cell Phenotypes},
  author={Li, Bo and Wang, Qing and Wang, Shihang and Zhang, Bob and Zhou, Minghao and Peng, Yuzhong and Liu, Chengliang and Li, Mengran and Tang, Ziyang and Yao, Xiaojun and Deng, Chuxia and Song, Qianqian},
  journal={bioRxiv},
  year={2025},
  publisher={Cold Spring Harbor Laboratory}
}

```

## 📧 Contact

For any questions or inquiries, please open an issue or contact:

* **Bo Li**: Boom985426@gmail.com
* **Qianqian Song**: qsong1@ufl.edu
* **Bob Zhang**: bobzhang@um.edu.mo
