from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SubmitField, IntegerField,
    BooleanField, HiddenField
)
from wtforms.validators import DataRequired, Optional, NumberRange


class LLMSearchForm(FlaskForm):
    """LLM查詢表單"""
    fsc = StringField('FSC 代碼:', validators=[
        DataRequired(message='請輸入FSC代碼')
    ])
    keyword = StringField('關鍵字:', validators=[
        DataRequired(message='請輸入產品關鍵字')
    ])
    submit = SubmitField('查詢')


class LLMSettingsForm(FlaskForm):
    """LLM設定表單 - 與llm.py參數保持一致"""
    # Ollama設定
    ollama_host = StringField('Ollama 主機地址', validators=[
        DataRequired(message='請輸入Ollama主機地址')
    ], default="192.168.1.106")

    ollama_port = StringField('Ollama 端口', validators=[
        DataRequired(message='請輸入Ollama端口')
    ], default="11434")

    ollama_model = StringField('LLM 模型', validators=[
        DataRequired(message='請輸入LLM模型名稱')
    ], default="phi4:14b")

    embedding_model = StringField('Embedding 模型', validators=[
        DataRequired(message='請輸入Embedding模型名稱')
    ], default="bge-m3:latest")

    # 資料庫設定 - 與llm.py中的DB_PARAMS保持一致
    db_host = StringField('資料庫主機', validators=[
        DataRequired(message='請輸入資料庫主機地址')
    ], default="192.168.1.14")

    db_port = StringField('資料庫端口', validators=[
        DataRequired(message='請輸入資料庫端口')
    ], default="5433")

    db_name = StringField('資料庫名稱', validators=[
        DataRequired(message='請輸入資料庫名稱')
    ], default="sbir1")

    db_user = StringField('資料庫用戶名', validators=[
        DataRequired(message='請輸入資料庫用戶名')
    ], default="postgres")

    db_password = StringField('資料庫密碼', validators=[
        DataRequired(message='請輸入資料庫密碼')
    ], default="postgres")

    # 搜索設定
    max_attempts = IntegerField('最大嘗試次數', validators=[
        NumberRange(min=1, max=10, message='嘗試次數必須在1-10之間')
    ], default=3)

    # 表單操作
    submit = SubmitField('保存')
    test = SubmitField('測試設定')