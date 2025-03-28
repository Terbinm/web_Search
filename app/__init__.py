from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect


from app.config import Config

# 初始化擴展套件
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# 設定登入視圖和訊息
login_manager.login_view = 'auth.login'
login_manager.login_message = '請先登入呦 ~~~ (ˊuˋ) ~~~'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化擴展套件
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # 添加全局上下文處理器
    @app.before_request
    def load_active_workflow():
        """在每個請求前檢查用戶是否有進行中的流程"""
        if current_user.is_authenticated:
            from app.models.workflow import WorkflowInstance
            g.active_workflow = WorkflowInstance.get_active_workflow_for_user(current_user.id)
        else:
            g.active_workflow = None

    # 註冊藍圖
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.part_routes import part_bp
    from app.routes.data_routes import data_bp
    from app.routes.nsn_routes import nsn_bp
    from app.routes.dify_routes import dify_bp
    from app.routes.llm_routes import llm_bp
    from app.routes.workflow_routes import workflow_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(part_bp, url_prefix='/part')
    app.register_blueprint(nsn_bp, url_prefix='/nsn')
    app.register_blueprint(dify_bp, url_prefix='/dify')
    app.register_blueprint(llm_bp, url_prefix='/llm')
    app.register_blueprint(data_bp)
    app.register_blueprint(workflow_bp)

    # 註冊錯誤處理
    from app.errors.handlers import register_error_handlers
    register_error_handlers(app)

    return app


# 匯入模型，使其可被識別
from app.models.user import User
from app.models.part_number import PartNumber
from app.models.data_item import DataItem
from app.models.nsn import NSN
from app.models.dify_config import DifyConfig, DifyQuery
from app.models.llm_config import LLMConfig, LLMQuery
from app.models.workflow import WorkflowInstance

# 確保utils目錄存在
import os
utils_dir = os.path.join(os.path.dirname(__file__), 'utils')
if not os.path.exists(utils_dir):
    os.makedirs(utils_dir)
    # 創建__init__.py文件
    with open(os.path.join(utils_dir, '__init__.py'), 'w') as f:
        f.write('# 初始化utils包\n')

# 確保static/templates目錄存在
templates_dir = os.path.join(os.path.dirname(__file__), 'static', 'templates')
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)