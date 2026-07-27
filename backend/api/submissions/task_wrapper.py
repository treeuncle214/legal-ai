"""
TaskWrapper 类
"""
from typing import List


class TaskWrapper:
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.title = data.get('title')
        self.description = data.get('description')
        self.due_date = data.get('due_date')
        self.task_type = data.get('task_type', '任务实践')
        self.enabled_indicators = data.get('enabled_indicators', '')
        self.max_submissions = data.get('max_submissions', 3)
        self.allow_after_deadline = data.get('allow_after_deadline', 0)
        self.class_id = data.get('class_id')
    
    def get_enabled_indicators_list(self) -> List[str]:
        if not self.enabled_indicators:
            return []
        return [s.strip() for s in self.enabled_indicators.split(',') if s.strip()]