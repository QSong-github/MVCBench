#!/bin/bash

# ==============================================================================
# MVCBench Image (Morphology) Prediction Benchmark Script
# Task: Evaluating Drug-to-Image Prediction
# Datasets: BBBC047, BBBC036
# ==============================================================================

# 1. 基础配置
GPU_ID=0
EPOCHS=2            # 单模态图像任务通常收敛较快
BATCH_SIZE=1024
PROJECT_ROOT=".."
LOG_DIR="${PROJECT_ROOT}/results/logs_image"
mkdir -p "$LOG_DIR"

# 2. 定义数据集
# 注意：这里使用单模态 Image 的键名 (BBBC047, BBBC036)
IMAGE_DATASETS=("BBBC047" "BBBC036" "cpg0016")

# 3. 定义分子表征 (12种)
MOLECULE_FEATURES=(
    "ECFP4"
    #  "KPGT" "InfoAlign" "ChemBERTa2" "MolT5" 
    # "Chemprop" "MolCLR" "Mole_BERT" "GeminiMol" 
    # "Ouroboros" "UniMol" "UniMolV2"
)

# 4. 图像编码器 (默认使用 CellProfiler Features)
IMAGE_ENCODER="Default"

echo "============================================"
echo "Starting Image Prediction Benchmarks"
echo "Log Directory: $LOG_DIR"
echo "============================================"

for dataset in "${IMAGE_DATASETS[@]}"; do
    for mol in "${MOLECULE_FEATURES[@]}"; do
        
        log_file="${LOG_DIR}/${dataset}_Mol-${mol}.log"
        
        echo "[$(date)] Running Image Task: Dataset=$dataset | Mol=$mol | Encoder=$IMAGE_ENCODER"
        
        # 调用 train_image.py
        CUDA_VISIBLE_DEVICES=$GPU_ID python $PROJECT_ROOT/train_image.py \
            --dataset_name "$dataset" \
            --molecule_feature "$mol" \
            --image_encoder_type "$IMAGE_ENCODER" \
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
echo "Image Benchmarks Completed."
echo "============================================"