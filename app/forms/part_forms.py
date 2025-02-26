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
        Optional()  # 改為非必填
    ])
    file_upload = FileField('上傳檔案', validators=[Optional()])
    submit = SubmitField('提交查詢')  # 更新按鈕文字


class PartNumberSearchForm(FlaskForm):
    """料號清單查詢表單"""
    part_number = StringField('料號:', validators=[Optional()])
    submit = SubmitField('Filter')


from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, SelectField
from wtforms.validators import DataRequired, Optional, Length

class CreatePartForm(FlaskForm):
    """新增料號表單"""
    # 基本信息
    pn = StringField('料號', validators=[DataRequired(message='請輸入料號')])
    english_name = StringField('英文品名', validators=[DataRequired(message='請輸入英文品名')])
    chinese_name = StringField('中文品名', validators=[DataRequired(message='請輸入中文品名')])

    # 編號信息
    accounting_number = StringField('單位會計編號', validators=[Optional()])
    item_code = StringField('品名代號', validators=[Optional()])
    issuing_department = StringField('撥發單位', validators=[Optional()])

    # 價格與規格
    price_usd = StringField('美金單價', validators=[Optional()])
    specification_indicator = SelectField('規格指示', choices=[
        ('E', 'E'), ('A', 'A'), ('B', 'B'),
        ('C', 'C'), ('D', 'D'), ('F', 'F'), ('N', 'N')
    ], default='E')
    packaging_quantity = SelectField('單位包裝量', choices=[
        ('0', '0'), ('1', '1'), ('2', '2')
    ], default='0')

    # 存儲相關
    storage_life = SelectField('存儲壽限', choices=[
        ('00', '00'), ('A', 'A'), ('B', 'B')
    ], default='00')
    storage_process = SelectField('壽限處理', choices=[
        ('00', '00'), ('ＣＯ', 'ＣＯ'), ('Ｃ－', 'Ｃ－')
    ], default='00')
    storage_type = SelectField('儲存型式', choices=[
        ('R', 'R'), ('A', 'A'), ('B', 'B')
    ], default='R')

    # 分類相關
    classification = SelectField('機密性代號', choices=[
        ('U', 'U'), ('A', 'A'), ('B', 'B')
    ], default='U')
    consumability = SelectField('消耗性代號', choices=[
        ('M', 'M'), ('N', 'N'), ('X', 'X'), ('Y', 'Y')
    ], default='M')
    repair_capability = SelectField('修理能量', choices=[
        ('9', '9'), ('0', '0'), ('1', '1')
    ], default='9')

    # 能量與來源
    manufacturing_capability = SelectField('製造能量', choices=[
        ('E', 'E'), ('A', 'A'), ('B', 'B')
    ], default='E')
    source = SelectField('來源代碼', choices=[
        ('5', '5'), ('C', 'C'), ('1', '1')
    ], default='5')
    system = SelectField('系統代號', choices=[
        ('5', '5'), ('C', 'C'), ('1', '1')
    ], default='5')
    category = SelectField('檔別代號', choices=[
        ('K', 'K'), ('V', 'V'), ('E', 'E')
    ], default='K')

    Schedule_distinction = StringField('檔別區分', validators=[Optional()])
    professional_category = StringField('專業代號', validators=[Optional()])
    special_parts = StringField('特種配件', validators=[Optional()])

    # 管制信息
    control_category = StringField('管制區分', validators=[Optional()])
    price_certification = StringField('單價簽證', validators=[Optional()])
    control_number = StringField('管制編號', validators=[Optional()])
    manager_department = StringField('主管處', validators=[Optional()])

    # 廠-家信息
    vendor_code = StringField('廠家代號', validators=[Optional()])
    reference_number = StringField('參考號碼(P/N)', validators=[Optional()])

    # PN相關
    pn_acquisition_level = StringField('P/N獲得程度', validators=[Optional()])
    pn_acquisition_source = StringField('P/N獲得來源', validators=[Optional()])
    ship_category = StringField('艦型', validators=[Optional()])

    # 規格與技術信息
    specification_description = TextAreaField('規格說明', validators=[Optional()])
    configuration_id = StringField('CID/NO.', validators=[Optional()])
    model_id = StringField('型式', validators=[Optional()])
    item_name = StringField('品名', validators=[Optional()])
    installation_number = StringField('裝置數', validators=[Optional()])
    location = StringField('位置', validators=[Optional()])

    # 申請相關
    application_unit = StringField('申請單位及電話', validators=[Optional()])
    application_date = DateField('申請日期', format='%Y-%m-%d', validators=[Optional()])
    application_unit_signature = StringField('申請單位簽章', validators=[Optional()])
    review_unit_signature = StringField('審核單位簽章', validators=[Optional()])
    nc_file_unit_signature = StringField('NC建檔會辦單簽章', validators=[Optional()])

    # 提交按鈕
    submit = SubmitField('建立料號')