# 此檔案由自動腳本建立
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional


class WorkflowStartForm(FlaskForm):
    """工作流程開始表單"""
    submit = SubmitField('開始新的申編流程')


class Step1Form(FlaskForm):
    """步驟1: Dify搜索表單"""
    query = TextAreaField('查詢內容:', validators=[
        DataRequired(message='請輸入查詢內容')
    ])
    search = SubmitField('搜索FSC代碼')
    selectedValue = HiddenField('已選擇的FSC代碼')
    selectedDisplay = HiddenField('已選擇的FSC描述')
    next_step = SubmitField('下一步')


class Step2Form(FlaskForm):
    """步驟2: LLM搜索表單"""
    fsc = HiddenField('FSC代碼', validators=[
        DataRequired(message='FSC代碼缺失')
    ])
    keyword = StringField('關鍵字:', validators=[
        DataRequired(message='請輸入產品關鍵字')
    ])
    search = SubmitField('搜索料號')
    selectedResultId = HiddenField('已選擇的料號')
    selectedResultText = HiddenField('已選擇的料號名稱')
    next_step = SubmitField('下一步')


class Step3Form(FlaskForm):
    """步驟3: INC搜索表單"""
    inc = StringField('INC:', validators=[
        DataRequired(message='INC缺失')
    ])
    search = SubmitField('查詢INC')
    selectedValue = HiddenField('已選擇的INC')
    selectedDisplay = HiddenField('已選擇的INC資料')
    inc_not_found = HiddenField('INC未找到')
    next_step = SubmitField('下一步')


class Step4Form(FlaskForm):
    """步驟4: 料號建立表單"""
    # 基本信息
    pn = StringField('料號', validators=[DataRequired(message='請輸入料號')])
    english_name = StringField('英文品名', validators=[DataRequired(message='請輸入英文品名')])
    chinese_name = StringField('中文品名', validators=[DataRequired(message='請輸入中文品名')])

    # 編號信息
    accounting_number = StringField('單位會計編號', validators=[Optional()])
    item_code = StringField('品名代號', validators=[Optional()])
    issuing_department = SelectField('撥發單位', choices=[
        ('EA', 'EA'), ('SE', 'SE'), ('A', 'A'), ('AT', 'AT'), ('AY', 'AY'),
        ('BA', 'BA'), ('BE', 'BE'), ('BF', 'BF'), ('BG', 'BG')
    ], default='EA')
    price_usd = StringField('美金單價', validators=[Optional()])

    # 規格信息
    specification_indicator = SelectField('規格指示', choices=[
        ('E', 'E'), ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'),
        ('F', 'F'), ('N', 'N')
    ], default='E')
    packaging_quantity = SelectField('單位包裝量', choices=[
        ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')
    ], default='0')
    storage_life = SelectField('存儲壽限', choices=[
        ('00', '00'), ('A', 'A'), ('B', 'B'), ('C', 'C')
    ], default='00')
    storage_process = SelectField('壽限處理', choices=[
        ('00', '00'), ('CO', 'CO'), ('C-', 'C-'), ('CT', 'CT')
    ], default='00')
    storage_type = SelectField('儲存型式', choices=[
        ('R', 'R'), ('A', 'A'), ('B', 'B'), ('C', 'C')
    ], default='R')

    # 分類信息
    classification = SelectField('機密性代號', choices=[
        ('U', 'U'), ('A', 'A'), ('B', 'B'), ('C', 'C')
    ], default='U')
    consumability = SelectField('消耗性代號', choices=[
        ('M', 'M'), ('N', 'N'), ('X', 'X'), ('Y', 'Y')
    ], default='M')
    repair_capability = SelectField('修理能量', choices=[
        ('9', '9'), ('0', '0'), ('1', '1'), ('2', '2')
    ], default='9')

    # 能量與來源
    manufacturing_capability = SelectField('製造能量', choices=[
        ('E', 'E'), ('A', 'A'), ('B', 'B'), ('C', 'C')
    ], default='E')
    source = SelectField('來源代碼', choices=[
        ('5', '5'), ('C', 'C'), ('1', '1'), ('2', '2')
    ], default='5')
    system = SelectField('系統代號', choices=[
        ('5', '5'), ('C', 'C'), ('1', '1')
    ], default='5')
    category = SelectField('檔別代號', choices=[
        ('K', 'K'), ('V', 'V'), ('E', 'E'), ('P', 'P')
    ], default='K')

    # 相關資料
    fsc_code = StringField('FSC代碼', validators=[Optional()])
    fsc_description = StringField('FSC描述', validators=[Optional()])
    specification_description = TextAreaField('規格說明', validators=[Optional()])

    next_step = SubmitField('創建料號')


class ResumeWorkflowForm(FlaskForm):
    """繼續工作流程表單"""
    workflow_id = HiddenField('流程ID', validators=[DataRequired()])
    submit = SubmitField('繼續上次未完成的流程')
    cancel = SubmitField('取消並開始新流程')