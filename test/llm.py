import os
import shutil
import psycopg2
import pandas as pd
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain.chains import RetrievalQA
import chromadb
import time
import random

# Ollama 服務設定
OLLAMA_HOST = "192.168.1.106"
OLLAMA_URL = f"http://{OLLAMA_HOST}:11434"
OLLAMA_MODEL = "phi4:14b"

# 資料庫連線資訊
DB_PARAMS = {
    "dbname": "sbir1",
    "user": "postgres",
    "password": "postgres",
    "host": "192.168.1.14",
    "port": "5433"
}

# SYSTEM_PROMPT (SQL 指令生成提示詞)
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


# 初始化 Ollama LLM 和 Embeddings
def initialize_ollama():
    try:
        ollama_llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_URL)
        ollama_embeddings = OllamaEmbeddings(base_url=OLLAMA_URL, model="bge-m3:latest")
        return ollama_llm, ollama_embeddings
    except Exception as e:
        print(f"初始化 Ollama 失敗: {e}")
        return None, None


# 初始化向量數據庫
def initialize_vectorstore(ollama_embeddings):
    try:
        # 檢查檔案是否存在
        data_file = r"file/finish.txt"
        if not os.path.isfile(data_file):
            print(f"錯誤：檔案 '{data_file}' 不存在或不是檔案。請確認檔案路徑是否正確。")
            return None

        # 載入 TXT 文件
        documents = []
        loader = TextLoader(data_file)
        documents.extend(loader.load())

        if not documents:
            print(f"錯誤：檔案 '{data_file}' 為空或無法讀取。")
            return None

        # 刪除舊的 ChromaDB 資料夾，避免維度衝突
        persist_directory = "./chroma_db_sql_keywords"
        shutil.rmtree(persist_directory, ignore_errors=True)

        # 建立向量資料庫 (ChromaDB)
        vectorstore = Chroma.from_documents(documents, embedding=ollama_embeddings, persist_directory=persist_directory)
        return vectorstore
    except Exception as e:
        print(f"初始化向量數據庫失敗: {e}")
        return None


# 根據 FSC 關鍵字搜尋相關 INC 代碼
def search_inc_by_fsc(fsc_pattern):
    query = """
    SELECT nm_cd_2303
    FROM "NM_CD_FSC_XREF-099"
    WHERE CONCAT(fsg_3994, fsc_wi_fsg_3996) LIKE %s
      AND nm_cd_2303 IS NOT NULL;
    """

    try:
        # 連線到 PostgreSQL
        conn = psycopg2.connect(**DB_PARAMS)
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
        print(f"FSC 搜尋錯誤: {e}")
        return []


# 搜尋並生成 SQL 指令的函數
def search_and_generate_sql(user_search_query, qa_chain, ollama_llm):
    """
    使用 RAG 搜尋 TXT 文件，並根據搜尋結果和 SYSTEM_PROMPT 生成 SQL 指令。
    """
    try:
        # 1. 使用 RAG 搜尋相關文件片段
        rag_result = qa_chain.invoke({"query": user_search_query})
        retrieved_context = rag_result['result']

        # 2. 將 RAG 結果放入 SYSTEM_PROMPT，生成最終 Prompt
        final_prompt = SYSTEM_PROMPT + retrieved_context + "\n\nONLY return a valid SQL query, no explanations."

        # 3. 使用 Ollama LLM 生成 SQL 指令
        sql_command = ollama_llm.invoke(final_prompt).strip()

        # 移除多餘的格式標記，例如 ```sql 或 ```
        sql_command = sql_command.replace("```sql", "").replace("```", "").strip()

        # 確保 SQL 指令有效
        if not sql_command.lower().startswith("select"):
            print("⚠️ LLM 生成的不是有效的 SQL 指令，請檢查 LLM 輸出。")
            print(f"\n🔍 LLM 回應內容:\n{sql_command}\n")
            return None

        return sql_command
    except Exception as e:
        print(f"生成 SQL 指令失敗: {e}")
        return None


