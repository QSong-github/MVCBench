# src/trainer.py
import torch
import torch.nn.functional as F
import numpy as np
import pandas as pd
from collections import defaultdict
import os

class Trainer:
    def __init__(self, model, optimizer, device, task_type='gene'):
        self.model = model
        self.optimizer = optimizer
        self.device = device
        self.task_type = task_type
        
    def train_epoch(self, loader):
        self.model.train()
        total_loss = 0
        count = 0
        
        for batch in loader:
            self.optimizer.zero_grad()
            loss = self._compute_loss(batch)
            if loss is None: continue # Skip single-sample batches
            
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item() * self._get_batch_size(batch)
            count += self._get_batch_size(batch)
            
        return total_loss / count

    def evaluate(self, loader, centroid=None):
        self.model.eval()
        total_loss = 0
        count = 0
        # 预留用于存储 Metrics 的列表
        preds_all = []
        targets_all = []
        
        with torch.no_grad():
            for batch in loader:
                loss = self._compute_loss(batch)
                total_loss += loss.item() * self._get_batch_size(batch)
                count += self._get_batch_size(batch)
                
                # 收集预测值用于后续指标计算 (这里简化处理，实际可参考 metrics.py)
                # ...
                
        return total_loss / count

    def _compute_loss(self, batch):
        """处理 Gene/Image 和 MVC 不同的输入逻辑"""
        if self.task_type == 'mvc':
            # MVC Dataset 返回的是 dict
            ctrl_cp = batch['control_cp'].to(self.device)
            ctrl_ge = batch['control_ge'].to(self.device)
            drug = batch['drug'].to(self.device)
            tgt_cp = batch['target_cp'].to(self.device)
            tgt_ge = batch['target_ge'].to(self.device)
            
            if ctrl_cp.shape[0] == 1: return None
            
            # Forward (Q4: 输入 Image+Gene+Drug)
            pred_cp, pred_ge = self.model(ctrl_cp, ctrl_ge, drug)
            
            # Loss: 简单加权
            loss = F.mse_loss(pred_cp, tgt_cp) + F.mse_loss(pred_ge, tgt_ge)
            return loss
            
        else:
            # BaseDataset 返回 tuple
            x1, x2, _, _, drug, _ = batch
            x1 = x1.to(self.device)
            x2 = x2.to(self.device)
            drug = drug.to(self.device)
            
            if x1.shape[0] == 1: return None
            
            x2_pred = self.model(x1, drug)
            return F.mse_loss(x2_pred, x2)

    def _get_batch_size(self, batch):
        if self.task_type == 'mvc':
            return batch['control_cp'].shape[0]
        else:
            return batch[0].shape[0]

    def save_checkpoint(self, path):
        torch.save(self.model, path)