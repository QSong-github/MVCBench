import argparse
import torch
import numpy as np
import pandas as pd
import os
from torch.utils.data import DataLoader

from src.utils import setup_seed, save_to_HDF
from src.dataset import get_datasets
from src.models import VCModel
from src.trainer import Trainer
from src.metrics import get_pcc, get_rmse

def parse_args():
    parser = argparse.ArgumentParser(description="Image Feature Prediction Training")
    
    # 数据集参数
    parser.add_argument("--dataset_name", type=str, default="cpg0016", help="BBBC047, BBBC036, cpg0016, Name of the dataset")
    parser.add_argument("--molecule_feature", type=str, default="KPGT", help="ECFP4, KPGT, MolT5, etc.")
    parser.add_argument("--image_encoder_type", type=str, default="Default") # 虽然目前逻辑里没怎么用到这个区分，但保留参数接口
    parser.add_argument("--split_data_type", type=str, default="smiles_split")
    parser.add_argument("--train_cell_count", type=str, default="None")
    
    # 训练参数
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument("--batch_size", type=int, default=1024)
    parser.add_argument("--n_epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--n_latent", type=int, default=1024)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--weight_decay", type=float, default=1e-5)
    parser.add_argument("--device", type=str, default="cuda:0")
    
    # 输出参数
    parser.add_argument("--save_dir_root", type=str, default="results")
    parser.add_argument("--predict_profile", type=bool, default=True)
    
    return parser.parse_args()

def calculate_metrics_per_sample(y_true, y_pred, centroid=None):
    """计算样本级指标"""
    metrics_list = []
    n_samples = y_true.shape[0]
    
    if centroid is not None:
        if centroid.ndim == 1: centroid = centroid.reshape(1, -1)
        delta_true = y_true - centroid
        delta_pred = y_pred - centroid

    for i in range(n_samples):
        row = {
            'pearson': get_pcc(y_true[i:i+1], y_pred[i:i+1]),
            'rmse': get_rmse(y_true[i:i+1], y_pred[i:i+1])
        }
        if centroid is not None:
            row['systema_pearson'] = get_pcc(delta_true[i:i+1], delta_pred[i:i+1])
            row['systema_rmse'] = get_rmse(delta_true[i:i+1], delta_pred[i:i+1])
        metrics_list.append(row)
    return metrics_list

def main():
    args = parse_args()
    setup_seed(args.seed)
    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')
    
    # 1. 路径构建
    experiment_name = f"{args.dataset_name}_{args.split_data_type}/{args.molecule_feature}_{args.image_encoder_type}"
    save_dir = os.path.join(args.save_dir_root, experiment_name)
    os.makedirs(save_dir, exist_ok=True)
    
    print(f"Task: Image Prediction | Dataset: {args.dataset_name} | Feat: {args.molecule_feature}")

    # 2. 数据加载 (task_type='gene' 也可以用于单模态 Image，只要 dataset key 正确)
    # 我们在 src/dataset.py 里写了通用逻辑，会自动找 control/target 或者 control_CP 等键
    train_ds, valid_ds, test_ds, meta = get_datasets(args, task_type='image')
    
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=4)
    valid_loader = DataLoader(valid_ds, batch_size=args.batch_size, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=4)
    
    print(f"Input Image Dim: {meta['input_dim']} | Mol Dim: {meta['mol_dim']}")

    # 3. 模型初始化
    model = VCModel(
        n_genes=meta['input_dim'], # 这里 n_genes 实际上就是 image feature dim
        n_emd=meta['input_dim'],
        molecule_feature_dim=meta['mol_dim'],
        n_latent=args.n_latent,
        dropout=args.dropout
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    trainer = Trainer(model, optimizer, device, task_type='gene') # task_type='gene' 意味着单模态训练逻辑
    
    # 4. 训练
    best_model_path = os.path.join(save_dir, 'best_model.pt')
    best_loss = float('inf')
    
    for epoch in range(args.n_epochs):
        train_loss = trainer.train_epoch(train_loader)
        valid_loss = trainer.evaluate(valid_loader)
        
        if epoch % 10 == 0:
            print(f"[Epoch {epoch:03d}] Train: {train_loss:.5f} | Valid: {valid_loss:.5f}")
        
        if valid_loss < best_loss:
            best_loss = valid_loss
            torch.save(model, best_model_path) # 保存整个模型，或者用 trainer.save_checkpoint

    # 5. 测试
    print("Evaluating...")
    model = torch.load(best_model_path, map_location=device, weights_only=False)
    model.eval()
    
    # 收集预测
    all_x2, all_pred, all_ids = [], [], []
    with torch.no_grad():
        for batch in test_loader:
            x1, x2, _, _, drug, ids = batch
            x1, drug = x1.to(device), drug.to(device)
            pred = model(x1, drug)
            
            all_x2.append(x2.cpu().numpy())
            all_pred.append(pred.cpu().numpy())
            all_ids.extend(ids)

    x2_arr = np.concatenate(all_x2, axis=0)
    pred_arr = np.concatenate(all_pred, axis=0)
    
    # 计算指标
    centroid = meta['centroid'].numpy() if 'centroid' in meta else None
    metrics = calculate_metrics_per_sample(x2_arr, pred_arr, centroid)
    
    # 保存 CSV
    df = pd.DataFrame(metrics)
    df['canonical_smiles'] = all_ids
    cols = ['canonical_smiles'] + [c for c in df.columns if c != 'canonical_smiles']
    df = df[cols]
    df.to_csv(os.path.join(save_dir, 'test_restruction_result_all_samples.csv'), index=False)
    
    # 保存 HDF5
    if args.predict_profile:
        save_to_HDF(os.path.join(save_dir, 'test_prediction_profile.h5'), {
            'x2': x2_arr,
            'x2_pred': pred_arr
        })
    
    print(f"Done. PCC: {df['pearson'].mean():.4f}")

if __name__ == "__main__":
    main()