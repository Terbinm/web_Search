from app import db
from datetime import datetime


class PartNumber(db.Model):
    """料號模型"""
    __tablename__ = 'part_numbers'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 基本信息
    part_number = db.Column(db.String(64), index=True)  # 料號
    name_english = db.Column(db.String(128))  # 英文品名
    name_chinese = db.Column(db.String(128))  # 中文品名

    # 編號信息
    accounting_number = db.Column(db.String(64))  # 單位會計編號
    item_code = db.Column(db.String(64))  # 品名代號
    issuing_department = db.Column(db.String(64))  # 撥發單位

    # 價格與規格
    price_usd = db.Column(db.Float)  # 美金單價
    specification_indicator = db.Column(db.String(8))  # 規格指示
    packaging_quantity = db.Column(db.String(8))  # 單位包裝量

    # 存儲相關
    storage_life = db.Column(db.String(8))  # 存儲壽限
    storage_process = db.Column(db.String(8))  # 壽限處理
    storage_type = db.Column(db.String(8))  # 儲存型式

    # 分類相關
    classification = db.Column(db.String(8))  # 機密性代號
    consumability = db.Column(db.String(8))  # 消耗性代號
    repair_capability = db.Column(db.String(8))  # 修理能量

    # 能量與來源
    manufacturing_capability = db.Column(db.String(8))  # 製造能量
    source = db.Column(db.String(8))  # 來源代碼
    system = db.Column(db.String(8))  # 系統代號
    category = db.Column(db.String(8))  # 檔別代號

    Schedule_distinction = db.Column(db.String(64))  # 檔別區分
    professional_category = db.Column(db.String(8))  # 專業代號
    special_parts = db.Column(db.String(64))  # 特種配件

    # 管制信息
    control_category = db.Column(db.String(64))  # 管制區分
    price_certification = db.Column(db.String(64))  # 單價簽證
    control_number = db.Column(db.String(64))  # 管制編號
    manager_department = db.Column(db.String(64))  # 主管處

    # 廠-家信息
    vendor_code = db.Column(db.String(64))  # 廠-家代號
    reference_number = db.Column(db.String(64))  # 參考號碼(P/N)

    # PN相關
    pn_acquisition_level = db.Column(db.String(64))  # P/N獲得程度
    pn_acquisition_source = db.Column(db.String(64))  # P/N獲得來源
    ship_category = db.Column(db.String(64))  # 艦型

    # 規格與技術信息
    specification_description = db.Column(db.Text)  # 規格說明
    configuration_id = db.Column(db.String(64))  # CID/NO.
    model_id = db.Column(db.String(64))  # 型式
    item_name = db.Column(db.String(128))  # 品名
    installation_number = db.Column(db.Integer)  # 裝置數
    location = db.Column(db.String(64))  # 位置

    # 申請相關
    application_unit = db.Column(db.String(128))  # 申請單位及電話
    application_date = db.Column(db.Date)  # 申請日期
    application_unit_signature = db.Column(db.String(64))  # 申請單位簽章
    review_unit_signature = db.Column(db.String(64))  # 審核單位簽章
    nc_file_unit_signature = db.Column(db.String(64))  # NC建檔會辦單簽章

    def __repr__(self):
        return f'<PartNumber {self.id}: {self.part_number}>'