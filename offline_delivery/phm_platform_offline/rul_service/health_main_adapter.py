"""Inference adapter for the trained health-main RUL ensemble assets."""
import joblib
import numpy as np
import torch
import torch.nn as nn


class _CNN(nn.Module):
    def __init__(self, dimension, hidden):
        super().__init__()
        self.conv1 = nn.Conv1d(1, hidden, 3, padding=1)
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.fc = nn.Linear(hidden, 1)

    def forward(self, value):
        return self.fc(self.pool(torch.relu(self.conv1(value.transpose(1, 2)))).squeeze(-1))


class _BiRNN(nn.Module):
    def __init__(self, dimension, hidden, kind='rnn'):
        super().__init__()
        self.kind = kind
        setattr(self, kind, getattr(nn, kind.upper())(dimension, hidden, batch_first=True, bidirectional=True))
        self.fc = nn.Linear(2 * hidden, 1)

    def forward(self, value):
        return self.fc(getattr(self, self.kind)(value)[0][:, -1, :])


class _SRNN(nn.Module):
    def __init__(self, dimension, hidden):
        super().__init__()
        self.rnn1 = nn.RNN(dimension, hidden, batch_first=True)
        self.rnn2 = nn.RNN(hidden, hidden, batch_first=True)
        self.fc = nn.Linear(hidden, 1)

    def forward(self, value):
        return self.fc(self.rnn2(self.rnn1(value)[0])[0][:, -1, :])


def predict(path, asset_dir, prepared=None):
    if prepared is None:
        import pandas as pd
        from .inputs import HI_NAMES
        frame = pd.read_csv(path)
        column = next((name for name in frame if name.strip().lower() in HI_NAMES), None)
        if column is None:
            raise ValueError('health-main 集成模型要求已预处理的 HI 输入')
        prepared = {'values': frame[column].astype(float).tolist(),
                    'times': list(range(len(frame))), 'source': {'method': 'provided_hi'}}
    hi = np.asarray(prepared['values'], dtype=float)
    sequence_length = 50
    if not np.isfinite(hi).all() or np.any((hi < 0) | (hi > 1)):
        raise ValueError('HI 必须为 0 到 1 的有限数值')
    if len(hi) <= sequence_length:
        raise ValueError(f'样本不足:集成模型至少需要 {sequence_length + 1} 个 HI 窗口;P 参数需至少约 51 秒时间跨度')
    sequences = np.array([hi[index:index + sequence_length]
                          for index in range(len(hi) - sequence_length)], dtype='float32')[:, :, None]
    names = ('CNN', 'BiRNN', 'BiLSTM', 'BiGRU', 'SRNN')
    predictions = []
    for name in names:
        parameters = joblib.load(asset_dir / f'{name}_best_params.pkl')
        hidden = parameters['hidden_dim']
        model = (_CNN(1, hidden) if name == 'CNN' else _SRNN(1, hidden) if name == 'SRNN'
                 else _BiRNN(1, hidden, {'BiRNN': 'rnn', 'BiLSTM': 'lstm', 'BiGRU': 'gru'}[name]))
        model.load_state_dict(torch.load(asset_dir / f'{name}_best_model.pt', map_location='cpu', weights_only=True))
        model.eval()
        with torch.no_grad():
            prediction = np.concatenate([model(torch.from_numpy(sequences[start:start + 256])).numpy().ravel()
                                         for start in range(0, len(sequences), 256)])
        predictions.append(prediction)
    stacked = np.stack(predictions, axis=1)
    ensemble = joblib.load(asset_dir / 'ensemble.pkl')
    rf, ada = ensemble['rf'].predict(stacked), ensemble['ada'].predict(stacked)
    if not np.isfinite(stacked).all() or not np.isfinite(rf).all() or not np.isfinite(ada).all():
        raise ValueError('训练模型产生非有限预测结果')
    return {'algorithm': 'health-main RUL 集成模型', 'model_source': str(asset_dir),
            'sample_count': len(hi), 'sequence_length': sequence_length, 'hi_sequence': hi.tolist(),
            'hi_times': prepared['times'], 'rul_times': prepared['times'][sequence_length:],
            'hi_source': prepared['source'], 'ensemble_rul': {'RF': rf.tolist(), 'Ada': ada.tolist()},
            'rul_value': max(0.0, float((rf[-1] + ada[-1]) / 2)), 'current_hi': float(hi[-1]),
            'model_predictions': {name: predictions[index].tolist() for index, name in enumerate(names)},
            'prediction_alignment': 'HI[i:i+50] predicts RUL at HI[i+50]',
            'last_input_hi': float(hi[-2])}
