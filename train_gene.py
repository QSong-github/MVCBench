import argparse
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
import numpy as np
import pandas as pd
import os
from collections import defaultdict

# 引入核心模块
from src.utils import setup_seed, save_to_HDF
from src.dataset import get_datasets
from src.models import VCModel
from src.trainer import Trainer
from src.metrics import compute_all_metrics, get_pcc, get_rmse

def parse_args():
    parser = argparse.ArgumentParser(description="Gene Expression Prediction Training")
    
    # --- 数据集配置 ---
    parser.add_argument("--dataset_name", type=str, default="BBBC047", help="LINCS, CIGS, BBBC047, BBBC036, LINCS965, Tahoe_P1, etc.")
    parser.add_argument("--molecule_feature", type=str, default="KPGT", help="ECFP4, KPGT, MolT5, etc.")
    parser.add_argument("--split_data_type", type=str, default="smiles_split", help="random_split, smiles_split, cells_split")
    parser.add_argument("--train_cell_count", type=str, default="None", help="Used only for cells_split")
    
    # --- 模型配置 ---
    parser.add_argument("--gene_encoder_type", type=str, default="Default", help="Default, scGPT, etc.")
    parser.add_argument("--n_latent", type=int, default=1024)
    parser.add_argument("--n_hidden", nargs='+', type=int, default=[512])
    
    # --- 训练配置 ---
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument("--batch_size", type=int, default=1024)
    parser.add_argument("--n_epochs", type=int, default=2) # For quick testing, set to 2 epochs
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--weight_decay", type=float, default=1e-5)
    parser.add_argument("--device", type=str, default="cuda:0")
    
    # --- 功能开关 ---
    parser.add_argument("--save_dir_root", type=str, default="results", help="Root directory for results")
    parser.add_argument("--predict_profile", type=bool, default=True, help="Whether to save prediction arrays to HDF5")
    
    return parser.parse_args()

def calculate_metrics_per_sample(y_true, y_pred, centroid=None):
    """
    计算每个样本的指标，返回字典列表，用于生成 CSV
    """
    metrics_list = []
    n_samples = y_true.shape[0]
    
    # 预计算 Systema 向量 (如果提供了中心)
    if centroid is not None:
        if centroid.ndim == 1: centroid = centroid.reshape(1, -1)
        delta_true = y_true - centroid
        delta_pred = y_pred - centroid
    
    for i in range(n_samples):
        # 基础指标
        pcc = get_pcc(y_true[i:i+1], y_pred[i:i+1])
        rmse = get_rmse(y_true[i:i+1], y_pred[i:i+1])
        
        row = {
            'pearson': pcc,
            'rmse': rmse
        }
        
        # Systema 指标
        if centroid is not None:
            sys_pcc = get_pcc(delta_true[i:i+1], delta_pred[i:i+1])
            sys_rmse = get_rmse(delta_true[i:i+1], delta_pred[i:i+1])
            row['systema_pearson'] = sys_pcc
            row['systema_rmse'] = sys_rmse
            
        metrics_list.append(row)
        
    return metrics_list

