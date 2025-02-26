from app import db
from datetime import datetime

class PartNumber(db.Model):
    """料號模型"""
    __tablename__ = 'Movie'  # 使用您指定的資料表名稱

    Id = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String)
    Genre = db.Column(db.String)
    Price = db.Column(db.Numeric(18, 2), nullable=False)
    ItemName = db.Column(db.String)
    PriceUSD = db.Column(db.String)
    IssuingDepart = db.Column(db.String)
    Specification = db.Column(db.String)
    PackagingQuantity = db.Column(db.String)
    StorageLife = db.Column(db.String)
    StorageProcess = db.Column(db.String)
    Classification = db.Column(db.String)
    Consumability = db.Column(db.String)
    StorageType = db.Column(db.String)
    ManufacturingCapability = db.Column(db.String)
    RepairCapability = db.Column(db.String)
    Source = db.Column(db.String)
    Category = db.Column(db.String)
    System = db.Column(db.String)
    Manufacturer = db.Column(db.String)
    PN = db.Column(db.String)
    PNAcquisitionLevel = db.Column(db.String)
    PNAcquisitionSource = db.Column(db.String)
    ShipCategory = db.Column(db.String)
    ConfigurationIdentificationNumber = db.Column(db.String)
    FederalItemIdentificationGuide = db.Column(db.String)
    InstallationNumber = db.Column(db.String)
    ItemName1 = db.Column(db.String)
    Location = db.Column(db.String)
    PartModelID = db.Column(db.String)
    PartSpecification = db.Column(db.String)
    AccountingNumber = db.Column(db.String)
    ItemNameEnglish = db.Column(db.String)
    ItemNameChinese = db.Column(db.String)
    NavyPartNumberPrefix = db.Column(db.String)

    def __repr__(self):
        return f'<PartNumber {self.Id}: {self.PN}>'