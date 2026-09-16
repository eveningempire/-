# 14 平台初接入与 409 Shadow 模型合同

> 合同版本：`platform_shadow_contract_v1`  
> 目标：2026-09-10 早上交付一个可被平台代码加载、调用、健康检查和回放的候选算法包。  
> 科学状态：`SYNTHETIC_ONLY / SHADOW_ONLY / NON_ACTIONABLE`。

## 1. 明早必须交付的两条线

### P1：可部署的 BiLSTM 合成候选包（必须）

- 默认架构预注册为纯 BiLSTM，不按 n1 test 排名选型。
- 包必须自包含：模型权重、scaler、feature schema、有效 config、源码/资产哈希、运行环境、输入输出合同、样例请求/响应和 `SHA256SUMS`。
- 必须有 Python API 和文件式 CLI；平台未给出 HTTP/RPC 合同，本轮不自行假定 Web 服务。
- 必须在无 GPU 的 CPU 节点完成冷启动、健康检查、单条和 batch 推理、确定性回放。

### P2：409 真实输入的 shadow 兼容演示（必须）

- 用冻结 409 快照只读构造历史窗口，不构造/伪造 RUL 标签，不计算 MAE/RMSE。
- 平台接口要能读入 409 序列并完成 schema/有限值/长度/分布检查。
- 若 P1 模型的 22 维合成 schema 与 409 schema 不一致，必须拒绝偷偷 reshape，返回 `MODEL_NOT_APPLIED_SCHEMA_MISMATCH`。
- 为了实现真正的端到端 shadow 演示，允许另外训练 `platform_lox_shadow_fixture_v1` 模型：其输入 schema 必须与当前 409 LOX 序列完全相同，但特征和目标全部由合成生成器产生，不得用 409 拟合 scaler、权重、阈值或标签。
- shadow 模型在 409 上的输出只能叫 `synthetic_proxy_score`，用于接口联调和分布观察，不得叫真实 RUL。

## 2. 稳定推理合同

Python 入口：

```python
runtime = PlatformRuntime.load(bundle_dir, device="cpu")
result = runtime.predict(features, lengths, sample_ids=None)
health = runtime.healthcheck()
```

文件 CLI 接受 `.npz`：

- `features`: `float32 [batch,time,feature]`，历史时间正序，右填充；
- `lengths`: `int64 [batch]`，且 `1 <= lengths[i] <= time`；
- `sample_ids`: 可选字符串数组；
- `input_space`: 只允许 manifest 声明的 `raw` 或 `scaled`，不得猜测。

输出 JSONL/CSV 每条至少包含：

```text
sample_id, model_version, contract_version, status,
raw_score, display_score_clipped, score_name,
deployment_mode, actionable, physical_rul_claim,
schema_hash, warnings
```

强制字段：

- `deployment_mode="shadow"`；
- `actionable=false`；
- `physical_rul_claim=false`；
- P1 的 `score_name="synthetic_contract_rul_normalized"`；
- P2 的 `score_name="synthetic_proxy_score"`。

`raw_score` 必须原样保留；可另外给出 `[0,1]` 的 `display_score_clipped`，但不得只保留裁剪值。NaN/Inf、schema 不匹配或资产哈希失配时必须 abstain，不得返回伪正常分数。

## 3. 安全、漂移与回退

1. 加载时校验包内 SHA-256、checkpoint schema、model config、feature schema 顺序和 scaler 维度。
2. 输入检查只在 `lengths` 覆盖的有效时刻上进行；填充尾不参与有限值和漂移统计。
3. 包内保存 train-only 分布摘要。对超出训练分布的输入记录逐特征漂移率和总漂移率；本轮不把任意漂移阈值宣称为安全阈值。
4. 单样本无效只 abstain 该样本；资产或合同级错误整批拒绝。
5. 回退不是返回随机/常数 RUL；回退是返回明确状态码和无分数。

## 4. 产物布局

```text
rul_prediction/deployments/<DEPLOY_VERSION>/
├── deployment_manifest.json
├── model_state.pt
├── scaler.npz
├── feature_schema.json
├── train_distribution.json
├── config.yaml
├── environment.json
├── source_hashes.json
├── sample_request.npz
├── sample_response.jsonl
├── healthcheck.json
├── README.md
└── SHA256SUMS
```

目录存在即拒绝覆盖。不使用指向外部模型目录的软链接。

## 5. 明早验收闸门

- [ ] P1 包在新 CPU 计算节点从空进程加载，healthcheck PASS。
- [ ] 同一 sample 重复 3 次输出逐位一致（或记录数值容差）。
- [ ] batch 输出与逐条输出一致。
- [ ] schema 错序、少列、NaN/Inf、非法 lengths、损坏哈希都有拒绝测试。
- [ ] P2 对 409 全部可用历史窗口跑完 shadow 推理，记录样本数、abstain 数和漂移摘要，无任何目标/评价指标。
- [ ] 将 409 目标列注入请求时接口必须拒绝。
- [ ] 输出全部含 `shadow/non-actionable/no-physical-RUL-claim` 标记。
- [ ] CPU 延迟、包大小、峰值内存和 Python/PyTorch 版本入报告。
- [ ] 包离线校验通过，且无 `health_assessment/` 文件泄漏。

## 6. 明早可以和不可以说的话

可以说：“已交付可集成的 BiLSTM 候选包，具备稳定推理合同、自检、追溯、拒绝和 409 shadow 联调能力；算法数值仅经合成合同验证。”

不可以说：“模型已能预测 409 真实剩余寿命”、“已达到上线安全标准”或“409 的 shadow 分数已被真实标签验证”。
