#!/bin/bash

# ==============================================================================
# MVCBench Gene Expression Prediction Benchmark Script
# Based on paper logic: Separating Molecular Benchmarks and Gene Model Benchmarks
# ==============================================================================

# 1. 设置基础参数
GPU_ID=0
EPOCHS=2 # change to 500 for train, 2 for test
BATCH_SIZE=1024
PROJECT_ROOT=".."
LOG_DIR="${PROJECT_ROOT}/results/logs_gene"
mkdir -p "$LOG_DIR"

# 2. 定义数据集列表 (根据论文 Table 1 & Methods)
# 注意：Tahoe 分为 P1-P14，这里作为示例列出部分，生产环境可用循环生成
BASIC_DATASETS=("LINCS" "CIGS" "BBBC047" "BBBC036")
TAHOE_PLATES=("Tahoe_P1" "Tahoe_P2" "Tahoe_P3" "Tahoe_P4" "Tahoe_P5" "Tahoe_P6" "Tahoe_P7" "Tahoe_P8" "Tahoe_P9" "Tahoe_P10" "Tahoe_P11" "Tahoe_P12" "Tahoe_P13" "Tahoe_P14")

# 合并所有数据集
ALL_DATASETS=("${BASIC_DATASETS[@]}" "${TAHOE_PLATES[@]}")

# 3. 定义模型列表 (根据论文 Fig. 1c & Table 2)
# 分子表征 (12种)
MOLECULE_FEATURES=(
    "ECFP4" "KPGT" "InfoAlign" "ChemBERTa2" "MolT5" 
    "Chemprop" "MolCLR" "Mole_BERT" "GeminiMol" 
    "Ouroboros" "UniMol" "UniMolV2"
)

# 基因表征 (12种，包含 Default)
GENE_ENCODERS=(
    "Default" "Geneformer" "scBERT" "Openbiomed" "SCimilarity" # Encoder-only
    "scFoundation" "scGPT" "UCE" "CellPLM" "STATE"             # Encoder-Decoder
    "tGPT" "Cell2Sentence"                                     # Decoder-only
)

echo "============================================"
echo "Starting MVCBench Gene Experiments"
echo "Log Directory: $LOG_DIR"
echo "============================================"

# ==============================================================================
# Experiment 1: 评估药物分子表征 (Benchmarking Drug Molecular Representations)
# 逻辑：固定 Gene Encoder 为 'Default' (Raw Expression)，遍历所有分子特征
# 对应论文 Fig. 2
# ==============================================================================
echo ">>> [Task 1] Benchmarking Drug Molecular Representations..."

for dataset in "${ALL_DATASETS[@]}"; do
    for mol in "${MOLECULE_FEATURES[@]}"; do
        
        # 固定基因编码器为 Default
        fixed_gene="Default"
        
        log_file="${LOG_DIR}/Task1_${dataset}_Mol-${mol}.log"
        echo "[$(date)] Running Task 1: Dataset=$dataset | Mol=$mol | Gene=$fixed_gene"
        
        CUDA_VISIBLE_DEVICES=$GPU_ID python $PROJECT_ROOT/train_gene.py \
            --dataset_name "$dataset" \
            --molecule_feature "$mol" \
            --gene_encoder_type "$fixed_gene" \
            --n_epochs $EPOCHS \
            --batch_size $BATCH_SIZE \
            --split_data_type "smiles_split" \
            --save_dir_root "${PROJECT_ROOT}/results" \
            > "$log_file" 2>&1
            
        if [ $? -eq 0 ]; then
            echo "   SUCCESS. Log: $log_file"
        else
            echo "   FAILED. Check log: $log_file"
        fi
    done
done

# ==============================================================================
# Experiment 2: 评估基因表征 (Benchmarking Gene Representations)
# 逻辑：固定 Molecule Feature 为 'ECFP4' (Baseline)，遍历所有基因模型
# 对应论文 Fig. 3
# ==============================================================================
echo ">>> [Task 2] Benchmarking Gene Representations..."

for dataset in "${ALL_DATASETS[@]}"; do
    for gene_enc in "${GENE_ENCODERS[@]}"; do
        
        # 固定分子特征为 ECFP4
        fixed_mol="ECFP4"
        
        # 避免重复跑 Task 1 已经跑过的 (ECFP4 + Default)
        if [ "$gene_enc" == "Default" ]; then
            echo "   Skipping Default+ECFP4 (Already run in Task 1)"
            continue
        fi

        log_file="${LOG_DIR}/Task2_${dataset}_Gene-${gene_enc}.log"
        echo "[$(date)] Running Task 2: Dataset=$dataset | Mol=$fixed_mol | Gene=$gene_enc"
        
        CUDA_VISIBLE_DEVICES=$GPU_ID python $PROJECT_ROOT/train_gene.py \
            --dataset_name "$dataset" \
            --molecule_feature "$fixed_mol" \
            --gene_encoder_type "$gene_enc" \
            --n_epochs $EPOCHS \
            --batch_size $BATCH_SIZE \
            --split_data_type "smiles_split" \
            --save_dir_root "${PROJECT_ROOT}/results" \
            > "$log_file" 2>&1
            
        if [ $? -eq 0 ]; then
            echo "   SUCCESS. Log: $log_file"
        else
            echo "   FAILED. Check log: $log_file"
        fi
    done
done

echo "============================================"
echo "All benchmarks completed."
echo "============================================"