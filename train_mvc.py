import argparse
import torch
import numpy as np
import pandas as pd
import os
from collections import defaultdict
from torch.utils.data import DataLoader

# 引入核心模块
from src.utils import setup_seed, save_to_HDF
from src.dataset import get_datasets
from src.models import MVCModel
from src.trainer import Trainer
from src.metrics import get_pcc, get_rmse

def parse_args():
    parser = argparse.ArgumentParser(description="Multi-View Coding (MVC) Training")
    
    # --- 数据集配置 ---
    # MVC 任务通常使用特定的组合数据集，如 MVC_BBBC047
    parser.add_argument("--dataset_name", type=str, default="MVC_BBBC047", help="Key name in configs.py")
    parser.add_argument("--molecule_feature", type=str, default="ECFP4")
    parser.add_argument("--split_data_type", type=str, default="smiles_split")
    parser.add_argument("--train_cell_count", type=str, default="None")
    
    # --- 模型配置 ---
    parser.add_argument("--n_latent", type=int, default=1024)
    parser.add_argument("--n_hidden", nargs='+', type=int, default=[512])
    
    # --- 训练配置 ---
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument("--batch_size", type=int, default=1024)
    parser.add_argument("--n_epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--weight_decay", type=float, default=1e-5)
    parser.add_argument("--device", type=str, default="cuda:0")
    
    # --- 输出配置 ---
    parser.add_argument("--save_dir_root", type=str, default="results")
    parser.add_argument("--predict_profile", type=bool, default=True)
    
    return parser.parse_args()

def calculate_mvc_metrics(y_true, y_pred, centroid=None, prefix=""):
    """
    辅助函数：计算单一样本在某一模态下的指标
    """
    row = {}
    
    # 基础指标
    row[f'{prefix}pearson'] = get_pcc(y_true, y_pred)
    row[f'{prefix}rmse'] = get_rmse(y_true, y_pred)
    
    # Systema 指标
    if centroid is not None:
        if centroid.ndim == 1: centroid = centroid.reshape(1, -1)
        delta_true = y_true - centroid
        delta_pred = y_pred - centroid
        
        row[f'{prefix}systema_pearson'] = get_pcc(delta_true, delta_pred)
        row[f'{prefix}systema_rmse'] = get_rmse(delta_true, delta_pred)
        
    return row

