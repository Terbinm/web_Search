import os
import json
import logging
import threading
import time
import random
import shutil
from typing import Dict, List, Any, Optional, Tuple, Union
import psycopg2
import pandas as pd

from flask import current_app
from app import db
from app.models.llm_config import LLMConfig, LLMQuery

# 直接整合llm.py的依賴
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain.chains import RetrievalQA
import chromadb


class LLMService:
    """LLM 服務 - 整合llm.py功能"""

    # 預設設定與llm.py保持一致
    DEFAULT_CONFIG = {
        "ollama_host": "192.168.1.106",
        "ollama_port": "11434",
        "ollama_model": "phi4:14b",
        "embedding_model": "bge-m3:latest",
        "db_host": "192.168.1.14",
        "db_port": "5433",
        "db_name": "sbir1",
        "db_user": "postgres",
        "db_password": "postgres",
        "max_attempts": 3
    }

    # 系統提示詞 - 與llm.py中的SYSTEM_PROMPT一致
    SYSTEM_PROMPT = """I have a data table called sbir1.public.real_final, with columns like:
SHRT_NM_2301 -> product title
NM_CD_2303 -> product code
ITM_NM_DEF_5015 -> description about this product

I will provide search prompts below. Please generate SQL queries using **only the exact search terms provided**, combining them in different order variations for better matching. **Do not expand keywords beyond those given.**

- **Only select product code (NM_CD_2303), product title (SHRT_NM_2301), and description (ITM_NM_DEF_5015).**  
- **Exclude results where product code (NM_CD_2303) is NULL or empty.**  
- **Remove duplicate product codes.**  
- **Ensure ORDER BY expressions appear in SELECT DISTINCT to prevent SQL errors.**  
a
ONLY SQL COMMAND OUTPUT  
ONLY VALID SQL COMMAND  
SELECT DISTINCT, ORDER BY expressions must appear in select list  

### Example:

```sql
SELECT DISTINCT
  nm_cd_2303,  shrt_nm_2301,  itm_nm_def_5015,
  CASE
    WHEN shrt_nm_2301 ILIKE '%XXX%' THEN 1
    WHEN itm_nm_def_5015 ILIKE '%XXX%' THEN 2
    WHEN shrt_nm_2301 ILIKE '%XXX%YYY%' THEN 3
    WHEN itm_nm_def_5015 ILIKE '%XXX%YYY%' THEN 4
    ELSE 99
  END AS relevance
FROM sbir1.public.real_final
WHERE nm_cd_2303 IS NOT NULL AND nm_cd_2303 <> ''
  AND (
    shrt_nm_2301 ILIKE '%XXX%'
    OR itm_nm_def_5015 ILIKE '%XXX%'
    OR shrt_nm_2301 ILIKE '%XXX%YYY%'
    OR itm_nm_def_5015 ILIKE '%XXX%YYY%'
  )
ORDER BY relevance, nm_cd_2303;
```
Search:
"""

    def __init__(self, app=None):
        """初始化 LLM 服務，可傳入 Flask 應用實例"""
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.config = None
        self.ollama_llm = None
        self.ollama_embeddings = None
        self.vectorstore = None
        self.qa_chain = None

        # 查詢任務字典
        self.tasks = {}

        # 如果有提供app，立即載入配置
        if app:
            self.load_config()

    def load_config(self) -> Optional[Dict]:
        """載入 LLM 配置，若無配置則創建預設配置"""
        try:
            if self.app:
                with self.app.app_context():
                    # 在應用上下文中查詢
                    config = LLMConfig.query.order_by(LLMConfig.id.desc()).first()

                    # 如果沒有找到配置，使用預設值創建一個
                    if not config:
                        self.logger.info("未找到 LLM 配置，創建預設配置")

                        # 創建預設配置
                        default_config = LLMConfig(
                            ollama_host=self.DEFAULT_CONFIG["ollama_host"],
                            ollama_port=self.DEFAULT_CONFIG["ollama_port"],
                            ollama_model=self.DEFAULT_CONFIG["ollama_model"],
                            embedding_model=self.DEFAULT_CONFIG["embedding_model"],
                            db_host=self.DEFAULT_CONFIG["db_host"],
                            db_port=self.DEFAULT_CONFIG["db_port"],
                            db_name=self.DEFAULT_CONFIG["db_name"],
                            db_user=self.DEFAULT_CONFIG["db_user"],
                            db_password=self.DEFAULT_CONFIG["db_password"],
                            max_attempts=self.DEFAULT_CONFIG["max_attempts"]
                        )

                        try:
                            db.session.add(default_config)
                            db.session.commit()
                            config = default_config
                            self.logger.info("成功創建預設 LLM 配置")
                        except Exception as e:
                            db.session.rollback()
                            self.logger.error(f"創建預設配置時出錯: {str(e)}")

                    if config:
                        # 保存設定到對象
                        self.config = config.to_dict()

                        # 初始化Ollama和向量數據庫
                        self._initialize_ollama()
                        self._initialize_vectorstore()

                        return self.config

            self.logger.warning("無法載入或創建 LLM 配置")
            return None
        except Exception as e:
            self.logger.error(f"載入 LLM 配置錯誤: {str(e)}")
            return None

    def _initialize_ollama(self):
        """初始化Ollama LLM和Embeddings"""
        try:
            ollama_url = f"http://{self.config['ollama_host']}:{self.config['ollama_port']}"
            self.ollama_llm = OllamaLLM(model=self.config['ollama_model'], base_url=ollama_url)
            self.ollama_embeddings = OllamaEmbeddings(base_url=ollama_url, model=self.config['embedding_model'])
            self.logger.info(f"成功初始化Ollama: {ollama_url}")
            return True
        except Exception as e:
            self.logger.error(f"初始化Ollama失敗: {str(e)}")
            return False

    def _initialize_vectorstore(self):
        """初始化向量數據庫"""
        try:
            # 使用唯一臨時目錄避免文件鎖定問題
            import uuid
            data_dir = os.path.join(current_app.instance_path, 'data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)

            data_file = os.path.join(data_dir, 'finish.txt')

            # 檢查數據文件是否存在，如果不存在則創建示例
            if not os.path.exists(data_file):
                with open(data_file, 'w', encoding='utf-8') as f:
                    f.write("Temperature Sensor\nPressure Gauge\nFlow Meter\nControl System\n")

            # 載入文本文件
            documents = []
            loader = TextLoader(data_file)
            documents.extend(loader.load())

            # 生成唯一ID作為向量庫目錄名稱
            unique_id = str(uuid.uuid4())
            persist_directory = os.path.join(current_app.instance_path, f'chroma_db_{unique_id}')

            # 創建新的向量數據庫
            self.vectorstore = Chroma.from_documents(
                documents,
                embedding=self.ollama_embeddings,
                persist_directory=persist_directory
            )

            # 創建檢索QA鏈
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.ollama_llm,
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 1})
            )

            return True
        except Exception as e:
            self.logger.error(f"初始化向量數據庫失敗: {str(e)}")
            return False

    def search_inc_by_fsc(self, fsc_pattern: str) -> List[str]:
        """根據FSC關鍵字搜索相關INC代碼 - 直接從llm.py移植"""
        query = """
        SELECT nm_cd_2303
        FROM "NM_CD_FSC_XREF-099"
        WHERE CONCAT(fsg_3994, fsc_wi_fsg_3996) LIKE %s
          AND nm_cd_2303 IS NOT NULL;
        """

        try:
            # 連線到PostgreSQL
            db_params = {
                "dbname": self.config["db_name"],
                "user": self.config["db_user"],
                "password": self.config["db_password"],
                "host": self.config["db_host"],
                "port": self.config["db_port"]
            }

            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()

            # 執行查詢
            cursor.execute(query, (f"%{fsc_pattern}%",))
            results = cursor.fetchall()

            # 只取第一個欄位的值
            codes = [row[0] for row in results]

            # 關閉連線
            cursor.close()
            conn.close()

            return codes
        except Exception as e:
            self.logger.error(f"FSC搜尋錯誤: {str(e)}")
            return []

    def search_and_generate_sql(self, user_search_query: str) -> Optional[str]:
        """使用RAG生成SQL查詢 - 直接從llm.py移植"""
        try:
            if not self.qa_chain or not self.ollama_llm:
                raise Exception("未初始化RAG鏈或LLM")

            # 使用RAG搜索相關文件片段
            rag_result = self.qa_chain.invoke({"query": user_search_query})
            retrieved_context = rag_result['result']

            # 將RAG結果放入SYSTEM_PROMPT，生成最終Prompt
            final_prompt = self.SYSTEM_PROMPT + retrieved_context + "\n\nONLY return a valid SQL query, no explanations."

            # 使用Ollama LLM生成SQL查詢
            sql_command = self.ollama_llm.invoke(final_prompt).strip()

            # 移除多餘的格式標記
            sql_command = sql_command.replace("```sql", "").replace("```", "").strip()

            # 確保SQL查詢有效
            if not sql_command.lower().startswith("select"):
                self.logger.warning(f"LLM生成的不是有效的SQL查詢: {sql_command}")
                return None

            return sql_command
        except Exception as e:
            self.logger.error(f"生成SQL查詢時出錯: {str(e)}")
            return None

    def execute_integrated_sql(self, sql_command: str, inc_codes: List[str]) -> Tuple[bool, List[Dict]]:
        """執行SQL查詢 - 直接從llm.py移植"""
        if sql_command is None:
            self.logger.error("SQL命令無效")
            return False, []

        if not inc_codes:
            self.logger.warning("FSC未找到相關INC代碼")
            return False, []

        try:
            # 修改SQL查詢，整合FSC搜索結果
            parts = sql_command.lower().split("order by")
            main_query = parts[0]
            order_clause = f"ORDER BY {parts[1]}" if len(parts) > 1 else ""

            # 檢查是否有WHERE子句
            if "where" in main_query:
                # 在原有WHERE子句後添加AND nm_cd_2303 IN (...)
                inc_list = "', '".join(inc_codes)
                modified_sql = main_query + f" AND nm_cd_2303 IN ('{inc_list}') " + order_clause
            else:
                # 添加新的WHERE子句
                inc_list = "', '".join(inc_codes)
                modified_sql = main_query + f" WHERE nm_cd_2303 IN ('{inc_list}') " + order_clause

            # 連接資料庫
            db_params = {
                "dbname": self.config["db_name"],
                "user": self.config["db_user"],
                "password": self.config["db_password"],
                "host": self.config["db_host"],
                "port": self.config["db_port"]
            }

            # 執行查詢
            with psycopg2.connect(**db_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(modified_sql)
                    data = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]

                    # 轉換為字典列表
                    results = []
                    for row in data:
                        result = {}
                        for i, col in enumerate(columns):
                            result[col] = row[i]
                        results.append(result)

                    return len(results) > 0, results

        except Exception as e:
            self.logger.error(f"執行SQL查詢時出錯: {str(e)}")
            return False, []

    def search(self, fsc: str, keyword: str, user_id: Optional[int] = None) -> int:
        """執行LLM查詢，返回查詢ID"""
        if not self.config:
            self.load_config()
            if not self.config:
                raise Exception("未找到有效的LLM配置")

        # 在應用上下文中建立查詢記錄
        query_id = None
        if self.app:
            with self.app.app_context():
                query_record = LLMQuery(
                    user_id=user_id,
                    fsc=fsc,
                    keyword=keyword,
                    status="pending"
                )
                db.session.add(query_record)
                db.session.commit()
                query_id = query_record.id

        # 啟動後台執行緒處理查詢
        if query_id:
            thread = threading.Thread(target=self._process_query, args=(query_id, fsc, keyword))
            thread.daemon = True
            thread.start()
            self.tasks[query_id] = {"thread": thread, "status": "pending"}

        return query_id

    def _process_query(self, query_id: int, fsc: str, keyword: str):
        """後台處理查詢 - 整合llm.py的主要邏輯"""
        if not self.app:
            return

        try:
            # 更新查詢狀態為處理中
            with self.app.app_context():
                query = LLMQuery.query.get(query_id)
                if query:
                    query.status = "processing"
                    db.session.commit()
                    self.tasks[query_id]["status"] = "processing"

            # 搜尋FSC相關的INC代碼
            self.logger.info(f"搜尋FSC關鍵字: {fsc}")
            inc_codes = self.search_inc_by_fsc(fsc)

            if not inc_codes:
                self.logger.warning(f"未找到與FSC關鍵字相關的INC代碼: {fsc}")
                with self.app.app_context():
                    query = LLMQuery.query.get(query_id)
                    if query:
                        query.code = "77777"
                        query.status = "completed"
                        db.session.commit()
                        self.tasks[query_id]["status"] = "completed"
                return

            self.logger.info(f"找到FSC相關INC代碼: {', '.join(inc_codes[:5])}...")

            # 嘗試最多max_attempts次搜索
            found_result = False
            results = []
            max_attempts = self.config["max_attempts"]

            for attempt in range(1, max_attempts + 1):
                # 根據產品關鍵字生成SQL命令
                self.logger.info(f"嘗試 {attempt}/{max_attempts}: 使用關鍵字 '{keyword}' 生成SQL命令")

                # 如果不是第一次嘗試，調整關鍵字
                if attempt > 1:
                    keywords = keyword.split()
                    if len(keywords) > 1:
                        random.shuffle(keywords)
                        modified_keyword = " ".join(keywords)
                    else:
                        modified_keyword = keyword.strip()
                        if random.choice([True, False]):
                            modified_keyword = modified_keyword.title()
                    self.logger.info(f"調整關鍵字為: '{modified_keyword}'")
                    sql_command = self.search_and_generate_sql(modified_keyword)
                else:
                    sql_command = self.search_and_generate_sql(keyword)

                if sql_command is None:
                    self.logger.warning(f"嘗試 {attempt}/{max_attempts}: 生成SQL命令失敗")
                    time.sleep(1)  # 稍微等待一下再嘗試
                    continue

                # 執行整合SQL查詢
                self.logger.info(f"嘗試 {attempt}/{max_attempts}: 執行查詢，同時匹配FSC和產品關鍵字")
                found_result, results = self.execute_integrated_sql(sql_command, inc_codes)

                if found_result:
                    self.logger.info(f"找到 {len(results)} 筆匹配記錄")
                    break

                # 如果還沒找到結果且還有嘗試次數，稍微等待再試
                if attempt < max_attempts:
                    time.sleep(1)

            # 更新查詢記錄
            with self.app.app_context():
                query = LLMQuery.query.get(query_id)
                if query:
                    if not found_result:
                        # 如果所有嘗試都沒找到結果，返回77777
                        query.code = "77777"
                        query.results_count = 0
                        self.logger.info("未找到結果，返回代碼77777")
                    else:
                        query.results_count = len(results)
                        query.raw_response = json.dumps(results, ensure_ascii=False)
                        self.logger.info(f"查詢成功，找到 {len(results)} 筆結果")

                    query.status = "completed"
                    db.session.commit()
                    self.tasks[query_id]["status"] = "completed"

        except Exception as e:
            self.logger.error(f"處理查詢時出錯: {str(e)}")
            # 更新查詢狀態為失敗
            with self.app.app_context():
                query = LLMQuery.query.get(query_id)
                if query:
                    query.status = "failed"
                    query.error_message = str(e)
                    db.session.commit()
                    self.tasks[query_id]["status"] = "failed"

    def get_query_status(self, query_id: int) -> Dict:
        """獲取查詢狀態"""
        if not self.app:
            return {"status": "unknown"}

        try:
            with self.app.app_context():
                query = LLMQuery.query.get(query_id)
                if query:
                    return {
                        "status": query.status,
                        "results_count": query.results_count,
                        "error_message": query.error_message
                    }
                return {"status": "unknown"}
        except Exception as e:
            self.logger.error(f"獲取查詢狀態時出錯: {str(e)}")
            return {"status": "unknown", "error": str(e)}

    def get_query_results(self, query_id: int) -> Dict:
        """獲取查詢結果"""
        if not self.app:
            return {"success": False, "error": "未初始化應用"}

        try:
            with self.app.app_context():
                query = LLMQuery.query.get(query_id)
                if not query:
                    return {"success": False, "error": "未找到查詢記錄"}

                if query.status != "completed":
                    return {"success": False, "status": query.status, "error": query.error_message}

                if query.code == "77777":
                    return {
                        "success": True,
                        "code": "77777",
                        "fsc": query.fsc,
                        "keyword": query.keyword,
                        "results": []
                    }

                results = []
                if query.raw_response:
                    try:
                        results = json.loads(query.raw_response)
                    except:
                        pass

                return {
                    "success": True,
                    "fsc": query.fsc,
                    "keyword": query.keyword,
                    "results": results,
                    "count": query.results_count
                }
        except Exception as e:
            self.logger.error(f"獲取查詢結果時出錯: {str(e)}")
            return {"success": False, "error": str(e)}

    def test_settings(self, config: Dict) -> Tuple[bool, str, Dict]:
        """測試LLM設定"""
        try:
            # 測試資料庫連接
            db_params = {
                "host": config["db_host"],
                "port": config["db_port"],
                "dbname": config["db_name"],
                "user": config["db_user"],
                "password": config["db_password"]
            }

            # 嘗試連接資料庫
            conn = psycopg2.connect(**db_params)
            conn.close()

            # 測試Ollama連接
            ollama_url = f"http://{config['ollama_host']}:{config['ollama_port']}"
            try:
                # 嘗試初始化Ollama
                ollama_llm = OllamaLLM(model=config['ollama_model'], base_url=ollama_url)
                ollama_embeddings = OllamaEmbeddings(base_url=ollama_url, model=config['embedding_model'])

                # 簡單測試以確保連接工作
                test_result = ollama_llm.invoke("Hello")

                return True, "設定測試成功，所有連接正常", {"response": "connection successful: " + test_result[:70] + "..."}
            except Exception as e:
                return False, f"Ollama連接測試失敗: {str(e)}", {}

        except psycopg2.Error as e:
            return False, f"資料庫連接測試失敗: {str(e)}", {}
        except Exception as e:
            self.logger.exception("設定測試時發生錯誤")
            return False, f"測試設定時發生錯誤: {str(e)}", {}

    def get_recent_queries(self, limit: int = 5) -> List[Dict]:
        """獲取最近的查詢記錄"""
        try:
            result = []
            if self.app:
                with self.app.app_context():
                    # 使用db.session.query而不是LLMQuery.query
                    queries = db.session.query(LLMQuery).filter(
                        LLMQuery.status == "completed"
                    ).order_by(
                        LLMQuery.created_at.desc()
                    ).limit(limit).all()

                    # 轉換為字典列表
                    result = [{
                        'id': q.id,
                        'fsc': q.fsc,
                        'keyword': q.keyword,
                        'results_count': q.results_count,
                        'created_at': q.created_at
                    } for q in queries]
            return result
        except Exception as e:
            self.logger.error(f"獲取最近查詢記錄時出錯: {str(e)}")
            return []