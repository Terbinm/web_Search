from datetime import datetime
import json

from app import db


class LLMConfig(db.Model):
    """LLM API設定模型 - 與llm.py參數保持一致"""
    __tablename__ = 'llm_configs'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Ollama設定 - 與llm.py中的常量保持一致
    ollama_host = db.Column(db.String(128), nullable=False, default="192.168.1.106")
    ollama_port = db.Column(db.String(32), nullable=False, default="11434")
    ollama_model = db.Column(db.String(64), nullable=False, default="phi4:14b")
    embedding_model = db.Column(db.String(64), nullable=False, default="bge-m3:latest")

    # 資料庫設定 - 與llm.py中的DB_PARAMS保持一致
    db_host = db.Column(db.String(128), nullable=False, default="192.168.1.14")
    db_port = db.Column(db.String(32), nullable=False, default="5433")
    db_name = db.Column(db.String(64), nullable=False, default="sbir1")
    db_user = db.Column(db.String(64), nullable=False, default="postgres")
    db_password = db.Column(db.String(64), nullable=False, default="postgres")

    # 搜索設定
    max_attempts = db.Column(db.Integer, default=3)

    # 存儲原始配置的JSON
    raw_config = db.Column(db.Text)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_raw_config()

    def update_raw_config(self):
        """根據當前字段生成原始配置JSON"""
        config = {
            "ollama": {
                "host": self.ollama_host,
                "port": self.ollama_port,
                "model": self.ollama_model,
                "embedding_model": self.embedding_model
            },
            "database": {
                "host": self.db_host,
                "port": self.db_port,
                "dbname": self.db_name,
                "user": self.db_user,
                "password": self.db_password
            },
            "search": {
                "max_attempts": self.max_attempts
            }
        }
        self.raw_config = json.dumps(config, ensure_ascii=False)
        return config

    def to_dict(self):
        """轉換為字典格式"""
        return {
            "id": self.id,
            "ollama_host": self.ollama_host,
            "ollama_port": self.ollama_port,
            "ollama_model": self.ollama_model,
            "embedding_model": self.embedding_model,
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "db_user": self.db_user,
            "db_password": self.db_password,
            "max_attempts": self.max_attempts,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    @classmethod
    def get_active_config(cls):
        """獲取當前啟用的配置（最新的）"""
        return cls.query.order_by(cls.id.desc()).first()

    def get_db_params(self):
        """獲取資料庫連接參數字典"""
        return {
            "dbname": self.db_name,
            "user": self.db_user,
            "password": self.db_password,
            "host": self.db_host,
            "port": self.db_port
        }


class LLMQuery(db.Model):
    """LLM查詢歷史記錄模型"""
    __tablename__ = 'llm_queries'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 查詢參數
    fsc = db.Column(db.String(64), nullable=False)
    keyword = db.Column(db.String(128), nullable=False)

    # 處理狀態
    status = db.Column(db.String(32), default="pending")  # pending, processing, completed, failed
    results_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)

    # 特殊狀態碼
    code = db.Column(db.String(16), nullable=True)  # 例如 77777

    # 用於存儲搜索響應的原始JSON
    raw_response = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<LLMQuery {self.id}: FSC={self.fsc}, Keyword={self.keyword}>'