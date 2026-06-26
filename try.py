from backend.database.tasks import add_task, get_task

# 创建带自定义提示词的任务
task_id = add_task(
    title="测试自定义提示词",
    description="测试描述",
    due_date="2026-12-31",
    created_by="admin",
    task_type="课堂练习",
    custom_prompt="你是一位严格的评分教师。任务：{task_title}\n学生提交：{final_output}\n请给出评分。"
)

# 获取任务详情
task = get_task(task_id)
print(f"custom_prompt: {task.get('custom_prompt')}")