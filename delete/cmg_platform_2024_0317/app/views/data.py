import os
import json
import pandas as pd
import numpy as np
import uuid
import time
from flask import Blueprint, render_template, request, jsonify, send_file
from app import redis_engine
from app.config import TRAIN_DATA_PATH, TEST_DATA_PATH

# 全局变量
NEW_DATA_FLAG = 0
NEW_DATA = pd.array([])
NEW_DATA_FILENAME = ""

# 创建蓝图
data_bp = Blueprint('data', __name__)

# 生成UUID
def get_uuid(kw=""):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{kw}#%.7f"%time.time()))

# 数据管理页面
@data_bp.route('/data-manage', methods=['GET', 'POST'])
def data_manage():
    return render_template("data-manage.html")

# 初始化数据管理
@data_bp.route('/data-manage/init-all-data', methods=['GET', 'POST'])
def init_data_manage():
    # tableData为列表，其将每个数据信息以字典形式存储{'dataName','dataDescript','dataType','dataUuid'}
    tableData_raw = redis_engine.hget('cmg', 'dataInfo')
    if tableData_raw is None:
        tableData = []
    else:
        tableData = json.loads(tableData_raw)
    return jsonify(tableData)

# 更新数据
@data_bp.route('/data-manage/update', methods=['GET', 'POST'])
def dataUpdate():
    tableData = [{k: v for k, v in itm.items()
                  if k in ['dataName','dataDescript','dataType','dataUuid']} 
                 for itm in json.loads(request.form.get("tableData") or "[]")]
    check_data_delete(tableData)
    redis_engine.hset('cmg', 'dataInfo', json.dumps(tableData))
    return jsonify(None)

# 检查并删除无效数据
def check_data_delete(tableData):
    valid_filenames = {item['dataName'] for item in tableData}
    for file_name in os.listdir(TRAIN_DATA_PATH):
        if file_name not in valid_filenames:
            file_path = os.path.join(TRAIN_DATA_PATH, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file from training data: {file_path}")

    for file_name in os.listdir(TEST_DATA_PATH):
        if file_name not in valid_filenames:
            file_path = os.path.join(TEST_DATA_PATH, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file from test data: {file_path}")

# 添加新数据
@data_bp.route('/data-manage/add-new-data', methods=['GET', 'POST'])
def add_new_data():
    global NEW_DATA, NEW_DATA_FLAG, NEW_DATA_FILENAME
    tableData_raw = redis_engine.hget('cmg', 'dataInfo')
    if tableData_raw is None:
        tableData = []
    else:
        tableData = json.loads(tableData_raw)
    
    if NEW_DATA_FLAG == 1:
        newDataInfo = json.loads(request.form.get("newData") or "[]")

        newDataInfo['dataUuid'] = get_uuid(newDataInfo["dataName"])
        newDataInfo = {k: v for k, v in newDataInfo.items()
                        if k in ['dataName','dataDescript','dataType','dataUuid']} 
        tableData.append(newDataInfo)
        
        if newDataInfo['dataType'] == "训练数据":
            data_path = os.path.join(TRAIN_DATA_PATH, NEW_DATA_FILENAME)
        else:
            data_path = os.path.join(TEST_DATA_PATH, NEW_DATA_FILENAME)

        NEW_DATA.to_csv(data_path, index=False)
        
        redis_engine.hset('cmg', 'dataInfo', json.dumps(tableData))
        NEW_DATA_FLAG = 0
    return jsonify(tableData)

# 加载新数据
@data_bp.route('/data-manage/load-new-data', methods=['GET', 'POST'])
def load_new_data():
    global NEW_DATA, NEW_DATA_FLAG, NEW_DATA_FILENAME
    NEW_DATA_FLAG = 1
    file = request.files.get("file")
    NEW_DATA_FILENAME = file.filename
    NEW_DATA = pd.read_csv(file, encoding="gbk")
    return jsonify(None)

# 列出数据文件
@data_bp.route('/data-manage/list-files', methods=['GET'])
def list_files():
    train_files = os.listdir(TRAIN_DATA_PATH)
    test_files = os.listdir(TEST_DATA_PATH)
    return jsonify({
        "traindata": train_files,
        "testdata": test_files
    })

# 下载文件
@data_bp.route('/data-manage/download-file', methods=['POST'])
def download_file():
    file_path = request.json.get('filePath')
    if not file_path:
        return jsonify({"error": "文件路径不存在"}), 400
    
    abs_path = os.path.join(os.getcwd(), file_path)
    if not os.path.exists(abs_path):
        return jsonify({"error": "文件不存在"}), 400
    return send_file(abs_path, as_attachment=True)

# 数据查看页面
@data_bp.route('/data-view', methods=['GET'])
def data_view():
    file_name = request.args.get('file_name')
    data_type = request.args.get('data_type')
    
    if data_type == "训练数据":
        file_path = os.path.join(TRAIN_DATA_PATH, file_name)
    else:
        file_path = os.path.join(TEST_DATA_PATH, file_name)
        
    return render_template('data-view.html', file_name=file_name)

# 获取数据文件内容
@data_bp.route('/data-manage/get-file-data', methods=['GET'])
def get_file_data():
    file_name = request.args.get('file_name')
    data_type = request.args.get('data_type')
    
    if data_type == "训练数据":
        file_path = os.path.join(TRAIN_DATA_PATH, file_name)
    else:
        file_path = os.path.join(TEST_DATA_PATH, file_name)
    
    try:
        # 尝试不同的编码方式读取文件
        try:
            df = pd.read_csv(file_path, encoding='gbk')
        except:
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except:
                df = pd.read_csv(file_path)
        
        columns = df.columns.tolist()
        
        # 将时间列和数据转换为适合绘图的格式
        # 假设第一列是时间戳，不管它的名称是什么
        time_col = columns[0]  
        time_data = df[time_col].tolist()
        
        data_dict = {}
        # 需要排除的列名列表，同时支持"label"和"标签"
        exclude_columns = ['label', '标签', 'LABEL', 'Label']
        
        for col in columns[1:]:  # 跳过第一列时间戳
            # 排除label/标签列不传到前端
            if col not in exclude_columns:
                data_dict[col] = df[col].tolist()
            
        return jsonify({
            'success': True,
            'columns': [col for col in columns[1:] if col not in exclude_columns],
            'time_column': time_col,
            'time_data': time_data,
            'data': data_dict
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error processing file {file_path}: {error_detail}")
        return jsonify({
            'success': False,
            'error': str(e),
            'detail': error_detail
        }), 500
