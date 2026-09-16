# p1_bilstm_candidate_v1_s3407

Profile: **P1_candidate** under contract `platform_shadow_contract_v1`.

- source run: `rul_syn_bilstm_s3407_20260909_n2` (synthetic contract fixture only)
- score name: `synthetic_contract_rul_normalized`
- deployment_mode=shadow, actionable=false, physical_rul_claim=false
- feature count: 22; seq_length: 16; input_space: raw

## Python API

```python
from rul_prediction.deployment.runtime import PlatformRuntime
runtime = PlatformRuntime.load("/irip/xietianyu_2024/workspace/20jd/rul_prediction/deployments/p1_bilstm_candidate_v1_s3407", device="cpu")
result = runtime.predict(features, lengths, sample_ids=None)
health = runtime.healthcheck()
```

## CLI

```bash
python -m rul_prediction.deployment.cli predict \
  --bundle "/irip/xietianyu_2024/workspace/20jd/rul_prediction/deployments/p1_bilstm_candidate_v1_s3407" --input request.npz --output result.jsonl --format jsonl
```

All outputs are shadow scores; they are not real RUL and are not actionable.