# 執行整合後的 SQL 查詢（包含 FSC 搜尋的 INC 結果）
def execute_integrated_sql(sql_command, inc_codes, attempt=1, max_attempts=3):
    if sql_command is None:
        print("❌ SQL 指令無效，跳過執行。")
        return False

    if not inc_codes:
        print("❌ FSC 未找到相關 INC 代碼，跳過執行。")
        return False

    try:
        # 修改 SQL 查詢，將 FSC 搜尋的 INC 結果整合進去
        # 先從原始 SQL 中提取主要查詢部分
        parts = sql_command.lower().split("order by")
        main_query = parts[0]
        order_clause = f"ORDER BY {parts[1]}" if len(parts) > 1 else ""

        # 檢查是否已經有 WHERE 子句
        if "where" in main_query:
            # 在原有 WHERE 子句後面加上 AND nm_cd_2303 IN (...)
            inc_list = "', '".join(inc_codes)
            modified_sql = main_query + f" AND nm_cd_2303 IN ('{inc_list}') " + order_clause
        else:
            # 沒有 WHERE 子句則新增一個
            inc_list = "', '".join(inc_codes)
            modified_sql = main_query + f" WHERE nm_cd_2303 IN ('{inc_list}') " + order_clause

        # 執行修改後的 SQL 查詢
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cursor:
                cursor.execute(modified_sql)
                data = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]  # 取得實際的欄位名稱
                df = pd.DataFrame(data, columns=columns)  # 建立 DataFrame

                pd.set_option('display.max_rows', None)
                pd.set_option('display.max_colwidth', None)  # 顯示完整內容

                if df.empty:
                    print(f"\n📊 嘗試 {attempt}/{max_attempts}: 查詢結果為空，未找到同時匹配關鍵字和 FSC 的記錄。")
                    return False
                else:
                    print(f"\n📊 嘗試 {attempt}/{max_attempts}: 找到 {len(df)} 筆同時匹配關鍵字和 FSC 的記錄:")

                    # 只顯示 nm_cd_2303 和 shrt_nm_2301 兩列，且 shrt_nm_2301 靠左顯示
                    display_df = df[['nm_cd_2303', 'shrt_nm_2301']].copy()
                    # 確保 shrt_nm_2301 靠左顯示
                    pd.set_option('display.colheader_justify', 'left')
                    print(display_df.to_string(index=False, justify='left'))

                    return True

    except Exception as e:
        print(f"執行整合 SQL 查詢錯誤: {e}")
        return False


def main():
    # 初始化 Ollama
    print("🔄 初始化 Ollama LLM 和 Embeddings...")
    ollama_llm, ollama_embeddings = initialize_ollama()
    if ollama_llm is None or ollama_embeddings is None:
        print("初始化失敗，程式結束。")
        return

    # 初始化向量數據庫
    print("🔄 初始化向量數據庫...")
    vectorstore = initialize_vectorstore(ollama_embeddings)
    if vectorstore is None:
        print("向量數據庫初始化失敗，程式結束。")
        return

    # 建立 RetrievalQA 鏈 (用於 RAG 搜尋)
    qa_chain = RetrievalQA.from_chain_type(
        llm=ollama_llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 1})  # 限制返回結果數量
    )

    print("✅ 初始化完成，可以開始搜尋。")

    while True:
        print("\n" + "=" * 50)

        # 同時輸入 FSC 關鍵字和產品關鍵字
        print("請同時輸入 FSC 關鍵字和產品關鍵字 (輸入 'exit' 離開)")
        fsc_pattern = input("FSC : ")
        if fsc_pattern.lower() == 'exit':
            print("程式結束。")
            break

        keyword = input("關鍵字: ")
        if keyword.lower() == 'exit':
            print("程式結束。")
            break

        # 搜尋 FSC 相關的 INC 代碼
        print(f"🔍 正在搜尋 FSC 關鍵字 '{fsc_pattern}' 相關的 INC 代碼...")
        inc_codes = search_inc_by_fsc(fsc_pattern)

        if not inc_codes:
            print("❌ 未找到與 FSC 關鍵字相關的 INC 代碼，請嘗試其他關鍵字。")
            continue

        print(f"✅ 找到 FSC 相關 INC 代碼: {', '.join(inc_codes)}")

        # 嘗試最多3次搜索
        found_result = False
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            # 根據產品關鍵字生成 SQL 指令
            print(f"🔍 嘗試 {attempt}/{max_attempts}: 正在使用關鍵字 '{keyword}' 生成 SQL 指令...")

            # 如果不是第一次嘗試，稍微變化關鍵字順序或組合方式
            if attempt > 1:
                # 簡單的變化方式：在關鍵字前後加空格、改變單詞順序等
                keywords = keyword.split()
                if len(keywords) > 1:
                    random.shuffle(keywords)
                    modified_keyword = " ".join(keywords)
                else:
                    # 如果只有一個單詞，加一些空格或調整大小寫
                    modified_keyword = keyword.strip()
                    if random.choice([True, False]):
                        modified_keyword = modified_keyword.title()
                print(f"   調整關鍵字為: '{modified_keyword}'")
                sql_command = search_and_generate_sql(modified_keyword, qa_chain, ollama_llm)
            else:
                sql_command = search_and_generate_sql(keyword, qa_chain, ollama_llm)

            if sql_command is None:
                print(f"❌ 嘗試 {attempt}/{max_attempts}: 生成 SQL 指令失敗")
                time.sleep(1)  # 稍微等待一下再嘗試
                continue

            # 執行整合後的 SQL 查詢
            print(f"🔍 嘗試 {attempt}/{max_attempts}: 正在執行整合查詢，同時匹配 FSC 和產品關鍵字...")
            found_result = execute_integrated_sql(sql_command, inc_codes, attempt, max_attempts)

            if found_result:
                break  # 如果找到結果，跳出循環

            # 如果還沒找到結果且還有嘗試次數，稍微等待再試
            if attempt < max_attempts:
                time.sleep(1)

        # 如果三次嘗試都沒有找到結果，輸出77777
        if not found_result:
            print("\n77777")


if __name__ == "__main__":
    main()