from pathlib import Path
p=Path('build_manual.py')
s=p.read_text(encoding='utf-8')
s=s.replace("def num(text):\n    para=doc.add_paragraph(style='List Number'); r=para.add_run(text); set_font(r); set_para_spacing(para,after=3); return para", "def num(text):\n    para=doc.add_paragraph(); r=para.add_run(text); set_font(r); set_para_spacing(para,after=3); return para")
s=s.replace("pagebreak(); h('附录 A 数据字段与输入契约',1)", "h('附录 A 数据字段与输入契约',1)")
# insert explicit batch and module actions
needle="h('6.3 下载、修改和删除',2)"
insert="""h('6.3 批量导入与质量预检',2)
p('管理员可在上传区选择一个或多个 CSV、JSON、JSONL 或 XLSX 文件，点击“批量导入数据”。页面返回成功/失败数量和逐文件结果；失败文件不会回滚已经成功导入的文件。批量导入前建议先按文件名、时间列和字段契约检查，导入后再逐条打开“查看数据”核对时间字段、FaultFlag 和参数列数。')
num('点击“选择文件”并选择多个文件；不要把同一个文件重复选择。')
num('点击“批量导入数据”，等待提示“成功/失败”统计完成。')
num('对失败项记录文件名和错误原因，修正后单独重新导入；不要直接删除整批已成功记录。')
num('用“关键字、来源、系统、故障类型”过滤并记录生成的数据集 ID。')
figure(ROOT/'docs/manual_20261010/screenshots/data-preview.png','图 6-3 数据预览用于核对字段角色、样本数和首次故障时间。')
"""
s=s.replace(needle,insert+needle)
# add model import details after model p
needle="p('“模型与可视化 → 模型管理”用于查看模型目录、业务域、版本、状态和登记标识。模型管理页主要提供状态查询和登记信息，不等同于模型已通过当前工况精度验收。运行算法时仍应以业务页面显示的实际模型、数据契约和结果限制为准。')"
insert="""p('管理员展开“导入模型 / 算法”，选择包含 manifest.json、入口 Python 文件和模型资产的 ZIP，点击“导入算法包”。当前限制为单包上传不超过 200 MB、解压后不超过 500 MB；已有 key 不覆盖。导入成功后列表显示“已导入，待验证”，必须在测试数据上实际运行后再进入正式目录。')
code('{ "key": "my_rul_model", "name": "我的寿命模型", "version": "1.0", "category": "rul", "entrypoint": "algorithm.py:predict", "min_rows": 51, "parameters": {} }')
"""
s=s.replace(needle,needle+'\n'+insert)
# expand release params
needle="h('13.2 建议的复核顺序',2)"
insert="""h('13.2 配置参数与执行',2)
p('页面左侧先填写运载器编号和任务名称，再为动力、电源、测控、导航制导与控制、结构设置健康度（0～100）和权重。权重合计必须约等于 100%；页面会显示归一化权重。然后填写寿命裕度、未关闭严重告警数、放行阈值和子系统最低阈值，点击“执行放行评估”。右侧显示系统健康指数、加权健康度、RBD 等效健康、任务成功概率和阻断项。')
table(['参数','含义','注意'],[('健康度','分系统当前状态 0～100 分','应有诊断/健康结果或人工检查依据。'),('权重','分系统在整器评估中的重要程度','合计应为 100%；后端会归一化。'),('寿命裕度','预计剩余寿命或可复用裕度','越低会降低成功概率。'),('严重告警','未关闭严重告警数量','每条都会降低概率并可能形成阻断项。'),('放行阈值','建议放行的最低成功概率','只是辅助判据，不替代组织流程。'),('子系统最低阈值','任一模块低于该值时的阻断线','由授权人员按任务要求设定。')])
"""
s=s.replace(needle,insert+needle)
# expand structural ops
needle="p('“结构与知识 → 运载器 PBS 结构树”展示产品、系统、子系统和部件层级。新增或修改节点时填写唯一标识、名称、父节点和层级，保存后刷新验证。删除节点可能影响子节点、PBS 关联和放行记录，必须在删除前导出结构和引用记录。')"
insert="""num('新增节点：点击“新增根节点”或父节点后的“新增下级”，填写节点标识、名称、层级、PBS 编码和父节点，保存后刷新。')
num('编辑/移动：选择节点，点击“编辑/移动”，修改名称、PBS 编码或父节点；节点标识用于稳定引用，不建议随意改变。')
num('关联数据：在“数据管理”对数据集点击“关联 PBS”，选择结构树中的单机产品并保存；寿命模型会据此阻止明显的部件不匹配。')
num('删除节点：确认级联影响后再删除；删除前导出结构和数据集关联清单。')
"""
s=s.replace(needle,needle+'\n'+insert)
# remove word indicating old and placeholder false positive; update output
p.write_text(s,encoding='utf-8')
