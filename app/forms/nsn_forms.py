from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length

class NSNSearchForm(FlaskForm):
    """單一NSN查詢表單"""
    nsn = StringField('NSN編號或料號:', validators=[
        DataRequired(message='請輸入NSN編號或料號')
    ])
    submit = SubmitField('查詢')


class BatchNSNSearchForm(FlaskForm):
    """批量NSN查詢表單"""
    nsn_list = TextAreaField('NSN編號或料號清單:', validators=[
        Optional()  # 改為非必填，因為可以通過文件上傳
    ])
    file_upload = FileField('上傳檔案', validators=[
        Optional(),
        FileAllowed(['txt', 'csv'], '只允許上傳 .txt 或 .csv 文件')
    ])
    submit = SubmitField('批量查詢')