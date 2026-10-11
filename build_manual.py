from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
from pathlib import Path
import os, re, shutil

ROOT = Path(r'E:/实验项目/航天管理项目/phm_platform')
OUT = ROOT / '交付文档' / '重复使用运载器健康管理平台软件使用手册_202610版.docx'
IMG = ROOT / 'logs'

# ---------- OOXML helpers ----------
def set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd'); tcPr.append(shd)
    shd.set(qn('w:fill'), fill)

def set_cell_border(cell, **kwargs):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    borders = tcPr.first_child_found_in('w:tcBorders')
    if borders is None:
        borders = OxmlElement('w:tcBorders'); tcPr.append(borders)
    for edge in ('top','left','bottom','right','insideH','insideV'):
        if edge in kwargs:
            tag = 'w:{}'.format(edge); element = borders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag); borders.append(element)
            for key, val in kwargs[edge].items(): element.set(qn('w:'+key), str(val))

def set_cell_margins(cell, top=100, start=120, bottom=100, end=120):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr(); tcMar = tcPr.first_child_found_in('w:tcMar')
    if tcMar is None: tcMar = OxmlElement('w:tcMar'); tcPr.append(tcMar)
    for m,v in [('top',top),('start',start),('bottom',bottom),('end',end)]:
        node = tcMar.find(qn('w:'+m))
        if node is None: node=OxmlElement('w:'+m); tcMar.append(node)
        node.set(qn('w:w'), str(v)); node.set(qn('w:type'),'dxa')

def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr(); tblHeader = OxmlElement('w:tblHeader'); tblHeader.set(qn('w:val'),'true'); trPr.append(tblHeader)

def set_keep_with_next(p):
    pPr = p._p.get_or_add_pPr(); keep = OxmlElement('w:keepNext'); pPr.append(keep)

def add_page_field(paragraph):
    run = paragraph.add_run(); fldChar1 = OxmlElement('w:fldChar'); fldChar1.set(qn('w:fldCharType'),'begin')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'),'preserve'); instr.text = 'PAGE'
    fldChar2 = OxmlElement('w:fldChar'); fldChar2.set(qn('w:fldCharType'),'end')
    run._r.extend([fldChar1,instr,fldChar2])

def set_font(run, name='微软雅黑', size=None, bold=None, color=None, italic=None):
    run.font.name = name; run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), name)
    run._element.get_or_add_rPr().rFonts.set(qn('w:ascii'), name)
    run._element.get_or_add_rPr().rFonts.set(qn('w:hAnsi'), name)
    if size is not None: run.font.size = Pt(size)
    if bold is not None: run.bold = bold
    if italic is not None: run.italic = italic
    if color is not None: run.font.color.rgb = RGBColor.from_string(color)

def set_para_spacing(p, before=0, after=6, line=1.15):
    fmt=p.paragraph_format; fmt.space_before=Pt(before); fmt.space_after=Pt(after); fmt.line_spacing=line

def add_hyperlink(paragraph, text, url):
    part = paragraph.part; r_id = part.relate_to(url, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', is_external=True)
    hyperlink = OxmlElement('w:hyperlink'); hyperlink.set(qn('r:id'), r_id)
    new_run = OxmlElement('w:r'); rPr = OxmlElement('w:rPr'); color = OxmlElement('w:color'); color.set(qn('w:val'),'0563C1'); rPr.append(color); u=OxmlElement('w:u'); u.set(qn('w:val'),'single'); rPr.append(u); new_run.append(rPr)
    t=OxmlElement('w:t'); t.text=text; new_run.append(t); hyperlink.append(new_run); paragraph._p.append(hyperlink)

# ---------- document ----------
doc=Document()
sec=doc.sections[0]
sec.top_margin=Inches(0.72); sec.bottom_margin=Inches(0.72); sec.left_margin=Inches(0.85); sec.right_margin=Inches(0.75)
# default font
styles=doc.styles
styles['Normal'].font.name='微软雅黑'; styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'),'微软雅黑'); styles['Normal'].font.size=Pt(10.5)
for sty_name,size,color in [('Title',26,'12345B'),('Heading 1',18,'0B5CAD'),('Heading 2',14,'1F4E79'),('Heading 3',11.5,'2B6D9D')]:
    s=styles[sty_name]; s.font.name='微软雅黑'; s._element.rPr.rFonts.set(qn('w:eastAsia'),'微软雅黑'); s.font.size=Pt(size); s.font.bold=True; s.font.color.rgb=RGBColor.from_string(color); s.paragraph_format.space_before=Pt(14 if sty_name!='Title' else 0); s.paragraph_format.space_after=Pt(7); s.paragraph_format.keep_with_next=True
# custom styles
if 'CaptionCN' not in [s.name for s in styles]:
    s=styles.add_style('CaptionCN', WD_STYLE_TYPE.PARAGRAPH); s.font.name='微软雅黑'; s._element.rPr.rFonts.set(qn('w:eastAsia'),'微软雅黑'); s.font.size=Pt(9); s.font.color.rgb=RGBColor(90,105,120); s.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER; s.paragraph_format.space_before=Pt(3); s.paragraph_format.space_after=Pt(9)
if 'SmallNote' not in [s.name for s in styles]:
    s=styles.add_style('SmallNote', WD_STYLE_TYPE.PARAGRAPH); s.font.name='微软雅黑'; s._element.rPr.rFonts.set(qn('w:eastAsia'),'微软雅黑'); s.font.size=Pt(9); s.font.color.rgb=RGBColor(90,90,90); s.paragraph_format.space_after=Pt(5); s.paragraph_format.line_spacing=1.1
# footer/header
header=sec.header.paragraphs[0]; header.alignment=WD_ALIGN_PARAGRAPH.RIGHT; r=header.add_run('重复使用运载器健康管理平台软件使用手册  ·  2026-10'); set_font(r,size=8.5,color='6E7F91')
footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=footer.add_run('内部使用  |  第 '); set_font(r,size=8.5,color='6E7F91'); add_page_field(footer); r=footer.add_run(' 页'); set_font(r,size=8.5,color='6E7F91')

# helpers

def p(text='', style=None, bold_prefix=None, align=None):
    para=doc.add_paragraph(style=style)
    if align is not None: para.alignment=align
    if bold_prefix and text.startswith(bold_prefix):
        r=para.add_run(bold_prefix); set_font(r,bold=True,color='1F4E79'); r=para.add_run(text[len(bold_prefix):]); set_font(r)
    else:
        r=para.add_run(text); set_font(r)
    set_para_spacing(para)
    return para

def bullet(text, level=0):
    para=doc.add_paragraph(style='List Bullet' if level==0 else 'List Bullet 2'); r=para.add_run(text); set_font(r); set_para_spacing(para,after=3); return para

def num(text):
    para=doc.add_paragraph(); r=para.add_run(text); set_font(r); set_para_spacing(para,after=3); return para

def h(text, level=1):
    para=doc.add_heading(text, level=level); set_keep_with_next(para); return para

def table(headers, rows, widths=None, font_size=9.2):
    tbl=doc.add_table(rows=1, cols=len(headers)); tbl.alignment=WD_TABLE_ALIGNMENT.CENTER; tbl.style='Table Grid'; tbl.autofit=True
    hdr=tbl.rows[0]; set_repeat_table_header(hdr)
    for i,txt in enumerate(headers):
        c=hdr.cells[i]; set_cell_shading(c,'DCEAF7'); set_cell_margins(c); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        para=c.paragraphs[0]; para.alignment=WD_ALIGN_PARAGRAPH.CENTER; rr=para.add_run(str(txt)); set_font(rr,size=font_size,bold=True,color='163A5B')
    for ridx,row in enumerate(rows):
        cells=tbl.add_row().cells
        for i,val in enumerate(row):
            c=cells[i]; set_cell_margins(c); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if ridx%2==1: set_cell_shading(c,'F7FAFD')
            para=c.paragraphs[0]; rr=para.add_run(str(val)); set_font(rr,size=font_size); set_para_spacing(para,after=1,line=1.08)
    doc.add_paragraph().paragraph_format.space_after=Pt(2)
    return tbl

def figure(path, caption, width=6.45):
    path=Path(path)
    if not path.exists():
        p('（截图文件未找到：'+str(path)+'）', style='SmallNote'); return
    para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.space_before=Pt(5); para.paragraph_format.space_after=Pt(1)
    run=para.add_run(); run.add_picture(str(path), width=Inches(width))
    cap=doc.add_paragraph(caption, style='CaptionCN'); cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
    return para

def code(text):
    para=doc.add_paragraph(); para.paragraph_format.left_indent=Inches(0.2); para.paragraph_format.right_indent=Inches(0.1); para.paragraph_format.space_before=Pt(3); para.paragraph_format.space_after=Pt(7)
    pPr=para._p.get_or_add_pPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'F1F5F9'); pPr.append(shd)
    r=para.add_run(text); set_font(r,name='Consolas',size=9,color='203040'); return para

