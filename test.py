import os


def create_structure():
    """
    建立對話中提到的檔案和資料夾結構
    """
    # 基礎資料夾結構
    base_folders = [
        'app',
        'app/routes',
        'app/forms',
        'app/models',
        'app/services',
        'app/templates',
        'app/templates/llm'
    ]

    # 檔案清單
    files = [
        'app/routes/llm_routes.py',
        'app/forms/llm_forms.py',
        'app/models/llm_config.py',
        'app/services/llm_service.py',
        'app/templates/llm/llm_search.html',
        'app/templates/llm/llm_settings.html',
        'app/templates/llm/llm_results.html',
        'app/templates/llm/llm_loading.html'
    ]

    # 建立資料夾
    for folder in base_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f'已建立資料夾: {folder}')

    # 建立檔案 (空檔案)
    for file_path in files:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                pass  # 建立空檔案
            print(f'已建立檔案: {file_path}')


if __name__ == "__main__":
    print("開始建立檔案和資料夾結構...")
    create_structure()
    print("完成！")