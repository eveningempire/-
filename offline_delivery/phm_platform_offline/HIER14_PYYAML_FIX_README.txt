Hier14 PyYAML 补丁

用于修复页面提示:Hier14 runtime unavailable: No module named yaml。

操作:
1. 关闭当前平台服务。
2. 将补丁内容解压到原项目根目录(与 manage.py 同级),保持 offline\python 目录合并。
3. 双击 install_hier14_yaml.bat。
4. 看到 PyYAML OK 后,重新双击 start_cmg_platform.bat。

不需要联网,不需要重新创建 .venv,也不需要重新解压完整项目包。
