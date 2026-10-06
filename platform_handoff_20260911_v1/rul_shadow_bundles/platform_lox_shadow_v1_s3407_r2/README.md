# platform_lox_shadow_v1_s3407_r2

Profile: **P2_lox_shadow** under contract `platform_shadow_contract_v1`.

- source run: `platform_lox_shadow_bilstm_s3407_20260909_r2` (synthetic contract fixture only)
- score name: `synthetic_proxy_score`
- deployment_mode=shadow, actionable=false, physical_rul_claim=false
- feature count: 10; seq_length: 16; input_space: raw

## Python API

```python
from rul_prediction.deployment.runtime import PlatformRuntime
runtime = PlatformRuntime.load("/irip/xietianyu_2024/workspace/20jd/rul_prediction/deployments/platform_lox_shadow_v1_s3407_r2", device="cpu")
result = runtime.predict(features, lengths, sample_ids=None)
health = runtime.healthcheck()
```

## CLI

```bash
python -m rul_prediction.deployment.cli predict \
  --bundle "/irip/xietianyu_2024/workspace/20jd/rul_prediction/deployments/platform_lox_shadow_v1_s3407_r2" --input request.npz --output result.jsonl --format jsonl
```

All outputs are shadow scores; they are not real RUL and are not actionable.
