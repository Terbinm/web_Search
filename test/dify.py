#!/usr/bin/env python3
import requests
import json
import os
import sys


def load_config():
    """從配置文件加載配置"""
    config_file = "config.json"
    config = {}

    # 默認配置
    default_config = {
        "base_url": "http://192.168.1.106/v1",
        "api_key": "dataset-obp0C2PEAHHFLkfgOtBew6At",
        "dataset_id": "5bd01088-75d7-4fca-b3c2-9549db5e7255",
        "query": "Capacitor, 2uF +\-5% 828v URMS電容器，2uF ±5% 828v URMS",
        "retrieval_model": {
            "search_method": "hybrid_search",
            "search_quality": "high",  # 高質量搜索模式
            "embedding_model": "bge-m3:latest",  # 使用的Embedding模型
            "reranking_enable": True,  # 啟用重排序
            "reranking_mode": "model",  # 使用模型進行重排序
            "reranking_model": {
                "reranking_provider_name": "",
                "reranking_model_name": ""
            },
            "weights": {
                "semantic": 1.0,  # 語義權重設為1.0
                "keyword": 0  # 關鍵詞權重設為0
            },
            "top_k": 10,
            "score_threshold_enabled": False,
            "score_threshold": 0
        }
    }

    # 嘗試從配置文件加載
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # 合併配置（這裡採用簡單方式，只處理頂層和retrieval_model層）
                for key, value in user_config.items():
                    if key == "retrieval_model" and isinstance(value, dict):
                        # 對於retrieval_model，深度合併
                        for rm_key, rm_value in value.items():
                            if rm_key == "reranking_model" and isinstance(rm_value, dict) and "reranking_model" in \
                                    default_config["retrieval_model"]:
                                for rrm_key, rrm_value in rm_value.items():
                                    default_config["retrieval_model"]["reranking_model"][rrm_key] = rrm_value
                            else:
                                default_config["retrieval_model"][rm_key] = rm_value
                    else:
                        default_config[key] = value

                print(f"從 {config_file} 加載了配置")
        except Exception as e:
            print(f"讀取配置文件時出錯: {e}")
            print("使用默認配置")
    else:
        print(f"配置文件 {config_file} 不存在，使用默認配置")

    # 從環境變量覆蓋某些設置
    if os.environ.get("API_KEY"):
        default_config["api_key"] = os.environ.get("API_KEY")
    if os.environ.get("DATASET_ID"):
        default_config["dataset_id"] = os.environ.get("DATASET_ID")

    return default_config


def retrieve_dataset(config):
    """發送POST請求到數據集檢索API"""
    # 檢查必要的配置
    if not config["api_key"]:
        print("錯誤: 未設置API密鑰。請在配置文件中設置或通過環境變量API_KEY提供。")
        return False

    if not config["dataset_id"]:
        print("錯誤: 未設置數據集ID。請在配置文件中設置或通過環境變量DATASET_ID提供。")
        return False

    # 構建URL和請求頭
    url = f"{config['base_url']}/datasets/{config['dataset_id']}/retrieve"
    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Content-Type': 'application/json'
    }

    # 構建請求體
    payload = {
        "query": config["query"],
        "retrieval_model": config["retrieval_model"]
    }

    print("發送請求...")
    print(f"URL: {url}")
    print(f"請求頭: {json.dumps(headers, indent=2)}")
    print(f"請求體: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=payload)

        print(f"\n響應狀態碼: {response.status_code}")

        if response.status_code == 200:
            try:
                response_json = response.json()
                print("響應內容:")
                print(json.dumps(response_json, indent=2, ensure_ascii=False))
                return True
            except json.JSONDecodeError:
                print("無法解析JSON響應")
                print("原始響應內容:")
                print(response.text)
                return False
        else:
            print(f"請求失敗，狀態碼: {response.status_code}")
            print("響應內容:")
            print(response.text)
            return False

    except requests.exceptions.RequestException as e:
        print(f"請求錯誤: {e}")
        return False


def main():
    # 加載配置
    config = load_config()

    # 執行API調用
    success = retrieve_dataset(config)

    # 根據結果設置退出碼
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()