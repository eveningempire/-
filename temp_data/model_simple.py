"""
SimpleGCNModel implementation - SIMPLIFIED VERSION
Based on the checkpoint structure and original predictions
"""

import torch
import torch.nn as nn
import pickle
from torch_geometric.nn import GCNConv


class GCNLayer(nn.Module):
    """GCN layer wrapper"""
    def __init__(self, in_channels, out_channels):
        super(GCNLayer, self).__init__()
        self.conv = GCNConv(in_channels, out_channels)
    
    def forward(self, x, edge_index, edge_weight=None):
        return self.conv(x, edge_index, edge_weight)


class RegHead(nn.Module):
    """Regression head"""
    def __init__(self, in_features, out_features=1):
        super(RegHead, self).__init__()
        self.linear = nn.Linear(in_features, out_features)
    
    def forward(self, x):
        return self.linear(x)


class SimpleGCNModel(nn.Module):
    """
    Simple GCN model for degradation prediction.
    IMPORTANT: This is a MINIMAL implementation matching the checkpoint structure.
    """
    
    def __init__(self, num_nodes=5, reg_head_type='linear', lambda_reg=0.0001):
        super(SimpleGCNModel, self).__init__()
        self.num_nodes = num_nodes
        self.reg_head_type = reg_head_type
        self.lambda_reg = lambda_reg
        
        # Edge weights - adjacency matrix
        self.edge_weights = nn.Parameter(torch.ones(num_nodes, num_nodes))
        
        # GCN layers - based on checkpoint:
        # gcn1: 69 -> 32
        # gcn2: 32 -> 32
        # reg_head: 32 -> 1
        self.gcn1 = GCNLayer(69, 32)
        self.gcn2 = GCNLayer(32, 32)
        
        # Regression head
        self.reg_head = RegHead(32, 1)
        
        # Scalers
        self.scaler_x = None
        self.scaler_y = None
    
    def forward(self, x, edge_index=None):
        """
        Forward pass - process each sample individually.
        
        Args:
            x: [batch_size, num_nodes, num_features]
        Returns:
            out: [batch_size, 1]
        """
        batch_size = x.shape[0]
        
       # Generate edge index
        if edge_index is None:
            edge_index = self._generate_edge_index()
        
        # Get edge weights for the edges
        edge_weight = self.edge_weights[edge_index[0], edge_index[1]]
        edge_weight = torch.abs(edge_weight)
        
        # Process each graph individually
        outputs = []
        for i in range(batch_size):
            # Single graph: [num_nodes, num_features]
            xi = x[i]
            
            # GCN forward
            h = self.gcn1(xi, edge_index, edge_weight)
            h = torch.relu(h)
            h = self.gcn2(h, edge_index, edge_weight)
            h = torch.relu(h)
            
            # Mean pooling: [num_nodes, 32] -> [32]
            h = h.mean(dim=0)
            
            # Regression: [32] -> [1]
            out = self.reg_head(h.unsqueeze(0))
            outputs.append(out)
        
        return torch.cat(outputs, dim=0)
    
    def _generate_edge_index(self):
        """Generate fully connected graph"""
        edges = []
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                if i != j:
                    edges.append([i, j])
        return torch.tensor(edges, dtype=torch.long).t()
    
    def load_scalers(self, scaler_path):
        """Load scalers from pickle file"""
        try:
            with open(scaler_path, 'rb') as f:
                scalers = pickle.load(f)
                if isinstance(scalers, dict):
                    self.scaler_x = scalers.get('channel_scaler')
                    self.scaler_y = scalers.get('label_scaler')
                else:
                    self.scaler_x, self.scaler_y = scalers
        except Exception as e:
            print(f"Warning: Failed to load scalers: {e}")
    
    def denormalize_labels(self, labels):
        """Denormalize predicted labels"""
        if self.scaler_y is not None and hasattr(self.scaler_y, 'inverse_transform'):
            import numpy as np
            if len(labels.shape) == 1:
                labels = labels.reshape(-1, 1)
            return self.scaler_y.inverse_transform(labels)
        return labels