def main():
    args = parse_args()
    setup_seed(args.seed)
    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')
    
    # ==========================================
    # 1. 路径构建
    # ==========================================
    experiment_name = f"{args.dataset_name}_{args.split_data_type}/{args.molecule_feature}_Default"
    save_dir = os.path.join(args.save_dir_root, experiment_name)
    os.makedirs(save_dir, exist_ok=True)
    
    print(f"==================================================")
    print(f"Task: MVC Prediction (Image + Gene + Drug)")
    print(f"Dataset: {args.dataset_name} | Feature: {args.molecule_feature}")
    print(f"Save Directory: {save_dir}")
    print(f"==================================================")

    # ==========================================
    # 2. 数据加载
    # ==========================================
    print("Loading MVC datasets...")
    # task_type='mvc' 确保返回包含 'control_cp', 'target_ge' 等键的 dict
    train_ds, valid_ds, test_ds, meta = get_datasets(args, task_type='mvc')
    
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=4)
    valid_loader = DataLoader(valid_ds, batch_size=args.batch_size, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=4)
    
    print(f"Train: {len(train_ds)} | Valid: {len(valid_ds)} | Test: {len(test_ds)}")
    print(f"Dims -> Image: {meta['n_images']} | Gene: {meta['n_genes']} | Mol: {meta['mol_dim']}")

    # ==========================================
    # 3. 模型初始化
    # ==========================================
    model = MVCModel(
        n_images=meta['n_images'],
        n_genes=meta['n_genes'],
        molecule_feature_dim=meta['mol_dim'],
        n_latent=args.n_latent,
        dropout=args.dropout
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    
    # Trainer 内部会自动处理 MVC 的 Loss 计算 (MSE_CP + MSE_GE)
    trainer = Trainer(model, optimizer, device, task_type='mvc')
    
    # ==========================================
    # 4. 训练循环
    # ==========================================
    best_model_path = os.path.join(save_dir, 'best_model.pt')
    best_valid_loss = float('inf')
    
    for epoch in range(args.n_epochs):
        train_loss = trainer.train_epoch(train_loader)
        valid_loss = trainer.evaluate(valid_loader)
        
        if epoch % 10 == 0:
            print(f"[Epoch {epoch:03d}] Train: {train_loss:.5f} | Valid: {valid_loss:.5f}")
        
        if valid_loss < best_valid_loss:
            best_valid_loss = valid_loss
            trainer.save_checkpoint(best_model_path)

    print("Training finished.")

    # ==========================================
    # 5. 预测与评估
    # ==========================================
    print(f"Loading best model for evaluation...")
    model = torch.load(best_model_path, map_location=device, weights_only=False)
    model.to(device)
    model.eval()
    
    # 数据容器
    results = defaultdict(list)
    mol_ids_list = []
    
    with torch.no_grad():
        for batch in test_loader:
            # 数据搬运
            c_cp = batch['control_cp'].to(device)
            c_ge = batch['control_ge'].to(device)
            drug = batch['drug'].to(device)
            t_cp = batch['target_cp'].to(device) # 真值
            t_ge = batch['target_ge'].to(device) # 真值
            ids = batch['mol_id']
            
            # 预测
            pred_cp, pred_ge = model(c_cp, c_ge, drug)
            
            # 收集 (转回 CPU numpy)
            results['x1_cp'].append(c_cp.cpu().numpy())
            results['x1_ge'].append(c_ge.cpu().numpy())
            results['x2_cp'].append(t_cp.cpu().numpy())
            results['x2_ge'].append(t_ge.cpu().numpy())
            results['pred_cp'].append(pred_cp.cpu().numpy())
            results['pred_ge'].append(pred_ge.cpu().numpy())
            mol_ids_list.extend(ids)

    # 拼接大数组
    final_data = {k: np.concatenate(v, axis=0) for k, v in results.items()}
    mol_ids_arr = np.array(mol_ids_list)
    n_samples = len(mol_ids_arr)
    
    # ------------------------------------------
    # 5.1 计算指标并保存 CSV
    # ------------------------------------------
    print("Calculating metrics per sample...")
    
    # 获取两个模态的扰动中心
    centroid_cp = meta['centroid']['cp'].numpy() if 'centroid' in meta else None
    centroid_ge = meta['centroid']['ge'].numpy() if 'centroid' in meta else None
    
    metrics_rows = []
    for i in range(n_samples):
        # Image Metrics
        m_cp = calculate_mvc_metrics(
            final_data['x2_cp'][i:i+1], 
            final_data['pred_cp'][i:i+1], 
            centroid=centroid_cp, 
            prefix="img_"
        )
        # Gene Metrics
        m_ge = calculate_mvc_metrics(
            final_data['x2_ge'][i:i+1], 
            final_data['pred_ge'][i:i+1], 
            centroid=centroid_ge, 
            prefix="gene_"
        )
        
        # 合并
        row = {**m_cp, **m_ge}
        metrics_rows.append(row)
        
    df_metrics = pd.DataFrame(metrics_rows)
    df_metrics['canonical_smiles'] = mol_ids_arr
    
    # 调整列顺序: ID在前
    cols = ['canonical_smiles'] + [c for c in df_metrics.columns if c != 'canonical_smiles']
    df_metrics = df_metrics[cols]
    
    # 保存 CSV
    csv_path = os.path.join(save_dir, 'test_restruction_result_all_samples.csv')
    df_metrics.to_csv(csv_path, index=False)
    print(f"Metrics saved to: {csv_path}")
    
    # 打印概览
    print("\n===== Test Summary =====")
    print(f"Image Pearson: {df_metrics['img_pearson'].mean():.4f}")
    print(f"Gene Pearson:  {df_metrics['gene_pearson'].mean():.4f}")
    if 'img_systema_pearson' in df_metrics.columns:
        print(f"Image Systema PCC: {df_metrics['img_systema_pearson'].mean():.4f}")
        print(f"Gene Systema PCC:  {df_metrics['gene_systema_pearson'].mean():.4f}")

    # ------------------------------------------
    # 5.2 保存 Profile (HDF5)
    # ------------------------------------------
    if args.predict_profile:
        h5_path = os.path.join(save_dir, 'test_prediction_profile.h5')
        print(f"Saving prediction profiles to {h5_path} ...")
        
        # 直接使用 final_data 字典
        save_to_HDF(h5_path, final_data)
        print("Profile saved successfully.")

if __name__ == "__main__":
    main()