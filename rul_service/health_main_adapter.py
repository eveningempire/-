"""Inference adapter for the trained health-main RUL ensemble assets."""
from pathlib import Path
import joblib, numpy as np, torch
import torch.nn as nn

class _CNN(nn.Module):
 def __init__(self,d,h): super().__init__(); self.conv1=nn.Conv1d(1,h,3,padding=1); self.pool=nn.AdaptiveMaxPool1d(1); self.fc=nn.Linear(h,1)
 def forward(self,x): return self.fc(self.pool(torch.relu(self.conv1(x.transpose(1,2)))).squeeze(-1))
class _BiRNN(nn.Module):
 def __init__(self,d,h,kind='rnn'):
  super().__init__(); self.kind=kind; setattr(self,kind,getattr(nn,kind.upper())(d,h,batch_first=True,bidirectional=True)); self.fc=nn.Linear(2*h,1)
 def forward(self,x): return self.fc(getattr(self,self.kind)(x)[0][:,-1,:])
class _SRNN(nn.Module):
 def __init__(self,d,h): super().__init__(); self.rnn1=nn.RNN(d,h,batch_first=True); self.rnn2=nn.RNN(h,h,batch_first=True); self.fc=nn.Linear(h,1)
 def forward(self,x): return self.fc(self.rnn2(self.rnn1(x)[0])[0][:,-1,:])

def predict(path, asset_dir):
 import pandas as pd
 df=pd.read_csv(path); col=next((c for c in df.columns if c.lower() in ('hi_norm','hi','health_index')),None)
 if not col: raise ValueError('health-main 集成模型要求 CSV 含 HI_norm/HI/health_index 列')
 hi=df[col].astype(float).to_numpy(); seq=50
 if not np.isfinite(hi).all() or ((hi<0)|(hi>1)).any(): raise ValueError('HI 必须为 0 到 1 的有限数值')
 if len(hi)<=seq: raise ValueError(f'样本不足：集成模型至少需要 {seq+1} 行 HI 数据')
 scaler=joblib.load(asset_dir/'scaler.pkl'); pca=joblib.load(asset_dir/'pca.pkl'); meta=__import__('json').loads((asset_dir/'hi_meta.json').read_text())
 X=np.array([hi[i:i+seq] for i in range(len(hi)-seq)],dtype='float32')[:,:,None]
 preds=[]; device='cpu'
 for name in ('CNN','BiRNN','BiLSTM','BiGRU','SRNN'):
  prm=joblib.load(asset_dir/f'{name}_best_params.pkl'); h=prm['hidden_dim']; model=_CNN(1,h) if name=='CNN' else _SRNN(1,h) if name=='SRNN' else _BiRNN(1,h,{'BiRNN':'rnn','BiLSTM':'lstm','BiGRU':'gru'}[name]); model.load_state_dict(torch.load(asset_dir/f'{name}_best_model.pt',map_location=device)); model.eval()
  with torch.no_grad(): preds.append(model(torch.from_numpy(X)).numpy().ravel())
 P=np.stack(preds,axis=1); ens=joblib.load(asset_dir/'ensemble.pkl'); rf=ens['rf'].predict(P); ada=ens['ada'].predict(P)
 return {'algorithm':'health-main RUL ensemble (CNN/BiRNN/BiLSTM/BiGRU/SRNN + RF/Ada)','model_source':str(asset_dir),'sample_count':len(hi),'sequence_length':seq,'hi_sequence':hi.tolist(),'ensemble_rul':{'RF':rf.tolist(),'Ada':ada.tolist()},'rul_value':float((rf[-1]+ada[-1])/2),'current_hi':float(hi[-1]),'model_predictions':{n:preds[i].tolist() for i,n in enumerate(('CNN','BiRNN','BiLSTM','BiGRU','SRNN'))}}
