# src/models.py
import torch
import torch.nn as nn

class BaseModel(nn.Module):
    def _init_weights(self, layer):
        if isinstance(layer, nn.Linear):
            nn.init.xavier_uniform_(layer.weight)

class VCModel(BaseModel):
    def __init__(self, n_genes, n_emd, molecule_feature_dim, n_latent=1024, 
                 n_en_hidden=[512], n_de_hidden=[768], dropout=0.2):
        super().__init__()
        self.n_latent = n_latent
        
        # Encoder
        layers = [
            nn.Linear(n_emd, n_en_hidden[0]),
            nn.BatchNorm1d(n_en_hidden[0]),
            nn.ReLU(),
            nn.Dropout(dropout)
        ]
        # (简化逻辑：支持多层 Hidden，这里展示基础结构，可按需还原循环构建逻辑)
        self.encoder = nn.Sequential(*layers)
        
        # Drug Embedding Adapter
        self.drug_adapter = nn.Sequential(
            nn.Linear(molecule_feature_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Decoder
        # Input dim = Encoder_Out (512) + Drug_Adapter_Out (512) = 1024
        self.decoder = nn.Sequential(
            nn.Linear(512 + 512, n_de_hidden[0]),
            nn.BatchNorm1d(n_de_hidden[0]),
            nn.LeakyReLU(0.1),
            nn.Dropout(dropout),
            nn.Linear(n_de_hidden[0], n_genes) # Output
        )
        
        self.apply(self._init_weights)

    def forward(self, x, drug_feat):
        z = self.encoder(x)
        d = self.drug_adapter(drug_feat)
        # Concatenate gene latent + drug latent
        z_combined = torch.cat([z, d], dim=1)
        return self.decoder(z_combined)

class MVCModel(BaseModel):
    def __init__(self, n_images, n_genes, molecule_feature_dim, 
                 n_latent=1024, dropout=0.2):
        super().__init__()
        
        # 1. Image Encoder
        self.enc_cp = nn.Sequential(
            nn.Linear(n_images, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # 2. Gene Encoder
        self.enc_ge = nn.Sequential(
            nn.Linear(n_genes, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # 3. Drug Adapter
        self.drug_adapter = nn.Sequential(
            nn.Linear(molecule_feature_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # 4. Fusion Layer (Late Latent)
        # Input: 512(CP) + 512(GE) + 512(Drug) = 1536
        self.fusion = nn.Sequential(
            nn.Linear(1536, n_latent),
            nn.BatchNorm1d(n_latent),
            nn.LeakyReLU(0.1),
            nn.Dropout(dropout)
        )
        
        # 5. Decoders
        self.dec_cp = nn.Linear(n_latent, n_images)
        self.dec_ge = nn.Linear(n_latent, n_genes)
        
        self.apply(self._init_weights)

    def forward(self, x_cp, x_ge, drug_feat):
        z_cp = self.enc_cp(x_cp)
        z_ge = self.enc_ge(x_ge)
        z_drug = self.drug_adapter(drug_feat)
        
        # Fusion
        z_fused = torch.cat([z_cp, z_ge, z_drug], dim=1)
        latent = self.fusion(z_fused)
        
        # Prediction
        pred_cp = self.dec_cp(latent)
        pred_ge = self.dec_ge(latent)
        
        return pred_cp, pred_ge