def pagebreak(): doc.add_page_break()

# cover
para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.space_before=Pt(45)
r=para.add_run('PHM'); set_font(r,size=30,bold=True,color='FFFFFF');
# colored run background
rPr=r._element.get_or_add_rPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'2189E8'); rPr.append(shd)
para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.space_before=Pt(28)
r=para.add_run('重复使用运载器健康管理平台'); set_font(r,size=25,bold=True,color='12345B')
para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=para.add_run('软件使用手册'); set_font(r,size=21,bold=True,color='12345B')
para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.space_before=Pt(16); r=para.add_run('面向 Windows 离线单机部署与现场操作'); set_font(r,size=12,color='5C718A')
for _ in range(3): doc.add_paragraph()
table(['文档属性','内容'],[
    ('文档版本','2.0（基于 2026-10-09 项目更新）'),('适用版本','当前 phm_platform 项目交付目录'),('适用对象','系统管理员、试验操作员、算法/健康评估人员、审查人员'),('适用环境','Windows 10/11 64 位；Chrome 或 Edge；离线单机优先'),('编制依据','当前前端路由、后端接口、项目说明及 2026-10-09 验证记录')],font_size=9.5)
para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.space_before=Pt(22); r=para.add_run('编制日期：2026 年 10 月'); set_font(r,size=11,color='5C718A')
pagebreak()

# front matter
h('阅读说明',1)
p('本手册描述当前项目中可见的菜单、页面和主要操作路径，重点覆盖数据导入与回放、MATLAB/Simulink 实时接入、窗口诊断、健康评估、寿命预测、再飞与放行评估、结构知识维护和用户权限管理。截图来自项目最近一次浏览器验证，页面中的数据集编号、时间和结果属于验证样例，现场使用时应替换为本次试验的数据。')
p('文档中的“必须”“不得”用于输入契约、权限和会影响数据完整性的操作；“建议”用于现场管理和复核。平台页面展示的算法结果是辅助信息，不能替代授权人员对型号、工况、故障真值、数据质量和模型适用范围的确认。')
p('如果你只需要快速启动，先阅读第 3 章和第 4 章；如果要执行一次完整分析，按第 5 章的“标准作业路线”依次阅读第 6～12 章；如果要排查接口或验收问题，优先查阅第 15 章和附录。')
h('目录',1)
p('以下目录按当前手册章节编排。本版目录采用静态章节清单；查找具体内容时可使用 Word 的导航窗格。')
for item in ['1 文档范围与平台定位','2 系统组成与业务闭环','3 安装、初始化与启动停止','4 登录、权限与通用页面操作','5 标准作业路线与数据准备','6 数据管理','7 状态监测与 MATLAB 实时采集','8 异常告警中心','9 故障诊断','10 健康评估','11 寿命预测','12 仿真、故障注入与事件重演','13 再飞与放行评估','14 模型、三维可视化与结构知识','15 运维、备份、故障处理与支持','附录 A 数据字段与输入契约','附录 B 2026-10-09 验证摘要','附录 C 现场检查清单','附录 D 修订记录']:
    bullet(item)

# chapter 1
chapter1 = h('1 文档范围与平台定位',1)
chapter1.paragraph_format.page_break_before = True
h('1.1 文档目的',2)
p('本手册用于指导现场人员从“准备运行环境”开始，完成平台登录、数据登记、历史回放或实时采集、算法分析、结果复核、数据导出和日常维护。它同时记录当前项目的输入约束和验证边界，使操作人员能区分页面可执行、接口可运行和工程结论可采用这三种不同状态。')
h('1.2 平台用途',2)
p('平台采用浏览器访问的 B/S 结构，后端由 Django 提供业务与接口，前端由 Vue 页面提供交互，默认使用 SQLite 保存业务记录。平台面向重复使用运载器/发射场健康管理场景，形成状态监测、异常告警、故障诊断、健康评估、剩余寿命预测、再飞与放行评估、仿真验证和结构知识维护的统一工作台。')
table(['业务域','当前入口','主要用途'],[
('综合态势','综合态势','查看 PHM 能力链、服务/数据资产状态并进入模块。'),('状态监测','遥测数据监测、异常告警中心','历史 CSV 回放或实时会话监测，持续查看告警。'),('仿真及故障注入','离线故障数据集、实时故障注入、故障事件重演','提交/查看仿真任务，组织故障场景并回放事件。'),('故障诊断','诊断分析','运行 Hier14 层次时序诊断，查看窗口事件与聚合结果。'),('健康与放行评估','部件/系统健康评估、寿命预测、再飞与放行评估','计算 HI、预测 RUL，并形成辅助放行依据。'),('模型与可视化','模型管理、三维部件定位','查看模型登记状态和部件空间定位。'),('结构与知识','PBS 结构树、多信号流图、FTA、FMECA','维护部件层级、信号关系和故障知识。'),('数据/权限','数据管理、用户与权限','登记/下载数据，分配角色和操作权限。')])
h('1.3 使用边界',2)
bullet('平台不直接控制 MATLAB/Simulink，也不需要 MATLAB Engine 才能进行 HTTP 实时上报；用户在 MATLAB 或 Simulink 侧组织信号并调用平台接口。')
bullet('仿真、诊断、健康评估和寿命预测使用各自的数据契约；同一个 CSV 能否被某个模块读取，不能推导出它适合所有模块。')
bullet('健康指数 HI 以 0～1 展示，接近 1 表示接近所选正常参考或算法定义的健康状态；不同算法的 HI 未经过统一工程标定，不能直接横向比较。')
bullet('“接口成功返回”只证明输入、预处理和模型调用链路打通；没有独立真值标签时，不能据此宣称诊断精度、健康度或寿命精度通过验收。')

