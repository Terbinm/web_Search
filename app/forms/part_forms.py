from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FileField, SelectField
from wtforms.validators import DataRequired, Optional, Length


class INCSearchForm(FlaskForm):
    """INC查詢表單"""
    inc = StringField('輸入INC:', validators=[
        DataRequired(message='請輸入INC')
    ])
    submit = SubmitField('提交')


class KeywordSearchForm(FlaskForm):
    """關鍵字料號查詢表單"""
    keyword = StringField('關鍵字:', validators=[
        DataRequired(message='請輸入關鍵字')
    ])
    submit = SubmitField('搜尋')


class BatchSearchForm(FlaskForm):
    """批次料號查詢表單"""
    part_numbers = TextAreaField('料號清單:', validators=[
        DataRequired(message='請輸入料號清單')
    ])
    file_upload = FileField('上傳檔案', validators=[Optional()])
    submit = SubmitField('上傳檔案')


class PartNumberSearchForm(FlaskForm):
    """料號清單查詢表單"""
    part_number = StringField('料號:', validators=[Optional()])
    submit = SubmitField('Filter')


class CreatePartForm(FlaskForm):
    """新增料號表單"""
    # 基本信息
    pn = StringField('料號', validators=[DataRequired(message='請輸入料號')])
    english_name = StringField('英文品名', validators=[DataRequired(message='請輸入英文品名')])
    chinese_name = StringField('中文品名', validators=[DataRequired(message='請輸入中文品名')])

    # 規格與單位
    unit_number = StringField('單位編號', validators=[Optional()])
    specification = StringField('規格', validators=[Optional()])
    packaging_quantity = StringField('包裝數量', validators=[Optional()])

    # 價格與來源
    price = StringField('美金價格', validators=[Optional()])
    specification_indicator = StringField('規格指示', validators=[Optional()], default='E')
    storage_quantity = StringField('儲位包裝量', validators=[Optional()])

    # 存儲相關
    storage_limitation = StringField('存儲限制', validators=[Optional()], default='00')
    storage_process = StringField('儲存過程', validators=[Optional()], default='00')
    consumability = StringField('耗材特性', validators=[Optional()], default='R')

    # 技術參數
    classification = StringField('消耗性特性', validators=[Optional()], default='U')
    storage_type = StringField('消耗性特型', validators=[Optional()], default='M')
    repair_capability = StringField('修理能量', validators=[Optional()])

    # 製造能力
    manufacturing_capability = StringField('製造能量', validators=[Optional()], default='E')
    source = StringField('來源代號', validators=[Optional()], default='5')
    category = StringField('系統代號', validators=[Optional()], default='5')

    # 其他分類
    system = StringField('廠別代號', validators=[Optional()], default='K')
    manufacturer = StringField('廠家', validators=[Optional()])
    reference_number = StringField('參考號碼/零件號碼', validators=[Optional()])

    # 採購相關
    pn_level = StringField('P/N獲得程度', validators=[Optional()])
    pn_source = StringField('P/N獲得來源', validators=[Optional()])
    ship_type = StringField('艦型', validators=[Optional()])

    # 識別信息
    cid_no = StringField('CID/NO.', validators=[Optional()])
    model = StringField('型式', validators=[Optional()])
    item_name = StringField('品名', validators=[Optional()])

    # 庫存信息
    quantity = StringField('數量', validators=[Optional()])
    location = StringField('位置', validators=[Optional()])
    fiig = StringField('FIIG', validators=[Optional()])

    # 其他信息
    notes = StringField('料號備用資訊', validators=[Optional()])

    # 提交按鈕
    submit = SubmitField('Create')