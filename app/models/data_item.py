from datetime import datetime
from app import db


class DataItem(db.Model):
    """資料項目模型"""
    __tablename__ = 'data_items'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 基本信息
    navy_part_number = db.Column(db.String(64), index=True)
    item_name_english = db.Column(db.String(128))
    item_name_chinese = db.Column(db.String(128))

    # 編號信息
    accounting_number = db.Column(db.String(64))
    item_code = db.Column(db.String(64))
    issuing_depart = db.Column(db.String(64))

    # 價格與規格
    price_usd = db.Column(db.Float)
    specification = db.Column(db.String(8))
    packaging_quantity = db.Column(db.String(8))

    # 存儲相關
    storage_life = db.Column(db.String(8))
    storage_process = db.Column(db.String(8))
    storage_type = db.Column(db.String(8))

    # 分類相關
    classification = db.Column(db.String(8))
    consumability = db.Column(db.String(8))
    repair_capability = db.Column(db.String(8))

    # 能量與來源
    manufacturing_capability = db.Column(db.String(8))
    source = db.Column(db.String(8))
    system = db.Column(db.String(8))
    category = db.Column(db.String(8))

    # 其他信息
    manufacturer = db.Column(db.String(64))
    pn = db.Column(db.String(64))
    ship_category = db.Column(db.String(64))

    # 展開的更多欄位
    pn_acquisition_level = db.Column(db.String(64))
    pn_acquisition_source = db.Column(db.String(64))
    configuration_identification_number = db.Column(db.String(64))
    part_model_id = db.Column(db.String(64))
    item_name1 = db.Column(db.String(128))
    installation_number = db.Column(db.Integer)
    location = db.Column(db.String(64))
    federal_item_identification_guide = db.Column(db.String(64))

    def __repr__(self):
        return f'<DataItem {self.navy_part_number}>'