# chapter 2
h('2 系统组成与业务闭环',1)
h('2.1 运行组成',2)
table(['组成','目录/接口','操作要点'],[
('前端成品','frontend/dist','正常运行直接使用已构建页面；修改源码后才需重建。'),('Django 后端','phm_backend、各业务 app','负责登录、数据集、会话、算法调用、权限和导出。'),('数据库','db.sqlite3','保存用户、结构、数据集、会话、告警及结果索引。'),('上传与运行文件','media/','保存 CSV、仿真输出和可下载文件；需与数据库一起备份。'),('Hier14 诊断资源','health-main 或交付包中已登记资源','要求原始状态字段；派生 P 参数不能直接替代。'),('健康评估资源','platform_handoff_20260911_v1/health_bundle','提供评估适配器、模型注册和健康模型资产。'),('MATLAB 工具','integrations/matlab/','提供 phm_send_telemetry.m 和实时演示脚本。'),('日志','logs/','保留启动、算法验证和故障排查证据。')])
h('2.2 业务闭环',2)
p('一次完整的现场分析通常按“数据准备 → 数据登记 → 回放或采集 → 告警观察 → 诊断/健康评估 → 寿命预测 → 放行复核 → 结果导出与留档”执行。每一步都应保留数据集 ID、采集会话 ID、算法/模型名称、时间范围、部件或 PBS 关联、结果截图和复核人。')
figure(ROOT/'docs/manual_20261010/screenshots/overview.png','图 2-1 综合健康态势页展示 PHM 能力链、服务与数据状态。')
figure(IMG/'algorithm_validation_20261009'/'real-pump-diagnosis-desktop.png','图 2-2 诊断页面展示窗口告警事件、全程聚合类别和数据来源信息。')

# chapter 3
h('3 安装、初始化与启动停止',1)
h('3.1 交付目录检查',2)
p('将离线交付目录完整解压到本地可写路径，例如 D:\\PHM\\phm_platform_offline。不要只复制启动脚本或 frontend/dist；启动脚本会按自身所在目录定位资源。解压后应能在根目录同时看到 manage.py、runtime（如交付包提供）、offline（如交付包提供）、frontend、media、config、db.sqlite3 和 start_phm_platform.bat。')
table(['文件/目录','用途','是否建议备份'],[
('start_phm_platform.bat','一键检查环境、迁移并启动服务','否'),('stop_phm_platform.bat','停止平台服务','否'),('setup_migration.ps1','离线环境检查或重建','否'),('runtime/、offline/','包内运行时和离线依赖（若交付包包含）','建议保留'),('db.sqlite3','业务数据库','必须'),('media/','上传和仿真文件','必须'),('config/','系统配置和路径','必须'),('logs/','运行与验证证据','建议')])
h('3.2 首次初始化',2)
num('双击 install_runtime_offline.bat（如交付包提供），按提示完成 Python 3.10 和 Node.js 的离线安装。已包含完整运行时的交付包通常无需再次安装系统级 Node.js。')
num('在项目根目录打开 PowerShell，执行 setup_migration.ps1；脚本会使用包内 Python 创建 .venv 并从本地 wheel 安装依赖。')
num('如果数据库中还没有管理员，启动一次平台后，在根目录执行 .\\.venv\\Scripts\\python.exe manage.py createsuperuser，按提示输入用户名、邮箱和密码。')
code("cd D:\\PHM\\phm_platform_offline\n.\\.venv\\Scripts\\python.exe manage.py createsuperuser")
p('旧版 create_superuser.py 或 create_superuser.bat 可能受环境和语法影响；当前建议优先使用 Django 内置 createsuperuser 命令。')
h('3.3 启动、访问和停止',2)
num('双击 start_phm_platform.bat，等待服务器窗口保持运行。')
num('浏览器访问 http://127.0.0.1:8000/；若没有自动打开浏览器，手动输入地址。')
num('登录后先打开“综合态势”，点击“刷新平台状态”，确认服务、模型资产和数据状态。')
num('停止时先结束 MATLAB 上报或实时采集会话，再双击 stop_phm_platform.bat，或在服务器窗口按 Ctrl+C。')
code("$env:USE_SQLITE = 'true'\n.\\.venv\\Scripts\\python.exe manage.py migrate\n.\\.venv\\Scripts\\python.exe manage.py runserver 127.0.0.1:8000")
h('3.4 启动后状态判断',2)
p('综合态势页面的状态灯反映算法、模型和仿真数据资产是否已装载，不等同于基础服务是否启动。RUL Shadow“已登记（开发）”表示资源登记存在但不作为正式在线推理；仿真数据/MATLAB 在没有现场数据或 MATLAB 会话时显示“待配置”属于预期状态。')
figure(ROOT/'docs/manual_20261010/screenshots/offline.png','图 3-1 离线故障数据集页展示注入参数与仿真任务区。')
figure(IMG/'algorithm_validation_20261009'/'real-simulink-desktop.png','图 3-2 离线故障数据集完成后显示 Engine 状态、任务进度和原始/派生输出。')

# chapter 4
h('4 登录、权限与通用页面操作',1)
h('4.1 登录与退出',2)
num('在登录页输入管理员或查看用户账号和密码，点击“登录”。')
num('进入综合态势后确认右上角显示当前环境、时间和“退出登录”按钮。')
num('完成操作后点击“退出登录”；仅关闭浏览器标签不会主动注销会话。')
h('4.2 角色与权限',2)
table(['角色','默认能力','现场建议'],[
('管理员','用户、权限、结构、数据登记与删除、采集会话、算法执行、导出和维护','由系统管理员持有；不要多人共用。'),('查看用户','查看平台数据、结果和页面，通常不能执行管理操作','适合评审、值班和结果复核。'),('自定义权限用户','由管理员按“用户与权限”页面分配具体能力','每次变更后让用户重新登录并验证菜单。')])
p('当前版本明确受权限控制的写操作包括数据上传、删除和 PBS 关联、结构维护、用户维护、实时会话创建/结束及仿真提交。页面按钮是否显示仍受角色和具体权限控制。需要特别注意：当前诊断、健康评估和 RUL 的部分预测接口在代码层尚未统一加上 run_analysis 权限校验，查看用户在某些部署配置下仍可能看到或调用分析按钮；如果验收要求“查看用户不得运行分析”，应先完成接口权限加固并重新验证，不能只依据菜单是否隐藏。数据删除、结构删除、模型登记和放行结论必须由授权人员执行。')
h('4.3 页面通用控件',2)
bullet('下拉框：先选数据集、会话、算法或部件，再点击“运行/评估/播放”等动作。')
bullet('表格：表头可排序或筛选；横向较宽的结果表应使用底部滚动条或缩小浏览器缩放。')
bullet('图表：时间序列通常支持拖动、缩放、重置和下载；缩放只影响显示范围，不改变原始文件。')
bullet('状态标签：绿色通常表示成功/健康，黄色表示等待、兼容性提示或需要复核，红色表示错误、严重告警或失败。')
bullet('返回/刷新：数据登记、会话和算法结果在变更后应点击页面刷新，确认数据库已保存。')
h('4.4 数据记录原则',2)
p('每次操作至少记录“操作者、时间、数据集 ID 或会话 ID、算法/模型、参数、页面结果、导出文件路径和复核结论”。截图不能替代原始 CSV 或数据库记录；对于告警和放行结论，建议同时保留原始输入、结果 JSON/CSV、页面截图和人工签名。')

