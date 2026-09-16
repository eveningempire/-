# 20JD 平台接入交付包 v1

本目录是面向平台开发人员的自包含交付副本，不是新的研发主目录。研发仍在 20JD 根目录进行，此包仅用于平台接口联调、模型加载和 shadow 链路验证。

## 交付状态

- 健康评估：可进行开发环境接入，输入是上游生成的窗口证据，尚不是从原始遥测端到端输入。
- RUL：仅限 `shadow` 模式；两个部署包均声明 `actionable=false` 和 `physical_rul_claim=false`。
- 当前 409 运行数据均为右删失，无观测失效和已注册失效阈值，不得将 RUL 输出当作真实剩余寿命或控制依据。
- 健康评估的 fault alarm 仍为 `ABSTAIN`，localization 阈值尚未注册；不得标注为安全认证模型。



## 目录

- `health_bundle/`：健康评估适配器、模型、注册表、示例与科学证据。
- `code/rul_prediction/`：RUL 部署运行时及建模定义。
- `rul_shadow_bundles/`：两个可加载的 RUL shadow 包（含模型、scaler、schema 和 hash）。
- `data_examples/`：平台请求/响应样例，不是训练数据。
- `docs/`：数据、算法、部署及替换模型说明。
- `scripts/`：独立冒烟测试和完整性校验。
- `manifests/SHA256SUMS.txt`：交付包文件校验和。

## 快速验证

在本目录打开 PowerShell，使用已安装依赖的 Python：

```powershell
python -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File scripts/smoke_health.ps1
powershell -ExecutionPolicy Bypass -File scripts/smoke_rul.ps1
powershell -ExecutionPolicy Bypass -File scripts/verify_manifest.ps1
```

接入时先完成 schema 映射和 shadow 日志落盘，不得在平台侧自动重排、补齐或猜测特征。细节见 `docs/HEALTH_PLATFORM_INTEGRATION_GUIDE.md` 和 `docs/14_平台初接入与409_Shadow模型合同.md`。
