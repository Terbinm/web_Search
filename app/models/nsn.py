from datetime import datetime
from app import db


class NSN(db.Model):
    """NSN數據模型"""
    __tablename__ = 'nsns'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 基本信息
    nsn = db.Column(db.String(20), index=True, unique=True)  # NSN號碼
    item_name = db.Column(db.String(256))  # 物品名稱
    federal_supply_classification = db.Column(db.String(128))  # 聯邦供應分類
    national_item_identification_number = db.Column(db.String(128))  # 國家識別號碼
    codification_country = db.Column(db.String(64))  # 編碼國家
    item_name_code = db.Column(db.String(64), nullable=True)  # 物品名稱代碼

    # 特性與指標
    criticality = db.Column(db.Text, nullable=True)  # 關鍵性指標
    hazardous_material_indicator_code = db.Column(db.Text, nullable=True)  # 危險物質指標代碼

    # 相關料號，以逗號分隔的字符串存儲
    part_number_list = db.Column(db.Text, nullable=True)  # 相關料號列表

    # 查詢來源
    source_key = db.Column(db.String(64), index=True, nullable=True)  # 查詢時使用的關鍵字

    def __repr__(self):
        return f'<NSN {self.nsn}>'

    @property
    def part_numbers(self):
        """返回相關料號列表"""
        if self.part_number_list:
            return [pn.strip() for pn in self.part_number_list.split(',')]
        return []