# chapter 5
h('5 标准作业路线与数据准备',1)
h('5.1 历史数据路线',2)
for x in ['准备 UTF-8 编码 CSV，确认时间列、字段名、单位、采样间隔和故障标记含义。','在“数据管理”填写名称、故障类型、系统和可选 PBS 单机产品，使用“上传单个数据集”登记文件；多个文件改用“批量导入数据”。','在“状态监测 → 遥测数据监测”选择“CSV 历史回放”，确认数据集、时间列和信号，先小速度播放检查趋势。','在“故障诊断”选择同一数据集和合适算法，运行单个或批量诊断，查看窗口事件和聚合结果。','在“健康与放行评估 → 部件/系统健康评估”选择与数据类型匹配的评估算法，记录 HI、正常参考来源和裁剪/假设提示。','在“寿命预测”选择满足输入契约的数据和正确部件模型；完成 PBS 关联核对后运行预测。','在“再飞与放行评估”汇总诊断、健康、寿命和人工复核信息，生成或保存辅助结论。']:
    num(x)
p('单个文件使用上传区的“上传单个数据集”；多个文件才使用“批量导入数据”。单个上传表单实际填写名称、故障类型、系统、可选 PBS 单机产品和文件，来源由当前页面按 offline 记录，数据角色由后端依据文件和仿真元数据判断。')
h('5.2 实时采集路线',2)
for x in ['在“状态监测 → 遥测数据监测”选择 MATLAB 实时采集，输入试验名称并创建会话。','保存一次性 Token 和平台生成的 MATLAB 代码；Token 不提交到代码仓库或聊天群。','在 MATLAB 运行 addpath、连通测试和采样循环/实时故障演示。','转到“异常告警中心”，选择同一会话并启用实时检测；确认状态为“正在连续检测”。','观察告警、诊断和健康指数；出现异常时记录告警时间、信号值、阈值、隔离对象和会话采样数。','停止上报后回到平台点击“结束采集”，再导出 CSV；结束后的会话不可继续写入，但仍可查询和导出。']:
    num(x)
h('5.3 数据质量预检',2)
table(['检查项','要求','不满足时的处理'],[
('编码/分隔符','UTF-8；常用逗号分隔；首行字段名唯一','转换编码或清理重复列名后重新上传。'),('时间列','time/Time/timestamp 等可识别；历史数据最好单调递增','明确时间列并检查重复、倒序、单位。'),('数值','特征列为有限数值，不含 NaN、Inf、空白和混合单位','在源系统清理；不要用字符串替代缺失值。'),('采样轴','诊断/寿命按各自契约处理；不能默认固定采样','记录采样间隔和重采样方法。'),('字段契约','Hier14 必须同时含 Time、29 个原始状态字段和 FaultFlag；寿命可使用派生 P 参数或同次配对原始数据','根据算法页的错误提示改选数据，不要强行上传不匹配文件。'),('真值标签','Hier14 的 FaultFlag 必须存在，取 0/1；它不进入模型特征，只用于窗口筛选和真值核对','没有真值时也要按数据定义填 0/1，不能省略该列。')])

# chapter 6
h('6 数据管理',1)
h('6.1 上传和登记',2)
p('进入“数据管理”，单个文件在上传区填写名称、故障类型、系统和可选 PBS 单机产品，选择 CSV 后点击“上传单个数据集”。来源由当前页面固定记录为 offline，页面没有单独的“数据类型”输入；数据角色由后端根据文件内容、文件名或仿真输出元数据判断。上传成功后记录数据集 ID；后续所有诊断、评估和寿命结果都应引用该 ID。数据名称应能区分试验、工况、故障类型、原始/派生角色和生成日期，避免只使用“测试数据”等无意义名称。')
h('6.2 原始与派生数据',2)
p('当前平台对仿真或数据处理结果同时登记“原始状态量”和“派生参数”角色。数据管理列表默认隐藏明确登记的仿真派生记录，当前页面没有“显示派生参数”开关；派生文件仍保存在后台，并由寿命预测适配器按同次仿真关系自动配对。Hier14 选择器会排除派生记录，因为模型要求 29 个原始字段；其他算法也应按页面契约选择数据。')
figure(ROOT/'docs/manual_20261010/screenshots/data.png','图 6-1 数据集构建和管理页：上传、查询、PBS 关联、预览和下载。')
figure(ROOT/'docs/manual_20261010/screenshots/data-preview.png','图 6-2 数据预览弹窗：显示时间字段、故障标记、参数列数和采样点。')
h('6.3 批量导入与质量预检',2)
p('管理员可在上传区选择一个或多个 CSV、JSON、JSONL 或 XLSX 文件，点击“批量导入数据”。页面返回成功/失败数量和逐文件结果；失败文件不会回滚已经成功导入的文件。批量导入前建议先按文件名、时间列和字段契约检查，导入后再逐条打开“查看数据”核对时间字段、FaultFlag 和参数列数。')
num('点击“选择文件”并选择多个文件；不要把同一个文件重复选择。')
num('点击“批量导入数据”，等待提示“成功/失败”统计完成。')
num('对失败项记录文件名和错误原因，修正后单独重新导入；不要直接删除整批已成功记录。')
num('用“关键字、来源、系统、故障类型”过滤并记录生成的数据集 ID。')
figure(ROOT/'docs/manual_20261010/screenshots/data-preview.png','图 6-3 数据预览用于核对字段角色、样本数和首次故障时间。')
h('6.4 下载、修改和删除',2)
bullet('下载前确认数据集 ID、文件名和来源，下载文件应与结果报告一起归档。')
bullet('修改登记名称不会改变 CSV 内容、路径和数据集 ID；修改 PBS/部件关联会影响寿命模型选择，应保留变更记录。')
bullet('删除数据前确认是否有诊断、健康评估、寿命预测、仿真任务或放行记录引用它；删除可能使结果无法复现。')

