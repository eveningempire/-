import json
from flask import Blueprint, render_template, request, jsonify
from app import redis_engine
from lib.algoModule.detectAlgo.ml.algoChoose import Model as mlModel
from lib.algoModule.detectAlgo.rule.RuleDetector import ruleConvertor

# 创建蓝图
ml_rule_bp = Blueprint('ml_rule', __name__)

# 全局变量
ALGOS_NAMES = {algoitm["key"]: algoitm["zh_name"] for algoitm in mlModel.get_algos()}

@ml_rule_bp.route('/ml-edit', methods=['GET', 'POST'])
def ml_edit():
    return render_template('ml-edit.html')

@ml_rule_bp.route('/ml-edit/get-config', methods=['GET', 'POST'])
def ml_edit_get_config():
    paraNames = {}  # key为parameter name， value为parameter name
    tableData = json.loads(redis_engine.hget('cmg', 'dataInfo') or "[]")
    return jsonify({
        "algoNames": ALGOS_NAMES,
        "paraNames": paraNames,
        "dataInfo": tableData
    })

@ml_rule_bp.route('/ml-edit/init-all-ml', methods=['GET', 'POST'])
def ml_edit_init_all_ml():
    tableData = json.loads(redis_engine.hget('cmg', "ml-edit-config") or "[]")
    return jsonify(tableData)

@ml_rule_bp.route('/rule-edit', methods=['GET', 'POST'])
def rule_edit_init():
    return render_template("rule-edit.html")

@ml_rule_bp.route('/rule-edit/get-config', methods=['GET', 'POST'])
def rule_edit_get_config():
    obj = 'cmg'
    faultNames = json.loads(redis_engine.hget(obj, "fault-name-config") or "{}")
    
    pnames = json.loads(redis_engine.hget(obj, "pnames") or "[]")
    pnames = {p:p for p in pnames}
    components = json.loads(redis_engine.hget(obj, "components") or "[]")
    components = {comp:comp for comp in components}

    return jsonify({"faultNames": faultNames, "components": components,
                    "pnames": pnames, "sources":{"专家意见":"专家意见","数据驱动挖掘":"数据驱动挖掘"}})

@ml_rule_bp.route('/rule-edit/init-all-rule', methods=['GET', 'POST'])
def rule_edit_init_all_rule():
    obj = 'cmg'
    tableData = json.loads(redis_engine.hget(obj, "rule-edit-config") or "[]")
    return jsonify(tableData)

@ml_rule_bp.route('/rule-edit/config-rule', methods=['GET', 'POST'])
def rule_edit_config_all_rule():
    obj = 'cmg'
    tableData = request.form.get("tableData")
    
    pnames = json.loads(redis_engine.hget(obj, "pnames") or "[]")
    
    onlineRules, _ = ruleConvertor(pnames)._config_rule(json.loads(tableData))
    redis_engine.hset(obj, "rule-edit-config", tableData)
    redis_engine.hset(obj, "rule-config", onlineRules)
    return jsonify(None)
