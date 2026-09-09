from flask import Blueprint, render_template, request, jsonify
from app import redis_engine

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

# 登录页面
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")

# 基础页面
@auth_bp.route('/base-site', methods=['GET', 'POST'])
def basesite():
    return render_template("base-site.html")

# 用户登录验证
@auth_bp.route('/login/get-user', methods=['POST'])
def get_user():
    res = redis_engine.checkUser(request.form.get("usrname"), request.form.get("pwd"))
    return jsonify(res)

# 用户注册
@auth_bp.route('/login/register-user', methods=['POST'])
def register_user():
    res = redis_engine.registerUser(request.form.get("usrname"), request.form.get("pwd"), request.form.get("pwd2")) 
    return jsonify(res)
