from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Optional


class DataForm(FlaskForm):
    """資料表單類"""
    # 基本信息
    navy_part_number = StringField('料號')
    item_name_english = StringField('英文品名')
    item_name_chinese = StringField('中文品名')

    # 編號信息
    accounting_number = StringField('單位會計編號')
    item_code = StringField('品名代號')
    issuing_depart = StringField('撥發單位')

    # 價格與規格
    price_usd = FloatField('美金價格', validators=[Optional()])
    specification = SelectField('規格指示', choices=[
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
        ('Ｕ', 'Ｕ'), ('Ａ', 'Ａ'), ('Ｂ', 'Ｂ')
    ], default='Ｕ')
    consumability = SelectField('消耗性代號', choices=[
        ('M', 'M'), ('N', 'N'), ('X', 'X'), ('Y', 'Y')
    ], default='M')
    repair_capability = SelectField('修理能量', choices=[
        ('9', '9'), ('0', '0'), ('1', '1')
    ], default='0')

    # 能量與來源
    manufacturing_capability = SelectField('製造能量', choices=[
        ('Ｅ', 'Ｅ'), ('Ａ', 'Ａ'), ('Ｂ', 'Ｂ')
    ], default='Ｅ')
    source = SelectField('來源代號', choices=[
        ('5', '5'), ('C', 'C'), ('1', '1')
    ], default='C')
    system = SelectField('系統代號', choices=[
        ('5', '5'), ('C', 'C'), ('1', '1'), ('C35', 'C35')
    ], default='C35')
    category = SelectField('檔別代號', choices=[
        ('K', 'K'), ('V', 'V'), ('E', 'E'), ('C', 'C')
    ], default='C')

    # 其他信息
    Schedule_distinction = StringField('檔別區分')
    pn = StringField('參考號碼/零件號碼')
    ship_category = StringField('艦型')

    # 展開的更多欄位
    pn_acquisition_level = StringField('P/N獲得程度', default="2", validators=[Optional()])
    pn_acquisition_source = StringField('P/N獲得來源')
    configuration_identification_number = StringField('CID/NO.')
    part_model_id = StringField('型式')
    item_name1 = StringField('品名')
    installation_number = IntegerField('裝置數', validators=[Optional()])
    location = StringField('位置')
    federal_item_identification_guide = StringField('FIIG')

    # 根據Excel表格新增的欄位
    control_number = StringField('管制編號')
    control_category = StringField('管制區分')
    manager_department = StringField('主管處')
    price_certification = StringField('單價簽證')
    vendor_code = StringField('廠家代號')
    specification_description = TextAreaField('規格說明')