def main():
    args = parse_args()
    setup_seed(args.seed)
    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')
    
    # ==========================================
    # 1. 路径构建 (保持原来的命名风格)
    # ==========================================
    experiment_name = f"{args.dataset_name}_{args.split_data_type}/{args.molecule_feature}_{args.gene_encoder_type}"
    save_dir = os.path.join(args.save_dir_root, experiment_name)
    os.makedirs(save_dir, exist_ok=True)
    
    print(f"==================================================")
    print(f"Task: Gene Prediction")
    print(f"Dataset: {args.dataset_name} | Feature: {args.molecule_feature}")
    print(f"Save Directory: {save_dir}")
    print(f"==================================================")

    # ==========================================
    # 2. 数据加载
    # ==========================================
    print("Loading datasets...")
    # 注意：get_datasets 需要你在 src/dataset.py 中实现好
    train_ds, valid_ds, test_ds, meta = get_datasets(args, task_type='gene')
    
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=4)
    valid_loader = DataLoader(valid_ds, batch_size=args.batch_size, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=4)
    
    print(f"Train samples: {len(train_ds)} | Valid: {len(valid_ds)} | Test: {len(test_ds)}")
    print(f"Input Gene Dim: {meta['input_dim']} | Mol Dim: {meta['mol_dim']}")

    # ==========================================
    # 3. 模型初始化
    # ==========================================
    model = VCModel(
        n_genes=meta['input_dim'],
        n_emd=meta['input_dim'],
        molecule_feature_dim=meta['mol_dim'],
        n_latent=args.n_latent,
        dropout=args.dropout
        # n_en_hidden=args.n_hidden # 如果你在 VCModel 里支持了这个参数
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    
    # 使用封装好的 Trainer
    trainer = Trainer(model, optimizer, device, task_type='gene')
    
    # ==========================================
    # 4. 训练循环
    # ==========================================
    best_model_path = os.path.join(save_dir, 'best_model.pt')
    best_valid_loss = float('inf')
    
    # 如果只是测试，可以加一个参数控制跳过训练
    # if args.train_flag: ...
    
    for epoch in range(args.n_epochs):
        train_loss = trainer.train_epoch(train_loader)
        valid_loss = trainer.evaluate(valid_loader)
        
        if epoch % 10 == 0:
            print(f"[Epoch {epoch:03d}] Train Loss: {train_loss:.5f} | Valid Loss: {valid_loss:.5f}")
        
        if valid_loss < best_valid_loss:
            best_valid_loss = valid_loss
            trainer.save_checkpoint(best_model_path)
            # print(f"  -> Saved best model at epoch {epoch}")

    print("Training finished.")

    # ==========================================
    # 5. 预测与评估 (Predict Profile)
    # ==========================================
    print(f"Loading best model from {best_model_path} for evaluation...")
    model = torch.load(best_model_path, map_location=device, weights_only=False)
    model.to(device)
    model.eval()
    
    # 用于收集所有测试集数据的列表
    all_x1 = []
    all_x2 = []
    all_pred = []
    all_mol_ids = []
    
    with torch.no_grad():
        for batch in test_loader:
            # 根据 src/dataset.py 的 BaseDataset 返回值解包
            # return (x_control, x_target, x_control, x_target, mol_features, mol_ids)
            x1, x2, _, _, drug, mol_ids = batch
            
            x1 = x1.to(device)
            drug = drug.to(device)
            
            # 模型预测
            pred = model(x1, drug)
            
            # 收集数据 (转回 CPU numpy)
            all_x1.append(x1.cpu().numpy())
            all_x2.append(x2.cpu().numpy())
            all_pred.append(pred.cpu().numpy())
            all_mol_ids.extend(mol_ids) # mol_ids 通常是 tuple 或 list
            
    # 合并为大数组
    x1_arr = np.concatenate(all_x1, axis=0)
    x2_arr = np.concatenate(all_x2, axis=0)
    pred_arr = np.concatenate(all_pred, axis=0)
    mol_ids_arr = np.array(all_mol_ids)
    
    # ------------------------------------------
    # 5.1 计算指标并保存 CSV
    # ------------------------------------------
    predict_dir = os.path.join(save_dir, 'predict')
    os.makedirs(predict_dir, exist_ok=True)
    
    print("Calculating metrics per sample...")
    # 获取扰动中心 (从 meta 中获取，转为 numpy)
    centroid = meta['centroid'].numpy() if 'centroid' in meta else None
    
    # 计算每个样本的 metrics
    metrics_list = calculate_metrics_per_sample(x2_arr, pred_arr, centroid=centroid)
    
    # 转为 DataFrame
    df_metrics = pd.DataFrame(metrics_list)
    df_metrics['canonical_smiles'] = mol_ids_arr # 添加 ID 列
    # 调整列顺序，把 ID 放在第一列
    cols = ['canonical_smiles'] + [c for c in df_metrics.columns if c != 'canonical_smiles']
    df_metrics = df_metrics[cols]
    
    csv_path = os.path.join(predict_dir, 'test_restruction_result_all_samples.csv')
    df_metrics.to_csv(csv_path, index=False)
    print(f"Saved metrics CSV to: {csv_path}")
    
    # 打印平均指标
    print(f"Average Test Pearson: {df_metrics['pearson'].mean():.4f}")
    if 'systema_pearson' in df_metrics.columns:
        print(f"Average Systema Pearson: {df_metrics['systema_pearson'].mean():.4f}")

    # ------------------------------------------
    # 5.2 保存 Profile (HDF5)
    # ------------------------------------------
    if args.predict_profile:
        h5_path = os.path.join(predict_dir, 'test_prediction_profile.h5')
        print(f"Saving prediction profiles to {h5_path} ...")
        
        data_dict = {
            'x1': x1_arr,
            'x2': x2_arr,
            'x2_pred': pred_arr,
            # 如果需要，也可以存 mol_ids，但 HDF5 存字符串比较麻烦，通常存索引或单独存
        }
        
        save_to_HDF(h5_path, data_dict)
        print("Profile saved successfully.")

if __name__ == "__main__":
    main()