# chapter 7
h('7 状态监测与 MATLAB 实时采集',1)
h('7.1 CSV 历史回放',2)
num('打开“状态监测 → 遥测数据监测”，选择“CSV 历史回放”。')
num('选择数据集，确认时间列和信号字段；平台会显示样本数、当前状态和图表。')
num('设置播放速度，点击“开始回放”；拖动图表缩放查看异常时段。')
num('点击下载/导出保存原始 CSV 或当前会话结果。')
p('历史回放只是展示和数据检查，不会自动替代诊断和健康评估。需要分析时，应在对应业务页面重新选择同一数据集并执行算法。')
h('7.2 创建 MATLAB 会话',2)
num('进入“状态监测 → 遥测数据监测”，点击“选择数据源”，选择“MATLAB 实时采集”。')
num('输入本次试验名称，点击“创建并获取 MATLAB 参数”。Token 只显示一次，立即保存。')
num('点击“复制全部 MATLAB 代码”，粘贴到 MATLAB 命令窗口，先执行连通测试，再执行实际采样循环。')
p('连通测试和故障演示不能在同一会话连续运行：测试样本只有 time、pressure、temperature 三个字段，演示脚本会从 time=0 开始并发送 attitude_error、control_error，混用会违反同一会话 time 严格递增和字段稳定约束。测试成功后结束该会话；要运行演示，请重新创建会话、更新 URL 和 Token、在告警中心重新选择新会话。该演示仅验证实时告警链路，不提供 Hier14 的 29 列输入，也不直接提供 RUL 的 P 参数或 HI。')
code("% MATLAB 2012 及以上版本，确认 JVM 可用\nassert(usejava('jvm') == 1);\naddpath('D:/PHM/phm_platform_offline/integrations/matlab');\naddpath('D:/PHM/phm_platform_offline/integrations/matlab/examples');\ningestUrl = 'http://127.0.0.1:8000/api/v1/phm/telemetry/sessions/<会话ID>/ingest/';\ntoken = '<创建会话时显示的 Token>';\ntestSample = struct('time',0,'pressure',10.0,'temperature',25.0);\nresponse = phm_send_telemetry(ingestUrl, token, testSample);\ndisp(response);")
h('7.3 实际采样约束',2)
table(['约束','说明'],[
('time 严格递增','同一会话不能重复或倒退；仿真重新从 0 开始时新建会话。'),('字段稳定','同一会话内字段名称和数量保持一致。'),('数值有限','不得发送 NaN、Inf、字符串或空值。'),('发送节奏','高频仿真建议缓存后每 0.2～1 秒批量发送，避免网页和后端被单点请求淹没。'),('跨电脑接入','把 127.0.0.1 改为平台服务器局域网 IP，确认 8000 端口、防火墙和路由可达。'),('结束方式','平台点击“结束采集”；结束会话不可继续写入。')])
h('7.4 实时故障注入演示',2)
num('结束上一条连通测试会话并新建 MATLAB 实时采集会话；将新会话的 URL 和 Token 填入代码。')
code("% 0～3 秒正常，之后注入压力下降\nfaultStartTime = 3.0;\nduration = 60.0;\nsamplePeriod = 0.25;\nresponses = demo_realtime_fault_injection(ingestUrl, token, faultStartTime, duration, samplePeriod);")
p('该演示只发送 5 个实时告警链路字段，适用于观察压力阈值告警、会话采样数和检测状态；它不应直接送入 Hier14 或寿命预测。需要运行 Hier14 时准备包含 Time、FaultFlag 和完整 29 个原始状态字段的 CSV；需要运行 RUL 时准备 P 参数/HI 或可自动配对的原始数据。')
figure(ROOT/'docs/manual_20261010/screenshots/telemetry-source.png','图 7-1 实时状态监测页：选择 CSV 回放或 MATLAB 实时采集。', width=5.2)
figure(IMG/'algorithm_validation_20261009'/'real-realtime-mobile.png','图 7-2 移动视口下的实时采集/告警页面验证，说明页面支持窄屏操作但现场建议使用桌面浏览器。')

# chapter 8
h('8 异常告警中心',1)
h('8.1 启用检测',2)
num('完成实时会话创建并发送至少一条测试数据。')
num('打开“状态监测 → 异常告警中心”，选择同一会话。')
num('打开“实时检测”开关，确认提示变为“正在连续检测实时数据”或“检测已启用，等待实时数据接入”。')
num('实时数据到达后查看告警表：时间、等级、诊断故障、异常信号、检测依据、隔离对象和健康指数。')
h('8.2 告警判读',2)
p('告警表中的“检测依据”给出信号值、运算符和阈值；“严重/警告/提示”描述告警等级，不等同于故障类别置信度。实时页面只加载当前主动选择的会话，新打开页面不会自动显示历史告警。出现告警后，先核对源数据和阈值，再进入故障诊断和健康评估页面做更完整分析。')
table(['现象','优先检查'],[
('没有会话','确认已在遥测页面创建会话，且浏览器使用同一登录会话。'),('一直等待数据','先执行单条 MATLAB 测试；检查 URL、会话 ID、Token 和 8000 端口。'),('会话采样数增加但无告警','确认实时检测开关已启用，检查信号字段和阈值适用范围。'),('显示 stale/接收中断','检查 MATLAB 进程、网络和最近一次上报时间；不要立即创建多个重复会话。'),('告警过多','先导出原始数据，核对噪声、单位和采样间隔，再由授权人员调整规则。')])
figure(ROOT/'docs/manual_20261010/screenshots/alarms.png','图 8-1 实时异常告警中心：选择会话、启用检测并查看告警表。')
figure(IMG/'algorithm_validation_20261009'/'real-gyro-diagnosis-desktop.png','图 8-2 诊断结果与告警事件联动示例。')

# chapter 9
h('9 故障诊断',1)
h('9.1 单个诊断与批量诊断',2)
p('进入“故障诊断 → 诊断分析”，在“单个诊断/批量诊断”之间切换。选择数据集和算法后运行；当前项目验证重点为 Hier14 层次时序诊断。运行后页面展示窗口告警事件、数据来源、系统/部件、故障标签（录入信息）、注入时间以及全程聚合信息。')
figure(IMG/'algorithm_validation_20261009'/'real-pump-diagnosis-desktop.png','图 9-1 Hier14 诊断详情：窗口开始/结束时间、窗口数、最高置信度和聚合类别。')
h('9.2 Hier14 输入与结果口径',2)
table(['项目','当前口径'],[
('输入','29 个原始状态字段；窗口长度 128、步长 64，每 4 行取样。派生 P1～P17 不能替代原始字段。'),('窗口事件','按连续相同异常类别、概率至少 0.55 的窗口汇总；事件来自预测窗口，不读取故障真值。'),('评分','推理后使用 FaultFlag 核对真值；跨越注入/恢复边界的混合窗口不计分。'),('全程聚合','页面显示全程平均/聚合类别；短时故障可能被全程平均掩盖，应优先查看窗口事件。'),('边界','新仿真数据中曾观察到正常误报，当前不能把少量成功识别案例外推为全部故障精度。')])
h('9.3 诊断操作步骤',2)
for x in ['在数据管理确认数据类型为原始状态量，且字段齐全。','在诊断页选择单个数据集和 Hier14，点击运行并等待状态完成。','先看窗口事件表：异常类别、开始/结束秒数、窗口数和最高置信度。','再看全程聚合类别与概率，避免只依据一个最终类别做结论。','记录数据集、算法版本、模型资源、运行时间和页面截图；批量任务逐个核对失败项。']:
    num(x)
p('Hier14 加载失败或输入不符合契约时，当前系统应明确报错，不应静默换成启发式算法。现场遇到“模型未启用”时，先查看综合态势状态和后端日志，再处理资源路径或版本问题。')

