import requests
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

from flask import current_app
from app.models.dify_config import DifyConfig, DifyQuery
from app import db


class DifyService:
    """Dify API 服務"""

    # 預設設定
    DEFAULT_CONFIG = {
        "base_url": "http://192.168.1.106/v1",
        "api_key": "dataset-obp0C2PEAHHFLkfgOtBew6At",
        "dataset_id": "dfc37e09-510b-4464-9d92-89376a88a861",
        "search_method": "hybrid_search",
        "search_quality": "high",
        "embedding_model": "bge-m3:latest",
        "reranking_enable": True,
        "reranking_mode": "model",
        "semantic_weight": 1.0,
        "keyword_weight": 0.0,
        "top_k": 10,
        "score_threshold_enabled": False,
        "score_threshold": 0.0
    }

    def __init__(self, app=None):
        """初始化 Dify 服務，可傳入 Flask 應用實例"""
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.config = None

        # 如果有提供app，立即載入配置
        if app:
            self.load_config()

    def load_config(self) -> Optional[Dict]:
        """載入 Dify 配置，若無配置則創建預設配置"""
        try:
            if self.app:
                with self.app.app_context():
                    # 在應用上下文中查詢
                    config = DifyConfig.query.order_by(DifyConfig.id.desc()).first()

                    # 如果沒有找到配置，使用預設值創建一個
                    if not config:
                        self.logger.info("未找到 Dify 配置，創建預設配置")

                        # 創建預設配置
                        default_config = DifyConfig(
                            base_url=self.DEFAULT_CONFIG["base_url"],
                            api_key=self.DEFAULT_CONFIG["api_key"],
                            dataset_id=self.DEFAULT_CONFIG["dataset_id"],
                            search_method=self.DEFAULT_CONFIG["search_method"],
                            search_quality=self.DEFAULT_CONFIG["search_quality"],
                            embedding_model=self.DEFAULT_CONFIG["embedding_model"],
                            reranking_enable=self.DEFAULT_CONFIG["reranking_enable"],
                            reranking_mode=self.DEFAULT_CONFIG["reranking_mode"],
                            semantic_weight=self.DEFAULT_CONFIG["semantic_weight"],
                            keyword_weight=self.DEFAULT_CONFIG["keyword_weight"],
                            top_k=self.DEFAULT_CONFIG["top_k"],
                            score_threshold_enabled=self.DEFAULT_CONFIG["score_threshold_enabled"],
                            score_threshold=self.DEFAULT_CONFIG["score_threshold"]
                        )

                        try:
                            db.session.add(default_config)
                            db.session.commit()
                            config = default_config
                            self.logger.info("成功創建預設 Dify 配置")
                        except Exception as e:
                            db.session.rollback()
                            self.logger.error(f"創建預設配置時出錯: {str(e)}")

                    if config:
                        # 保存設定到對象，但不使用SQLAlchemy實例
                        self.config = {
                            "id": config.id,
                            "base_url": config.base_url,
                            "api_key": config.api_key,
                            "dataset_id": config.dataset_id,
                            "search_method": config.search_method,
                            "search_quality": config.search_quality,
                            "embedding_model": config.embedding_model,
                            "reranking_enable": config.reranking_enable,
                            "reranking_mode": config.reranking_mode,
                            "semantic_weight": config.semantic_weight,
                            "keyword_weight": config.keyword_weight,
                            "top_k": config.top_k,
                            "score_threshold_enabled": config.score_threshold_enabled,
                            "score_threshold": config.score_threshold
                        }
                        return self.config

            self.logger.warning("無法載入或創建 Dify 配置")
            return None
        except Exception as e:
            self.logger.error(f"載入 Dify 配置錯誤: {str(e)}")
            return None

    def search(self, query: str, user_id: Optional[int] = None) -> Tuple[bool, Optional[str], Optional[List[Dict]]]:
        """執行查詢操作

        Args:
            query: 查詢字串
            user_id: 使用者 ID（可選）

        Returns:
            Tuple[bool, Optional[str], Optional[List[Dict]]]:
                - 成功狀態
                - 錯誤訊息（如果有）
                - 結果列表（如果成功）
        """
        if not self.config:
            self.load_config()
            if not self.config:
                return False, "未找到有效的 Dify 配置", None

        # 構建請求
        try:
            url = f"{self.config['base_url']}/datasets/{self.config['dataset_id']}/retrieve"
            headers = {
                'Authorization': f'Bearer {self.config["api_key"]}',
                'Content-Type': 'application/json'
            }

            retrieval_model = {
                "search_method": self.config["search_method"],
                "search_quality": self.config["search_quality"],
                "embedding_model": self.config["embedding_model"],
                "reranking_enable": self.config["reranking_enable"],
                "reranking_mode": self.config["reranking_mode"],
                "weights": {
                    "semantic": self.config["semantic_weight"],
                    "keyword": self.config["keyword_weight"]
                },
                "top_k": self.config["top_k"],
                "score_threshold_enabled": self.config["score_threshold_enabled"],
                "score_threshold": self.config["score_threshold"]
            }

            payload = {
                "query": query,
                "retrieval_model": retrieval_model
            }

            self.logger.info(f"發送查詢請求: {query}")
            response = requests.post(url, headers=headers, json=payload, timeout=(10, 60))

            response_text = response.text

            if response.status_code == 200:
                response_data = response.json()

                # 處理結果
                results = self._process_results(response_data)

                # 按照分數從大到小排序
                results.sort(key=lambda x: x.get('score', 0), reverse=True)

                # 在應用上下文中保存記錄
                if self.app:
                    with self.app.app_context():
                        query_record = DifyQuery(
                            user_id=user_id,
                            query=query,
                            raw_response=response_text,
                            results_count=len(results),
                            success=True
                        )
                        db.session.add(query_record)
                        db.session.commit()

                return True, None, results
            else:
                error_msg = f"API 請求失敗，狀態碼: {response.status_code}, 響應: {response_text}"
                self.logger.error(error_msg)

                # 在應用上下文中保存記錄
                if self.app:
                    with self.app.app_context():
                        query_record = DifyQuery(
                            user_id=user_id,
                            query=query,
                            raw_response=response_text,
                            error_message=error_msg,
                            success=False
                        )
                        db.session.add(query_record)
                        db.session.commit()

                return False, f"查詢失敗: HTTP {response.status_code}", None

        except Exception as e:
            error_msg = f"執行查詢時發生錯誤: {str(e)}"
            self.logger.exception(error_msg)

            # 在應用上下文中保存記錄
            if self.app:
                with self.app.app_context():
                    query_record = DifyQuery(
                        user_id=user_id,
                        query=query,
                        error_message=error_msg,
                        success=False
                    )
                    db.session.add(query_record)
                    db.session.commit()

            return False, error_msg, None

    def _process_results(self, response_data: Dict) -> List[Dict]:
        """處理 API 回傳的結果，格式化為 FSC 編碼與說明

        Args:
            response_data: API 回傳的原始資料

        Returns:
            List[Dict]: 處理後的結果列表，包含 fsc_code 和 description
        """
        results = []

        # 檢查數據結構
        if not response_data:
            self.logger.warning("處理結果時收到空的響應數據")
            return results

        # 嘗試從 records[0]['child_chunks'] 獲取數據
        if 'records' in response_data and len(response_data['records']) > 0:
            record = response_data['records'][0]

            if 'child_chunks' in record:
                child_chunks = record['child_chunks']
                self.logger.info(f"找到 {len(child_chunks)} 個 child_chunks")

                # 處理每個 child_chunk
                for chunk in child_chunks:
                    content = chunk.get('content', '')

                    # 解析內容提取 FSC 編碼和說明
                    # 預期格式: "1234 說明文字..."
                    try:
                        if content and len(content) >= 4:
                            # 提取前4個字符作為FSC編碼
                            fsc_code = content[:4].strip()

                            # 確保FSC編碼是四位數字
                            if fsc_code.isdigit() and len(fsc_code) == 4:
                                # 提取剩餘部分作為說明
                                description = content[4:].strip()

                                result = {
                                    'fsc_code': fsc_code,
                                    'description': description,
                                    'original_content': content,
                                    'id': chunk.get('id', ''),
                                    'score': chunk.get('score', 0)
                                }
                                results.append(result)
                    except Exception as e:
                        self.logger.error(f"解析FSC格式時出錯: {str(e)}")
        else:
            self.logger.warning("響應中沒有有效的 records 或 child_chunks 數據")

        # 按FSC代碼排序
        results.sort(key=lambda x: x.get('fsc_code', ''))
        self.logger.info(f"最終處理後的FSC結果數量: {len(results)}")

        return results


    def test_settings(self, config: Dict) -> Tuple[bool, str, Dict]:
        """測試 Dify 設定

        Args:
            config: 要測試的設定

        Returns:
            Tuple[bool, str, Dict]:
                - 成功狀態
                - 訊息
                - 回應資料
        """
        try:
            # 建構測試用的請求
            url = f"{config['base_url']}/datasets/{config['dataset_id']}/retrieve"
            headers = {
                'Authorization': f'Bearer {config["api_key"]}',
                'Content-Type': 'application/json'
            }

            # 建立檢索模型設定
            retrieval_model = {
                "search_method": config.get('search_method', 'hybrid_search'),
                "search_quality": config.get('search_quality', 'high'),
                "embedding_model": config.get('embedding_model', 'bge-m3:latest'),
                "reranking_enable": config.get('reranking_enable', True),
                "reranking_mode": config.get('reranking_mode', 'model'),
                "weights": {
                    "semantic": config.get('semantic_weight', 1.0),
                    "keyword": config.get('keyword_weight', 0.0)
                },
                "top_k": config.get('top_k', 10),
                "score_threshold_enabled": config.get('score_threshold_enabled', False),
                "score_threshold": config.get('score_threshold', 0.0)
            }

            payload = {
                "query": "測試查詢",
                "retrieval_model": retrieval_model
            }

            # 發送測試請求
            self.logger.info("發送設定測試請求")
            response = requests.post(url, headers=headers, json=payload, timeout=(5, 30))

            response_data = {}
            try:
                response_data = response.json()
            except:
                response_data = {"raw_text": response.text}

            if response.status_code == 200:
                return True, "設定測試成功，API 連接正常", {"response": response_data}
            else:
                return False, f"設定測試失敗，API 返回狀態碼: {response.status_code}", {"response": response_data}

        except requests.exceptions.ConnectionError:
            return False, "連接錯誤: 無法連接到指定的 API 地址", {}
        except requests.exceptions.Timeout:
            return False, "請求超時: API 服務未在預期時間內回應", {}
        except Exception as e:
            self.logger.exception("設定測試時發生錯誤")
            return False, f"測試設定時發生錯誤: {str(e)}", {}

    def get_recent_queries(self, limit: int = 5) -> List[Dict]:
        """獲取最近的查詢記錄

        Args:
            limit: 返回記錄的最大數量

        Returns:
            List[Dict]: 查詢記錄列表
        """
        try:
            result = []
            if self.app:
                with self.app.app_context():
                    # 使用 db.session.query 而不是 DifyQuery.query
                    queries = db.session.query(DifyQuery).filter(
                        DifyQuery.success == True
                    ).order_by(
                        DifyQuery.created_at.desc()
                    ).limit(limit).all()

                    # 轉換為字典列表，避免使用SQLAlchemy實例
                    result = [{
                        'id': q.id,
                        'query': q.query,
                        'results_count': q.results_count,
                        'created_at': q.created_at
                    } for q in queries]
            return result
        except Exception as e:
            self.logger.error(f"獲取最近查詢記錄時出錯: {str(e)}")
            return []