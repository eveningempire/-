# PHM 平台启动说明

## GitHub 下载版

下载 **main 分支**并完整解压。安装 64 位 Python 3.10、3.11 或 3.12 后，双击 `start_phm_platform.bat`；首次运行会联网安装依赖并创建数据库。双击 `create_superuser.bat` 设置自己的管理员账号，访问 <http://127.0.0.1:8000/>。随后双击 `import_sample_data.bat` 导入真实仿真数据。

本版已包含 Hier14 的 `best_model.pth`、`scaler.pkl` 和部署元数据，15 个部件的完整寿命模型、健康评估模型、Simulink 源模型以及前端成品。无需安装 Node.js、Redis、MySQL；GitHub 版不包含 Python 本体、离线 wheel、个人数据库或账号。

默认自带正常及 13 类故障各一组真实仿真数据，共 28 个完整 CSV。需要完整 492 个 CSV 时执行 `python download_simulation_data.py`，或从 [Release](https://github.com/eveningempire/-/releases/tag/phm-github-20261104) 下载 `simulate_data_+1.zip` 放进 `integrations/simulation_assets/`。不要解压该数据包；重启平台后自动使用完整包，再运行 `import_sample_data.bat`。

可通过 `powershell -NoProfile -ExecutionPolicy Bypass -File .\start_phm_platform.ps1 -CheckOnly` 检查依赖、数据库和模型实际加载。若提示缺少模型，请重新下载 main 完整项目，不要只复制 Python 文件。

## 完整离线交付包

只有单独制作的离线交付包才携带 `runtime/python310` 或 Python 安装包、`offline/python` 和现场数据库；不要将 GitHub 的“Download ZIP”视为完整离线包。已有包内 Python 和依赖时仍支持离线安装，`setup_migration.ps1 -Offline` 会强制禁用联网安装。

## MATLAB

离线回放、故障诊断、健康评估、寿命预测不要求 MATLAB。实时 Simulink 仿真需要当前电脑安装 MATLAB/Simulink（随附源模型 R2023a）与匹配的 Engine，安装目录需在页面设置。MATLAB 2012 可通过 `integrations/matlab/` 的 Java HTTP 接口发送真实遥测，但不能据此保证运行 R2023a 源模型。

## 后续使用

- 启动：`start_phm_platform.bat`。
- 停止：`stop_phm_platform.bat`。
- 创建管理员：`create_superuser.bat`。
- 导入样例/完整数据：`import_sample_data.bat`，重复执行会复用已有记录。
- 验证真实模型推理：导入后执行 `.\.venv\Scripts\python.exe verify_github_inference.py`。

项目可放在含中文或空格的路径中；迁移到另一台电脑时重新创建 `.venv`，不要复制旧电脑的虚拟环境。