# chapter 10
h('10 健康评估',1)
h('10.1 评估层级与算法',2)
p('进入“健康与放行评估 → 部件/系统健康评估”，页面支持部件级和系统级评估、单个和批量评估。当前适配器可调用 CDPCA-GA、AE-GMM 等部件/系统健康评估方法；GCN/RBD 接口可运行，但使用结果时必须确认部件映射和独立样本条件。')
table(['算法/层级','用途','解释边界'],[
('CDPCA-GA 部件级','基于相对正常参考计算特征融合和 HI','HI 是当前输入相对参考的健康候选值，尚未按型号/工况/故障等级标定。'),('AE-GMM 部件级','基于自编码器和 GMM 的异常/健康评估','训练迭代可能有未收敛提示；需保留提示并由算法人员复核。'),('GCN/RBD 系统级','部件到系统的健康融合接口','同一次物理运行的原始/派生文件不能当作两个独立部件样本。'),('批量评估','一次提交多个数据集并返回成功/失败列表','单个失败不应阻断其他文件，但必须记录失败原因。')])
h('10.2 方向修正后的 HI 解释',2)
p('2026-10-09 的健康评估修正改为优先使用已登记的同次正常基线并按时间对齐计算偏离；HI 越接近正常参考越接近 1，偏离时下降，恢复时允许回升。没有正常基线时才使用故障注入前的初始参考段，并在结果中标注假设。FaultFlag 只用于验证，不进入推理特征。')
figure(IMG/'algorithm_validation_20261009'/'health-batch-desktop.png','图 10-1 健康评估批量结果页：显示成功/失败数、HI、健康等级、样本数和详情。')
figure(ROOT/'docs/manual_20261010/screenshots/flow.png','图 10-2 多信号流图展示数据集、PBS、信号与健康/寿命输入之间的接入关系。')
h('10.3 健康评估步骤',2)
p('页面没有手动选择正常基线的控件。部件评估会按数据集的仿真 provenance 自动查找同飞行次数、同模型和同输出类型的无故障基线；找不到时使用故障注入前的初始参考段，并在结果中标注参考来源。现场要保证无故障基线先完成仿真并登记，且与故障数据保持同一飞行次数、模型、时长和输出类型。')
for x in ['选择部件级或系统级。','确认无故障基线已按同次仿真条件登记，并检查结果中的参考来源和 PBS 关联。','选择算法后点击评估，等待结果完成。','查看 HI、等级、样本数、参考来源、输入特征和结果属性。','如果页面提示“尚未按型号与工况标定”“裁剪比例高”或“未关联 PBS”，把提示写入评估记录，不要省略。']:
    num(x)
h('10.4 结果限制',2)
bullet('HI 不是跨算法、跨型号或跨工况的统一分数；不同算法输出差异大时，应回到正常参考、输入字段和模型版本核对。')
bullet('正常参考来源和时间轴比单一数值更重要；参考段混入故障会导致方向和基线错误。')
bullet('GCN/RBD、系统级融合和放行结论必须结合真实部件映射及独立样本复核。')

# chapter 11
h('11 寿命预测',1)
h('11.1 输入选择与部件映射',2)
p('进入“健康与放行评估 → 寿命预测”，选择数据集、寿命模型和部件。当前集成模型使用 health-main 训练资产。派生数据可直接提供所需 P 参数；原始状态量数据由接口查找已完成登记的同次派生文件，要求 Time 时间轴完全一致。缺少配对或时间轴不一致时应明确报错。')
table(['模型编号','部件','参数','页面选择要点'],[
(1,'液氧泵','P1','选择液氧泵；确认 PBS 关联一致。'),(2,'液氧涡轮','P2','不要用相邻编号参数替代。'),(3,'煤油管路','P3','原始数据需能找到同次派生 P3。'),(4,'煤油阀门','P4','核对模型与部件名称。'),(5,'燃气发生器','P5','特征顺序与其他部件不同。'),(6,'燃烧室','P6','输入会执行 1-HI 方向处理。'),(7,'喷管','P7','使用模型 7。'),(8,'TVC','P8','使用模型 8。'),(9,'RCS','P10','P10，不是 P9。'),(10,'栅格舵','P9','P9，不是 P10。'),(11,'传感器','P12','P11 不属于交付 15 个模型。'),(12,'液氧管路','P14','使用模型 12。'),(13,'液氧阀门','P15','使用模型 13。'),(14,'煤油泵','P16','使用模型 14。'),(15,'煤油涡轮','P17','使用模型 15。')])
h('11.2 冻结预处理与结果单位',2)
p('当前预处理按 Time 构建 [起点，起点+2 秒) 窗口，每 1 秒移动，计算 min、mean、rms、max，再按训练顺序排列，并使用保存的 scaler、PCA 和 hi_meta 资产，不在新 CSV 上重新拟合。集成 RUL 输出单位为秒（s）；页面的 HI 为 0～1。至少需要 51 个 HI 窗口；按 1 秒步长通常需要约 51 秒时间跨度。')
figure(IMG/'rul_validation_20261009'/'rul-derived-desktop.png','图 11-1 寿命预测页显示模型、部件参数、当前 HI、RUL（秒）和健康趋势图。')
h('11.3 寿命预测步骤',2)
for x in ['先在数据管理确认数据角色和 PBS/部件关联。','选择原始或派生数据，选择匹配部件模型；不要仅按参数编号猜测部件。','确认页面显示的输入参数、窗口长度、步长和数据量。','点击“运行预测”，查看当前 HI、RUL、趋势和结果限制。','如果裁剪比例很高、提示超出训练归一化范围或数据未关联 PBS，把结果作为接口/趋势参考，不能作为已验证真实剩余寿命。','批量预测时逐个查看失败项；一个错误文件不应阻断其他文件。']:
    num(x)
h('11.4 典型问题',2)
table(['提示/现象','原因与处理'],[
('缺少 HI 列','使用派生 P 参数或已有合法 HI 列；原始 CSV 需通过同次派生配对。'),('部件不匹配','数据集 PBS 关联与模型部件不一致；回到数据管理修正关联或重新选择模型。'),('时间轴不一致','原始与派生文件不是同次输出；不得强行配对。'),('裁剪比例高','输入超出训练归一化范围；保留提示，先做工况/单位和训练范围核对。'),('RUL 单位误读','当前仿真 Time 为秒，页面显示“秒 (s)”；不要按小时解释。')])

# chapter 12
h('12 仿真、故障注入与事件重演',1)
h('12.1 离线故障数据集',2)
p('进入“仿真及故障注入 → 离线故障数据集”。页面支持选择子系统和故障类型、设置注入时间、恢复时间、飞行次数，提交仿真任务并查看排队、启动引擎、配置模型、求解、导出 CSV、登记数据集等阶段。')
num('确认 MATLAB/Simulink Engine 状态和模型版本提示。跨版本兼容加载时，页面会提示“模型为 R2023a，本机使用 R2022b 兼容加载”；这说明任务可运行，不代表跨版本结果已经通过验收。')
num('填写任务名称、子系统、故障类型、注入/恢复时间和飞行次数。')
num('点击“提交仿真”，等待任务状态完成；不要在求解期间关闭服务窗口。')
num('在仿真输出表核对原始/派生数据集 ID、样本数、FaultFlag 样本数、参数数和下载链接。')
figure(ROOT/'docs/manual_20261010/screenshots/replay.png','图 12-1 故障事件重演页支持时间窗口、倍速、播放/暂停和曲线查看。')
figure(IMG/'algorithm_validation_20261009'/'real-simulink-desktop.png','图 12-2 离线仿真任务完成后展示 29 参数原始 CSV 与 17 参数派生 CSV。')
h('12.2 真实联调结果的正确使用',2)
p('2026-10-09 已完成泵气蚀、无故障基线和陀螺仪恒偏差三组真实 Simulink 运行并登记数据集。Hier14 可以在原始状态量上运行并识别本次完整故障窗口，但新数据正常误报明显；MSFG+TEAMS-RT 和 PCA-iForest 当前不能作为一院 13 类故障准确识别的验收结论。现场使用时应把这些数据作为接入、流程和算法验证样例，不能把样例表现外推到所有飞行次数或故障类别。')
h('12.3 故障事件重演',2)
p('进入“故障事件重演”，选择历史数据集或已保存的故障事件，按时间范围查看异常前后趋势。重演用于复盘告警、诊断窗口和健康指数变化；它不会改变原始数据。复盘报告应注明时间范围、数据集 ID、事件类别、相关信号和人工判断。')

