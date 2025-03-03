from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
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

    # 註冊藍圖
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.part_routes import part_bp
    from app.routes.data_routes import data_bp
    from app.routes.nsn_routes import nsn_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(part_bp, url_prefix='/part')
    app.register_blueprint(nsn_bp, url_prefix='/nsn')
    app.register_blueprint(data_bp)

    # 註冊錯誤處理
    from app.errors.handlers import register_error_handlers
    register_error_handlers(app)

    return app


# 匯入模型，使其可被識別
from app.models.user import User
from app.models.part_number import PartNumber
from app.models.data_item import DataItem
from app.models.nsn import NSN