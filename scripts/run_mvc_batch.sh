#!/bin/bash

# ==============================================================================
# MVCBench Multimodal Prediction Benchmark Script
# Task: Evaluating MVC Model Performance with different Molecular Embeddings
# Datasets: MVC_BBBC047, MVC_BBBC036
# ==============================================================================

# 1. 基础配置
GPU_ID=0
EPOCHS=300            # MVC 模型参数较多，通常需要较多轮次收敛
BATCH_SIZE=1024
LR=1e-3
PROJECT_ROOT=".."
LOG_DIR="${PROJECT_ROOT}/results/logs_mvc"
mkdir -p "$LOG_DIR"

# 2. 定义数据集 (MVC 专用键名，对应 configs.py)
MVC_DATASETS=("MVC_BBBC047" "MVC_BBBC036")

# 3. 定义分子表征 (12种)
MOLECULE_FEATURES=(
    "ECFP4" "KPGT" "InfoAlign" "ChemBERTa2" "MolT5" 
    "Chemprop" "MolCLR" "Mole_BERT" "GeminiMol" 
    "Ouroboros" "UniMol" "UniMolV2"
)

echo "============================================"
echo "Starting MVC Benchmarks"
echo "Log Directory: $LOG_DIR"
echo "============================================"

for dataset in "${MVC_DATASETS[@]}"; do
    for mol in "${MOLECULE_FEATURES[@]}"; do
        
        # 定义日志文件
        log_file="${LOG_DIR}/${dataset}_Mol-${mol}.log"
        
        echo "[$(date)] Running MVC: Dataset=$dataset | Mol=$mol"
        
        # 调用 train_mvc.py
        CUDA_VISIBLE_DEVICES=$GPU_ID python $PROJECT_ROOT/train_mvc.py \
            --dataset_name "$dataset" \
            --molecule_feature "$mol" \
            --n_epochs $EPOCHS \
            --batch_size $BATCH_SIZE \
            --lr $LR \
            --split_data_type "smiles_split" \
            --save_dir_root "${PROJECT_ROOT}/results" \
            > "$log_file" 2>&1
            
        # 状态检查
        if [ $? -eq 0 ]; then
            echo "   SUCCESS. Log: $log_file"
        else
            echo "   FAILED. Check log: $log_file"
        fi
        
    done
done

echo "============================================"
echo "MVC Benchmarks Completed."
echo "============================================"