# chapter 13
h('13 再飞与放行评估',1)
h('13.1 评估目的',2)
p('再飞与放行评估用于把诊断、健康、寿命和人工检查结果放到同一复核流程中，形成辅助决策记录。它不是自动放行器，页面结果需要由授权人员结合部件检查、任务约束、历史维修和组织流程签字确认。')
figure(ROOT/'docs/manual_20261010/screenshots/release.png','图 13-1 再飞与放行评估页：配置分系统健康度、权重、寿命裕度和严重告警。')
h('13.2 配置参数与执行',2)
p('页面左侧先填写运载器编号和任务名称，再为动力、电源、测控、导航制导与控制、结构设置健康度（0～100）和权重。权重合计必须约等于 100%；页面会显示归一化权重。然后填写寿命裕度、未关闭严重告警数、放行阈值和子系统最低阈值，点击“执行放行评估”。右侧显示系统健康指数、加权健康度、RBD 等效健康、任务成功概率和阻断项。')
table(['参数','含义','注意'],[('健康度','分系统当前状态 0～100 分','应有诊断/健康结果或人工检查依据。'),('权重','分系统在整器评估中的重要程度','合计应为 100%；后端会归一化。'),('寿命裕度','预计剩余寿命或可复用裕度','越低会降低成功概率。'),('严重告警','未关闭严重告警数量','每条都会降低概率并可能形成阻断项。'),('放行阈值','建议放行的最低成功概率','只是辅助判据，不替代组织流程。'),('子系统最低阈值','任一模块低于该值时的阻断线','由授权人员按任务要求设定。')])
h('13.3 建议的复核顺序',2)
for x in ['确认本次数据集、采集会话或仿真任务身份，检查时间范围和来源。','核对告警是否为真实异常、传感器异常或规则误报；查看原始趋势和检测阈值。','核对 Hier14 窗口事件与全程聚合差异，避免只看最终类别。','核对健康评估的正常参考、HI 方向、裁剪比例和部件/PBS 关联。','核对 RUL 输入契约、模型部件、单位和结果限制。','在放行页面记录结论、依据、人工复核人和后续措施，保存导出文件与截图。']:
    num(x)
h('13.4 结论分级建议',2)
table(['结论状态','使用条件'],[
('可继续分析','输入、字段和模型调用正常，但尚未完成工程精度或独立真值验证。'),('需人工复核','存在告警、健康度明显下降、RUL 裁剪比例高、模型兼容性提示或 PBS 未关联。'),('不建议放行','数据质量不合格、模型/部件不匹配、时间轴无法配对、关键告警未解释或结果失败。'),('授权放行','仅在组织流程要求的全部检查、人工签署和证据归档完成后使用。')])

# chapter 14
h('14 模型、三维可视化与结构知识',1)
figure(ROOT/'docs/manual_20261010/screenshots/models.png','图 14-1 模型管理页：查看内置模型并由管理员导入 ZIP 算法包。')
h('14.1 模型管理',2)
p('“模型与可视化 → 模型管理”用于查看模型目录、业务域、版本、状态和登记标识。模型管理页主要提供状态查询和登记信息，不等同于模型已通过当前工况精度验收。运行算法时仍应以业务页面显示的实际模型、数据契约和结果限制为准。')
p('管理员展开“导入模型 / 算法”，选择包含 manifest.json、入口 Python 文件和模型资产的 ZIP，点击“导入算法包”。当前限制为单包上传不超过 200 MB、解压后不超过 500 MB；已有 key 不覆盖。导入成功后列表显示“已导入，待验证”，必须在测试数据上实际运行后再进入正式目录。')
code('{ "key": "my_rul_model", "name": "我的寿命模型", "version": "1.0", "category": "rul", "entrypoint": "algorithm.py:predict", "min_rows": 51, "parameters": {} }')

figure(ROOT/'docs/manual_20261010/screenshots/structure.png','图 14-2 PBS 结构树：维护运载器、分系统、子系统和单机产品层级。')
figure(ROOT/'docs/manual_20261010/screenshots/fta.png','图 14-3 FTA 图形化故障树：编辑节点、逻辑门和连线。')
figure(ROOT/'docs/manual_20261010/screenshots/fmeca.png','图 14-4 FMECA 管理：维护部件、故障模式、原因和风险等级。')
figure(ROOT/'docs/manual_20261010/screenshots/three-dimensional.png','图 14-5 三维可视化监控：选择仿真单元、定位部件和查看运行状态。')
h('14.2 三维部件定位',2)
p('“三维部件定位”用于从部件列表或场景选择目标，查看模型空间位置、视角和结构关系。三维页面用于定位和沟通，不会自动把异常结果映射为全系统故障；应将部件名称、PBS 编码和诊断/健康页面的结果相互核对。')
figure(ROOT/'docs/manual_20261010/screenshots/users.png','图 14-6 用户与权限：管理员创建账号并配置功能权限。')
h('14.3 PBS 结构树',2)
p('“结构与知识 → 运载器 PBS 结构树”展示产品、系统、子系统和部件层级。新增或修改节点时填写唯一标识、名称、父节点和层级，保存后刷新验证。删除节点可能影响子节点、PBS 关联和放行记录，必须在删除前导出结构和引用记录。')
num('新增节点：点击“新增根节点”或父节点后的“新增下级”，填写节点标识、名称、层级、PBS 编码和父节点，保存后刷新。')
num('编辑/移动：选择节点，点击“编辑/移动”，修改名称、PBS 编码或父节点；节点标识用于稳定引用，不建议随意改变。')
num('关联数据：在“数据管理”对数据集点击“关联 PBS”，选择结构树中的单机产品并保存；寿命模型会据此阻止明显的部件不匹配。')
num('删除节点：确认级联影响后再删除；删除前导出结构和数据集关联清单。')

h('14.4 多信号流图、FTA 与 FMECA',2)
table(['模块','操作重点','风险控制'],[
('多信号流图','维护测点、信号、部件和故障关系，检查方向和依赖。','关系错误会影响解释和定位；修改后要做一条已知事件回放。'),('FTA 故障树','维护 AND/OR 逻辑、节点和连接，保存版本。','避免循环引用和重复边；删除节点前检查其连接。'),('FMECA','维护故障模式、原因、影响、严重度/发生度/探测度等知识。','等级和知识结论需由专业人员确认，页面不自动生成放行结论。')])

