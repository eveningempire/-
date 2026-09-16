# 示例数据说明

`rul/*.npz` 仅用于校验平台请求 schema 和重现 bundle 的 shadow 响应，不是真实训练或验收数据。

请求包含 `features [batch,time,feature]`、`lengths [batch]` 及可选 `sample_ids`。推理请求不得包含 P1--P17、truth、rate、fault timing、split、seed、mode、target 或任何未来信息。特征名称、顺序、维度与 input space 必须和 bundle 中的 schema 完全一致。
