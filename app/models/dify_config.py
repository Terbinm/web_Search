from datetime import datetime
import json

from app import db


class DifyConfig(db.Model):
    """Dify API設定模型"""
    __tablename__ = 'dify_configs'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 基本設定
    base_url = db.Column(db.String(256), nullable=False, default="http://localhost/v1")
    api_key = db.Column(db.String(256), nullable=False)
    dataset_id = db.Column(db.String(128), nullable=False)

    # 檢索模型設定
    search_method = db.Column(db.String(64), default="hybrid_search")  # hybrid_search, semantic_search, keyword_search
    search_quality = db.Column(db.String(32), default="high")  # high, medium, low
    embedding_model = db.Column(db.String(128), default="bge-m3:latest")
    reranking_enable = db.Column(db.Boolean, default=True)
    reranking_mode = db.Column(db.String(32), default="model")  # model, custom

    # 搜索權重
    semantic_weight = db.Column(db.Float, default=1.0)
    keyword_weight = db.Column(db.Float, default=0.0)

    # 結果設定
    top_k = db.Column(db.Integer, default=10)
    score_threshold_enabled = db.Column(db.Boolean, default=False)
    score_threshold = db.Column(db.Float, default=0.0)

    # 存儲原始配置的JSON
    raw_config = db.Column(db.Text)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_raw_config()

    def update_raw_config(self):
        """根據當前字段生成原始配置JSON"""
        config = {
            "base_url": self.base_url,
            "api_key": self.api_key,
            "dataset_id": self.dataset_id,
            "retrieval_model": {
                "search_method": self.search_method,
                "search_quality": self.search_quality,
                "embedding_model": self.embedding_model,
                "reranking_enable": self.reranking_enable,
                "reranking_mode": self.reranking_mode,
                "weights": {
                    "semantic": self.semantic_weight,
                    "keyword": self.keyword_weight
                },
                "top_k": self.top_k,
                "score_threshold_enabled": self.score_threshold_enabled,
                "score_threshold": self.score_threshold
            }
        }
        self.raw_config = json.dumps(config, ensure_ascii=False)
        return config

    def to_dict(self):
        """轉換為字典格式"""
        return {
            "id": self.id,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "dataset_id": self.dataset_id,
            "search_method": self.search_method,
            "search_quality": self.search_quality,
            "embedding_model": self.embedding_model,
            "reranking_enable": self.reranking_enable,
            "reranking_mode": self.reranking_mode,
            "semantic_weight": self.semantic_weight,
            "keyword_weight": self.keyword_weight,
            "top_k": self.top_k,
            "score_threshold_enabled": self.score_threshold_enabled,
            "score_threshold": self.score_threshold,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    @classmethod
    def get_active_config(cls):
        """獲取當前啟用的配置（最新的）"""
        return cls.query.order_by(cls.id.desc()).first()

    def get_retrieval_config(self):
        """獲取用於API的retrieval_model配置部分"""
        return {
            "search_method": self.search_method,
            "search_quality": self.search_quality,
            "embedding_model": self.embedding_model,
            "reranking_enable": self.reranking_enable,
            "reranking_mode": self.reranking_mode,
            "weights": {
                "semantic": self.semantic_weight,
                "keyword": self.keyword_weight
            },
            "top_k": self.top_k,
            "score_threshold_enabled": self.score_threshold_enabled,
            "score_threshold": self.score_threshold
        }


class DifyQuery(db.Model):
    """Dify查詢歷史記錄模型"""
    __tablename__ = 'dify_queries'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    query = db.Column(db.Text, nullable=False)
    results_count = db.Column(db.Integer, default=0)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text, nullable=True)

    # 用於存儲搜索響應的原始JSON
    raw_response = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<DifyQuery {self.id}: {self.query[:20]}...>'