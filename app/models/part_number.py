from app import db
from datetime import datetime


class PartNumber(db.Model):
    """料號模型"""
    __tablename__ = 'part_numbers'  # 更正資料表名稱，符合命名慣例

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 基本信息 - 使用更一致的命名方式
    part_number = db.Column(db.String(64), index=True)  # 主料號欄位
    name_chinese = db.Column(db.String(128))  # 中文品名
    name_english = db.Column(db.String(128))  # 英文品名

    # 編號信息
    accounting_number = db.Column(db.String(64))  # 單位會計編號
    item_code = db.Column(db.String(64))  # 品名代號
    issuing_department = db.Column(db.String(64))  # 撥發單位

    # 價格與規格
    price_usd = db.Column(db.Float)  # 美金價格
    specification = db.Column(db.String(8))  # 規格指示
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
    source = db.Column(db.String(8))  # 來源代號
    system = db.Column(db.String(8))  # 系統代號
    category = db.Column(db.String(8))  # 檔別代號

    # 其他信息
    manufacturer = db.Column(db.String(64))  # 廠家代號
    reference_number = db.Column(db.String(64))  # 參考號碼/零件號碼
    ship_category = db.Column(db.String(64))  # 艦型

    # 展開的更多欄位
    pn_acquisition_level = db.Column(db.String(64))  # P/N獲得程度
    pn_acquisition_source = db.Column(db.String(64))  # P/N獲得來源
    configuration_id = db.Column(db.String(64))  # CID/NO.
    model_id = db.Column(db.String(64))  # 型式
    item_name = db.Column(db.String(128))  # 品名
    installation_number = db.Column(db.Integer)  # 裝置數
    location = db.Column(db.String(64))  # 位置
    fiig = db.Column(db.String(64))  # 聯邦物品識別指南

    def __repr__(self):
        return f'<PartNumber {self.id}: {self.part_number}>'