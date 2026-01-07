# src/dataset.py
import torch
import numpy as np
import pickle
import os
from torch.utils.data import Dataset
from src.utils import load_from_HDF, split_data, split_data_cid
from src.configs import DATA_ROOT, EMBEDDING_FILES, get_data_path

class BaseDataset(Dataset):
    def __init__(self, x_control, x_target, mol_features, mol_ids, extra_data=None):
        # 修改后：强制转为 float32
        self.x_control = x_control.astype(np.float32)
        self.x_target = x_target.astype(np.float32)
        
        self.mol_features = mol_features.astype(np.float32)
        self.mol_ids = mol_ids
        self.extra_data = extra_data

    def __getitem__(self, index):
        # 统一返回：(Control, Target, Control_Duplicate, Target_Duplicate, Drug, ID)
        # Duplicate 是为了兼容你旧代码的接口习惯
        return (self.x_control[index], self.x_target[index], 
                self.x_control[index], self.x_target[index], 
                self.mol_features[index], self.mol_ids[index])

    def __len__(self):
        return len(self.mol_ids)

class MVCDataset(Dataset):
    def __init__(self, x_ctrl_cp, x_tgt_cp, x_ctrl_ge, x_tgt_ge, mol_features, mol_ids):
        self.x_ctrl_cp = x_ctrl_cp
        self.x_tgt_cp = x_tgt_cp
        self.x_ctrl_ge = x_ctrl_ge
        self.x_tgt_ge = x_tgt_ge
        self.mol_features = mol_features.astype(np.float32)
        self.mol_ids = mol_ids

    def __getitem__(self, index):
        # MVC 模型输入 (Q4): Image(Ctrl) + Gene(Ctrl) + Drug
        # 对应字典返回，方便 DataLoader 使用
        return {
            'control_cp': self.x_ctrl_cp[index],
            'target_cp': self.x_tgt_cp[index],
            'control_ge': self.x_ctrl_ge[index],
            'target_ge': self.x_tgt_ge[index],
            'drug': self.mol_features[index],
            'mol_id': self.mol_ids[index]
        }

    def __len__(self):
        return len(self.mol_ids)

def get_datasets(args, task_type='gene'):
    """
    统一的数据加载函数，返回 Train/Valid/Test Datasets 和 Meta Info
    """
    # 1. 加载主数据
    data_path = get_data_path(args.dataset_name, task_type=task_type)
    
    if not data_path or not os.path.exists(data_path):
        # 增加更详细的报错信息，方便调试
        raise FileNotFoundError(
            f"Data path not found for dataset='{args.dataset_name}' with task='{task_type}'. "
            f"Resolved path: {data_path}"
        )
        
    raw_data = load_from_HDF(data_path)
    
    # 2. 数据切分
    if args.split_data_type == 'cells_split':
        pair_tr, pair_va, pair_te = split_data_cid(raw_data, args.train_cell_count)
    else:
        pair_tr, pair_va, pair_te = split_data(raw_data, n_folds=5, split_type=args.split_data_type, rnds=args.seed)

    # 3. 加载 Molecule Embedding
    emb_file = EMBEDDING_FILES.get(args.molecule_feature)
    # 根据数据集类型确定 embedding 子目录 (逻辑参考原代码)
    if 'MVC' in args.dataset_name or args.dataset_name.startswith('BBBC'):
        emb_subdir = 'Molecular_representations/BBBCData'    
    elif args.dataset_name.startswith('cpg'):
        emb_subdir = 'Molecular_representations/cpg0016'
    else:
        dataset_part = args.dataset_name.split('_')[0] # e.g., Tahoe
        emb_subdir = f'Molecular_representations/{dataset_part}'
    
    # print(f"Loading molecule embeddings from {emb_subdir}/{emb_file}...")
    emb_path = os.path.join(DATA_ROOT, emb_subdir, emb_file)
    print(f"Embedding path: {emb_path}")  
    # ./data/Molecular_representations/LINCS965/ECFP4_emb2048.pickle
    
    # 如果找不到，尝试通用路径
    if not os.path.exists(emb_path):
        emb_path = os.path.join(DATA_ROOT, 'Molecular_representations', emb_file)
        
    with open(emb_path, 'rb') as f:
        smi2emb = pickle.load(f)

    # 4. Q2: 计算全局扰动中心 (Perturbed Centroid)
    # 逻辑：只使用训练集 (pair_tr) 的 target 数据
    if task_type == 'mvc':
        train_target_cp = pair_tr['target_CP'] # 假设 MVC 数据里 key 是这个
        train_target_ge = pair_tr['target_GE']
        centroid = {
            'cp': torch.tensor(train_target_cp.mean(axis=0)).float(),
            'ge': torch.tensor(train_target_ge.mean(axis=0)).float()
        }
    else:
        # 单模态处理
        # 兼容旧 Key 名 (Q1 落实)
        if 'target' in pair_tr:
            tgt_key = 'target'
        elif 'x2' in pair_tr: # LINCS 可能用 x2
            tgt_key = 'x2'
        elif 'target_GE' in pair_tr: # BBBC 单模态可能用 target_GE
            tgt_key = 'target_GE'
        else:
            raise KeyError(f"Cannot find target key in data. Available: {pair_tr.keys()}")
            
        train_target = pair_tr[tgt_key]
        centroid = torch.tensor(train_target.mean(axis=0)).float()

    # 5. 构建 Dataset 对象
    def build_ds(subset_data):
        mol_ids = subset_data['canonical_smiles']
        mol_feats = np.array([smi2emb[str(m)] for m in mol_ids])
        
        if task_type == 'mvc':
            return MVCDataset(
                subset_data['control_CP'], subset_data['target_CP'],
                subset_data['control_GE'], subset_data['target_GE'],
                mol_feats, mol_ids
            )
        else:
            # 修复逻辑：显式查找存在的 Key，而不是用 'or'
            # 优先级：control -> x1 -> control_GE
            if 'control' in subset_data:
                ctrl = subset_data['control']
            elif 'x1' in subset_data:
                ctrl = subset_data['x1']
            elif 'control_GE' in subset_data:
                ctrl = subset_data['control_GE']
            else:
                raise KeyError(f"Missing control key. Available: {list(subset_data.keys())}")

            # 优先级：target -> x2 -> target_GE
            if 'target' in subset_data:
                tgt = subset_data['target']
            elif 'x2' in subset_data:
                tgt = subset_data['x2']
            elif 'target_GE' in subset_data:
                tgt = subset_data['target_GE']
            else:
                raise KeyError(f"Missing target key. Available: {list(subset_data.keys())}")

            return BaseDataset(ctrl, tgt, mol_feats, mol_ids)

    train_ds = build_ds(pair_tr)
    valid_ds = build_ds(pair_va)
    test_ds = build_ds(pair_te)
    
    # 6. 元数据信息
    if task_type == 'mvc':
        meta = {
            'n_genes': pair_tr['control_GE'].shape[1],
            'n_images': pair_tr['control_CP'].shape[1],
            'mol_dim': mol_feats.shape[1],
            'centroid': centroid
        }
    else:
        # 简单获取维度
        dummy_item = train_ds[0]
        meta = {
            'input_dim': dummy_item[0].shape[0], # genes or images
            'mol_dim': dummy_item[4].shape[0],
            'centroid': centroid
        }
        
    return train_ds, valid_ds, test_ds, meta