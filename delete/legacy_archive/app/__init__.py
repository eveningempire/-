import os
from flask import Flask, redirect
from lib.flaskModule.msfgModule.msfgApp import msfg_route_app
from lib.databaseModule.redisProcess import safeRedis as Redis

# 创建Redis实例
redis_engine = Redis()

def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__, 
                template_folder="../templates", 
                static_folder="../static", 
                static_url_path='/static')
    app.debug = False  # 关闭调试模式
    app.use_reloader = False  # 关闭自动重载
    
    # 配置Jinja2模板引擎
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.variable_start_string = '||<-EL PSY CONGROO->||'
    app.jinja_env.variable_end_string = '||<-EL PSY CONGROO->||'
    
    # 注册msfg路由
    msfg_route_app(app)
    
    # 注册蓝图
    from app.views.auth import auth_bp
    from app.views.data import data_bp
    from app.views.simulation import simulation_bp
    from app.views.prediction import prediction_bp
    from app.views.msfg import msfg_bp
    from app.views.ontime_test import ontime_test_bp
    from app.views.ml_rule import ml_rule_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(msfg_bp)
    app.register_blueprint(ontime_test_bp)
    app.register_blueprint(ml_rule_bp)
    
    # 注册首页路由
    @app.route('/')
    def index():
        return redirect('/login')
    
    return app
