from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SubmitField, SelectField,
    BooleanField, FloatField, IntegerField, HiddenField
)
from wtforms.validators import DataRequired, Optional, NumberRange, URL, Length


class DifySearchForm(FlaskForm):
    """Dify查詢表單"""
    query = TextAreaField('查詢內容:', validators=[
        DataRequired(message='請輸入查詢內容')
    ])
    submit = SubmitField('查詢')


class DifySettingsForm(FlaskForm):
    """Dify設定表單"""
    # 基本設定
    base_url = StringField('API 基礎 URL', validators=[
        DataRequired(message='請輸入API基礎URL'),
        URL(message='請輸入有效的URL地址')
    ])

    api_key = StringField('API 密鑰', validators=[
        DataRequired(message='請輸入API密鑰'),
        Length(min=5, message='API密鑰長度不足')
    ])

    dataset_id = StringField('數據集 ID', validators=[
        DataRequired(message='請輸入數據集ID'),
        Length(min=5, message='數據集ID長度不足')
    ])

    # 檢索模型設定
    search_method = SelectField('搜索方法', choices=[
        ('hybrid_search', '混合搜索'),
        ('semantic_search', '語義搜索'),
        ('keyword_search', '關鍵詞搜索')
    ], default='hybrid_search')

    search_quality = SelectField('搜索質量', choices=[
        ('high', '高質量'),
        ('medium', '中等質量'),
        ('low', '低質量')
    ], default='high')

    embedding_model = StringField('Embedding 模型', validators=[
        DataRequired(message='請輸入Embedding模型名稱')
    ], default='bge-m3:latest')

    reranking_enable = BooleanField('啟用重排序', default=True)

    reranking_mode = SelectField('重排序模式', choices=[
        ('model', '模型重排序'),
        ('custom', '自定義重排序')
    ], default='model')

    # 搜索權重
    semantic_weight = FloatField('語義搜索權重', validators=[
        NumberRange(min=0, max=1, message='權重必須在0-1之間')
    ], default=1.0)

    keyword_weight = FloatField('關鍵詞搜索權重', validators=[
        NumberRange(min=0, max=1, message='權重必須在0-1之間')
    ], default=0.0)

    # 結果設定
    top_k = IntegerField('最大結果數量', validators=[
        NumberRange(min=1, max=50, message='結果數量必須在1-50之間')
    ], default=10)

    score_threshold_enabled = BooleanField('啟用分數閾值', default=False)

    score_threshold = FloatField('分數閾值', validators=[
        NumberRange(min=0, max=1, message='閾值必須在0-1之間')
    ], default=0.0)

    # 表單操作
    submit = SubmitField('保存')
    test = SubmitField('測試設定')