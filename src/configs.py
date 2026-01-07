# src/configs.py
import os

DATA_ROOT = os.getenv('VCBENCH_DATA_ROOT', './data')

DATASET_FILES = {
    # ================= Gene Tasks (数据源通常是 Processed_Paired_GE.h5) =================
    'LINCS': os.path.join(DATA_ROOT, 'LINCS2020/processed_data.h5'),
    'LINCS965': os.path.join(DATA_ROOT, 'LINCS2020/lincs_data965.h5'),
    'CIGS': os.path.join(DATA_ROOT, 'CIGS/CIGS_2Cell_lines.h5'),
    
    # 显式定义 BBBC 的 Gene 数据路径
    'BBBC036_Gene': os.path.join(DATA_ROOT, 'MVC/CDRPBIO-BBBC036-Bray/Processed_Paired_GE.h5'),
    'BBBC047_Gene': os.path.join(DATA_ROOT, 'MVC/CDRP-BBBC047-Bray/Processed_Paired_GE.h5'),

    # ================= Image Tasks (数据源通常是 Image/xxxx.h5) =================
    # 显式定义 BBBC 的 Image 数据路径
    'BBBC036_Image': os.path.join(DATA_ROOT, 'Image/BBBC036_data.h5'),
    'BBBC047_Image': os.path.join(DATA_ROOT, 'Image/BBBC047_data.h5'),
    'cpg0016': os.path.join(DATA_ROOT, 'Image/cpg0016_data.h5'),

    # ================= MVC Tasks (多模态数据) =================
    'MVC_BBBC047': os.path.join(DATA_ROOT, 'MVC/MVC_BBBC047/Aggregated_CP_GE.h5'),
    'MVC_BBBC036': os.path.join(DATA_ROOT, 'MVC/MVC_BBBC036/Aggregated_CP_GE.h5'),
}

# Embedding 映射保持不变
EMBEDDING_FILES = {
    'ECFP4': 'ECFP4_emb2048.pickle',
    'KPGT': 'KPGT_emb2304.pickle',
    'InfoAlign': 'InfoAlign_emb300.pickle',
    'ChemBERTa2': 'ChemBERTa2_emb384.pickle',
    'MolT5': 'MolT5_emb768.pickle',
    'Chemprop': 'Chemprop_emb300.pickle',
    'MolCLR': 'MolCLR_emb512.pickle',
    'Mole_BERT': 'Mole_BERT_emb300.pickle',
    'GeminiMol': 'GeminiMol_emb2048.pkl',
    'Ouroboros': 'Ouroboros_emb2048.pkl',
    'UniMol': 'UniMol_emb512.pkl',
    'UniMolV2': 'UniMolV2_emb1024.pkl'
}

def get_data_path(dataset_name, task_type=None):
    """
    根据数据集名称和任务类型返回路径。
    自动处理 _Gene / _Image 后缀，避免 shell 脚本需要改名。
    """
    # 1. 处理 Tahoe 特殊逻辑
    if dataset_name.startswith('Tahoe_'):
        part = dataset_name.split('_')[1]
        return os.path.join(DATA_ROOT, f'Tahoe-100M/Tahoe_mini/{part}/default.h5')

    # 2. 尝试直接获取 (例如 'LINCS', 'MVC_BBBC047')
    if dataset_name in DATASET_FILES:
        return DATASET_FILES[dataset_name]

    # 3. 如果 dataset_name 是 'BBBC036' 且 task_type 是 'gene'，自动找 'BBBC036_Gene'
    if task_type:
        # 首字母大写处理 (gene -> Gene, image -> Image)
        suffix = task_type.capitalize()
        keyed_name = f"{dataset_name}_{suffix}"
        if keyed_name in DATASET_FILES:
            return DATASET_FILES[keyed_name]
    
    return None