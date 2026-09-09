# -*- coding: utf-8 -*-
import json
import os
# 定义 infoData 数组
infoData = [
    {"baseinfo": "生产厂家", "attribute": "中国航天运载火箭技术研究院"},
    {"baseinfo": "生产时间", "attribute": "2018年1月1日"},
    {"baseinfo": "产品代号", "attribute": "PBSFA002"},
    {"baseinfo": "产品编号", "attribute": "1204967294"},
    {"baseinfo": "产品名称", "attribute": "执行机构"},
    {"baseinfo": "产品描述", "attribute": "执行机构"},
    {"baseinfo": "重量", "attribute": "3.0 kg"},
    {"baseinfo": "功耗", "attribute": "1000.0 W"},
    {"baseinfo": "工作电压", "attribute": "220.0 V"},
    {"baseinfo": "工作电流", "attribute": "5.0 A"},
    {"baseinfo": "工作环境", "attribute": "默认"},
    {"baseinfo": "研制阶段", "attribute": "默认"},
    {"baseinfo": "舱位", "attribute": "默认"},
    {"baseinfo": "占位", "attribute": "默认"}
]

# 提取产品代号
product_code = None
for item in infoData:
    if item["baseinfo"] == "产品代号":
        product_code = item["attribute"]
        break
if product_code:
    # 使用产品代号作为文件名
    file_name = f"{product_code}.json"
    file_path = os.path.join('E:/health2/assessment/backend/nodeinfo/nodebaseinfo/', file_name)  # 修改为你实际的路径

    # 将数据写入指定路径的 JSON 文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(infoData, f, ensure_ascii=False, indent=4)
        print(f"数据已成功写入到 {file_path}")
    except Exception as e:
        print(f"写入文件失败: {e}")
else:
    print("未找到产品代号，无法设置文件名")
