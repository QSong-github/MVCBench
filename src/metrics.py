# src/metrics.py
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import mean_squared_error

def get_pcc(y_true, y_pred):
    """
    计算样本级 Pearson Correlation Coefficient (PCC)
    y_true, y_pred: shape [N, Features]
    """
    # 逐行计算 PCC，避免慢速循环
    # Centering
    x_centered = y_true - np.mean(y_true, axis=1, keepdims=True)
    y_centered = y_pred - np.mean(y_pred, axis=1, keepdims=True)
    
    # Numerator: dot product
    numerator = np.sum(x_centered * y_centered, axis=1)
    
    # Denominator: product of norms
    denominator = np.sqrt(np.sum(x_centered**2, axis=1)) * np.sqrt(np.sum(y_centered**2, axis=1))
    
    # Avoid division by zero
    pccs = numerator / (denominator + 1e-8)
    return np.mean(pccs)

def get_rmse(y_true, y_pred):
    """计算样本级 RMSE"""
    mse = np.mean((y_true - y_pred)**2, axis=1)
    return np.mean(np.sqrt(mse))

def compute_all_metrics(y_true, y_pred, centroid=None, prefix=""):
    """
    计算一套完整的指标，包括 Raw Metrics 和 Systema Metrics
    
    Args:
        y_true: 真实值 (numpy array)
        y_pred: 预测值 (numpy array)
        centroid: 扰动中心 (numpy array, optional). 如果提供，将计算 Systema 指标.
        prefix: 指标名称前缀 (e.g., "gene_", "img_")
    
    Returns:
        dict: 包含所有指标的字典
    """
    metrics = {}
    
    # 1. 基础指标 (Raw Expression)
    metrics[f"{prefix}pcc"] = get_pcc(y_true, y_pred)
    metrics[f"{prefix}rmse"] = get_rmse(y_true, y_pred)
    
    # 2. Systema 指标 (Relative to Centroid)
    # 逻辑：预测的是“扰动带来的变化方向”是否正确
    if centroid is not None:
        # 确保 centroid 维度匹配
        if centroid.ndim == 1:
            centroid = centroid.reshape(1, -1)
            
        delta_true = y_true - centroid
        delta_pred = y_pred - centroid
        
        metrics[f"{prefix}systema_pcc"] = get_pcc(delta_true, delta_pred)
        metrics[f"{prefix}systema_rmse"] = get_rmse(delta_true, delta_pred)
        
    return metrics