# chapter 15
h('15 运维、备份、故障处理与支持',1)
h('15.1 日常备份',2)
p('停止平台和 MATLAB 上报后，至少备份 db.sqlite3、media/、config/、logs/以及使用到的外部模型/资源路径信息。只备份数据库会导致记录存在但 CSV 和附件找不到；只备份 CSV 又会丢失数据集、结构和结果索引。建议按日期建立备份目录并记录平台版本、Python、MATLAB、模型权重和依赖版本。')
code("# 示例：停止服务后复制到备份目录\nNew-Item -ItemType Directory -Force .\\backup\\2026-10-10 | Out-Null\nCopy-Item .\\db.sqlite3 .\\backup\\2026-10-10\\\nCopy-Item .\\media .\\backup\\2026-10-10\\ -Recurse\nCopy-Item .\\config .\\backup\\2026-10-10\\ -Recurse\nCopy-Item .\\logs .\\backup\\2026-10-10\\ -Recurse")
h('15.2 恢复与验证',2)
num('停止平台，先对当前 db.sqlite3 和 media/ 做一次安全副本。')
num('使用同一版本或经过迁移验证的项目目录恢复 db.sqlite3、media/ 和 config/。')
num('核对外部模型路径、Python 依赖、MATLAB 版本和权限。')
num('启动平台后依次检查登录、数据集列表、CSV 下载、结构树、模型状态、诊断和寿命页面。')
num('使用一份已知样例执行回放和算法调用，记录恢复验证结果。')
h('15.3 常见问题',2)
table(['问题','排查路径'],[
('页面打不开','确认启动窗口未关闭；访问 127.0.0.1:8000；检查 8000 端口占用。'),('登录失败','确认使用同一目录和数据库；管理员重新核对账号或创建超级用户。'),('前端无变化','重启平台并 Ctrl+F5；源码变更后确认 npm run build 成功。'),('模型未启用','查看综合态势错误提示、资源目录、权重和依赖版本；检查 logs。'),('MATLAB 函数未找到','addpath 指向 integrations/matlab；执行 which phm_send_telemetry。'),('Token 无效','确认复制完整、属于当前会话且会话未结束；必要时新建会话。'),('time 必须递增','新建会话，从 0 开始的仿真不能写入旧会话。'),('寿命模型拒绝数据','核对 HI/P 参数、原始/派生配对、Time 时间轴和部件 PBS。'),('结果精度疑问','先检查输入契约、参考来源、窗口口径和验证标签，不要仅看接口 200。')])
h('15.4 支持信息',2)
p('反馈问题时提供 Windows/Python/Node.js/MATLAB 版本、平台地址、页面路径、复现步骤、数据集或会话 ID、启动窗口错误、浏览器控制台错误和 logs/django.log 对应时间段。不要发送密码、完整 Token 或未经脱敏的客户数据。')

# appendices
h('附录 A 数据字段与输入契约',1)
h('A.1 通用 CSV 示例',2)
code("Time,X,Y,H,Vx,Vy,Vz,FT,Roll,Pitch,Yaw,S1,S2,S3,S4,S5,S6,S7,S8,S9,S10_X,S10_Y,S10_Z,S11,S12,S13,S14,S15,S16,S17,FaultFlag\n0,0,0,100,0,0,0,1000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n1,0,0,100,0,0,0,1000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
p('Hier14 CSV 必须包含 Time、FaultFlag 和以下 29 个原始状态列，列名必须完全匹配：X、Y、H、Vx、Vy、Vz、FT、Roll、Pitch、Yaw、S1、S2、S3、S4、S5、S6、S7、S8、S9、S10_X、S10_Y、S10_Z、S11、S12、S13、S14、S15、S16、S17。Time 使用秒并按时间排序；FaultFlag 使用 0/1，必须存在但不作为预测特征。X/Y/H 的物理量纲为 m，Vx/Vy/Vz 为 m/s，FT 为 N，Roll/Pitch/Yaw 为 deg；S1～S9、S10_X/Y/Z、S11～S17 是状态或执行器量，单位按当前 Simulink 模型定义。模型内部按每 4 行抽样，seq_len=128、stride=64；这是当前原始采样约 0.031 秒时的模型处理规则，不应当把它当成所有数据的通用重采样规则。')
h('A.2 诊断与寿命输入对照',2)
table(['模块','可选输入','关键限制'],[
('状态监测','带时间列的 CSV 或实时会话','至少一个可绘制数值信号；异常值应先清理。'),('Hier14','Time、FaultFlag 和 29 个原始状态字段','列名必须匹配；派生 P 参数不能替代；窗口按模型契约处理。'),('健康评估','原始/派生数据，按算法选择','需要匹配正常参考；HI 未统一标定。'),('寿命预测','派生 P 参数、已有合法 HI，或可配对原始数据','至少 51 个 HI 窗口；部件模型和 PBS 必须一致。'),('实时告警','MATLAB/HTTP 会话样本','字段稳定、time 严格递增、数值有限。')])
h('A.3 MATLAB 上报字段建议',2)
table(['字段','类型','说明'],[
('time','有限标量数值','秒；同会话严格递增。'),('pressure / temperature','有限标量数值','示例信号；现场按实际字段替换。'),('bus_voltage / current 等','有限标量数值','字段名在会话内保持稳定。'),('FaultFlag','必须存在的 0/1 标签','用于窗口筛选和离线真值核对，不作为模型特征。')])

h('附录 B 2026-10-09 验证摘要',1)
p('以下信息用于说明当前版本的验证依据和使用边界，不构成对所有数据、型号和工况的性能承诺。')
table(['验证项','结果','解释'],[
('健康评估方向修正','platform_health 测试 18 项通过；真实 API 与浏览器验证通过','HI 改为相对正常参考的偏离度方向。'),('真实 Simulink 联调','泵气蚀、无故障、陀螺仪恒偏差三组任务完成','跨版本兼容加载；结果仍需独立验收。'),('Hier14 新仿真数据','3/3 文件成功；完整故障窗口均识别，但正常误报 19.70%','可说明接入和窗口识别样例，不能外推全部精度。'),('寿命适配','536/536 数据集模型 1 调用成功；15/15 模型在样例上成功','证明输入适配和调用链路，新增数据无真实 RUL 标签。'),('页面验收','1440/390 像素浏览器检查通过，无横向溢出和 JS 页面错误','覆盖下载、批量、详情、移动端视口。')])
p('正式工程验收前，仍需统一 MATLAB/模型版本、scikit-learn 依赖、采样策略和独立航次划分；控制类故障应补充独立飞行样本和阶段适用规则。')

h('附录 C 现场检查清单',1)
table(['阶段','检查项','完成'],[
('启动前','项目完整解压，manage.py、db.sqlite3、media、config 可见','□'),('启动前','Python/Node/MATLAB 版本和模型路径已记录','□'),('账号','管理员/查看用户已验证；权限符合岗位','□'),('数据','CSV 编码、时间列、单位、缺失值和字段契约已检查','□'),('采集','会话名称、Token、URL、time 单调递增已确认','□'),('告警','已选择同一会话并启用实时检测','□'),('诊断','已记录数据集、算法、窗口事件和聚合结果','□'),('健康','已记录正常参考来源、HI、裁剪比例和 PBS 关联','□'),('寿命','已确认模型编号、部件、参数、单位和 51 窗口条件','□'),('放行','授权人员已复核并签名；证据文件已归档','□'),('收尾','采集已结束；db.sqlite3、media、config 和日志已备份','□')])

h('附录 D 修订记录',1)
table(['版本','日期','修订内容'],[
('1.0','2026-09-26','基于离线交付版的基础安装、运行和 MATLAB 接入说明。'),('2.0','2026-10-10','按当前项目菜单和 2026-10-09 验证结果重编；补充健康评估方向修正、RUL 原始/派生配对、窗口告警事件、真实仿真联调、页面截图、输入契约、现场检查清单和结果边界。')])
p('本手册中的路径示例以 D:\\PHM\\phm_platform_offline 为例。实际部署时请替换为现场解压目录，并以平台页面和当前交付目录中的文件为准。')

# core properties / metadata
props=doc.core_properties; props.title='重复使用运载器健康管理平台软件使用手册'; props.subject='当前项目版本的安装、操作、数据契约与验证边界'; props.author='PHM Platform'; props.keywords='PHM,健康管理,故障诊断,寿命预测,使用手册'
# ensure all table cells fonts maybe
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(OUT)

