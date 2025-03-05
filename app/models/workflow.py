# 此檔案由自動腳本建立
from datetime import datetime
import json
from app import db


class WorkflowInstance(db.Model):
    """工作流程實例模型，存儲料號申編流程的狀態和數據"""
    __tablename__ = 'workflow_instances'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    current_step = db.Column(db.Integer, default=1)  # 1-5 代表不同步驟
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, cancelled

    # 各步驟數據 (存儲為JSON)
    step1_data = db.Column(db.Text, nullable=True)  # Dify查詢和結果
    step2_data = db.Column(db.Text, nullable=True)  # LLM查詢和結果
    step3_data = db.Column(db.Text, nullable=True)  # INC查詢和結果
    step4_data = db.Column(db.Text, nullable=True)  # 料號建立數據
    step5_data = db.Column(db.Text, nullable=True)  # 完成數據

    # 關鍵數據快速存取欄位
    fsc_code = db.Column(db.String(10), nullable=True)
    fsc_description = db.Column(db.String(256), nullable=True)
    part_number = db.Column(db.String(64), nullable=True)
    part_name = db.Column(db.String(256), nullable=True)
    created_part_id = db.Column(db.Integer, nullable=True)  # 指向創建的料號ID

    # 時間戳記
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<WorkflowInstance {self.id}: Step {self.current_step}, Status {self.status}>'

    def set_step_data(self, step: int, data: dict):
        """設置特定步驟的數據"""
        if step == 1:
            self.step1_data = json.dumps(data)
            if 'fsc_code' in data and data['fsc_code']:
                self.fsc_code = data['fsc_code']
            if 'fsc_description' in data and data['fsc_description']:
                self.fsc_description = data['fsc_description']
        elif step == 2:
            self.step2_data = json.dumps(data)
            if 'part_number' in data and data['part_number']:
                self.part_number = data['part_number']
            if 'part_name' in data and data['part_name']:
                self.part_name = data['part_name']
        elif step == 3:
            self.step3_data = json.dumps(data)
        elif step == 4:
            self.step4_data = json.dumps(data)
        elif step == 5:
            self.step5_data = json.dumps(data)
            if 'created_part_id' in data and data['created_part_id']:
                self.created_part_id = data['created_part_id']

    def get_step_data(self, step: int) -> dict:
        """獲取特定步驟的數據"""
        data_str = None
        if step == 1:
            data_str = self.step1_data
        elif step == 2:
            data_str = self.step2_data
        elif step == 3:
            data_str = self.step3_data
        elif step == 4:
            data_str = self.step4_data
        elif step == 5:
            data_str = self.step5_data

        if data_str:
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                return {}
        return {}

    def complete_workflow(self, part_id=None):
        """完成工作流程"""
        self.status = 'completed'
        self.current_step = 5
        self.completed_at = datetime.utcnow()
        if part_id:
            self.created_part_id = part_id
            # 存儲完成數據
            data = {'created_part_id': part_id}
            self.set_step_data(5, data)

    def cancel_workflow(self):
        """取消工作流程"""
        self.status = 'cancelled'

    @classmethod
    def get_active_workflow_for_user(cls, user_id):
        """獲取用戶的活動工作流程"""
        return cls.query.filter_by(
            user_id=user_id,
            status='in_progress'
        ).order_by(cls.updated_at.desc()).first()

    @classmethod
    def get_recent_workflows(cls, user_id, limit=5):
        """獲取用戶最近的工作流程"""
        return cls.query.filter_by(
            user_id=user_id
        ).order_by(cls.updated_at.desc()).limit(limit).all()