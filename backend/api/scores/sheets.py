"""
Excel Sheet 构建函数
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from backend.config import SCORING_DIMENSIONS
from backend.api.scores.helpers import get_level


def create_sheet1(ws, students, tasks, all_scores, student_names, task_info):
    """Sheet 1: 任务总览"""
    # ✅ 添加学院和专业列
    headers = ["学号", "姓名", "学院", "专业"]
    task_ids = []
    for task in tasks:
        headers.append(f"{task.title}")
        task_ids.append(task.id)
    headers.append("平均分")
    headers.append("等级")
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    row_num = 2
    student_scores = {}
    
    for student in students:
        username = student["username"]
        display_name = student["display_name"]
        college = student.get("college", "")
        major = student.get("major", "")
        student_scores[username] = []
        
        ws.cell(row=row_num, column=1, value=username)
        ws.cell(row=row_num, column=2, value=display_name)
        ws.cell(row=row_num, column=3, value=college or "-")
        ws.cell(row=row_num, column=4, value=major or "-")
        
        col = 5  # 从第5列开始是任务成绩
        total_sum = 0
        valid_count = 0
        
        for task in tasks:
            score_data = all_scores.get(username, {}).get(task.id)
            if score_data:
                score = score_data["total"]
                ws.cell(row=row_num, column=col, value=score)
                total_sum += score
                valid_count += 1
                student_scores[username].append(score)
            else:
                ws.cell(row=row_num, column=col, value="-")
            col += 1
        
        avg_score = round(total_sum / valid_count, 2) if valid_count > 0 else 0
        level = get_level(avg_score) if valid_count > 0 else "未提交"
        
        ws.cell(row=row_num, column=col, value=avg_score)
        ws.cell(row=row_num, column=col + 1, value=level)
        
        row_num += 1
    
    if row_num > 2:
        ws.cell(row=row_num, column=1, value="📊 全班平均")
        ws.cell(row=row_num, column=2, value="")
        ws.cell(row=row_num, column=3, value="")
        ws.cell(row=row_num, column=4, value="")
        
        col = 5
        for task in tasks:
            scores = []
            for student in students:
                score_data = all_scores.get(student["username"], {}).get(task.id)
                if score_data:
                    scores.append(score_data["total"])
            avg = round(sum(scores) / len(scores), 2) if scores else 0
            ws.cell(row=row_num, column=col, value=avg)
            col += 1
        
        all_avg = []
        for student in students:
            student_avg = student_scores.get(student["username"], [])
            if student_avg:
                all_avg.append(sum(student_avg) / len(student_avg))
        total_avg = round(sum(all_avg) / len(all_avg), 2) if all_avg else 0
        ws.cell(row=row_num, column=col, value=total_avg)
        
        summary_font = Font(bold=True)
        summary_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        for c in range(1, col + 2):
            cell = ws.cell(row=row_num, column=c)
            cell.font = summary_font
            cell.fill = summary_fill
    
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 14
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 16  # 学院列
    ws.column_dimensions["D"].width = 16  # 专业列


def create_sheet4(ws, tasks, all_scores, student_names, task_info):
    """Sheet 4: 各任务汇总"""
    dimension_keys = [d["key"] for d in SCORING_DIMENSIONS]
    dimension_names = {d["key"]: d["name"] for d in SCORING_DIMENSIONS}
    
    headers = ["任务名称", "任务类型"]
    for dim_key in dimension_keys:
        headers.append(f"{dimension_names[dim_key]}(平均)")
    headers.append("全班平均分")
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    row_num = 2
    for task in tasks:
        ws.cell(row=row_num, column=1, value=task.title)
        ws.cell(row=row_num, column=2, value=task_info[task.id]["type"])
        
        col = 3
        total_scores = []
        
        for dim_key in dimension_keys:
            scores = []
            for student in student_names.keys():
                score_data = all_scores.get(student, {}).get(task.id)
                if score_data:
                    dim_score = score_data["dimension_scores"].get(dim_key, 0)
                    if dim_score > 0:
                        scores.append(dim_score)
                    total_scores.append(score_data["total"])
            
            avg = round(sum(scores) / len(scores), 2) if scores else 0
            ws.cell(row=row_num, column=col, value=avg)
            col += 1
        
        task_avg = round(sum(total_scores) / len(total_scores), 2) if total_scores else 0
        ws.cell(row=row_num, column=col, value=task_avg)
        
        row_num += 1
    
    if row_num > 2:
        ws.cell(row=row_num, column=1, value="📊 全部任务汇总")
        ws.cell(row=row_num, column=2, value="")
        
        col = 3
        for dim_key in dimension_keys:
            dim_scores = []
            for task in tasks:
                task_row = tasks.index(task) + 2
                val = ws.cell(row=task_row, column=col).value
                if val and val > 0:
                    dim_scores.append(val)
            avg = round(sum(dim_scores) / len(dim_scores), 2) if dim_scores else 0
            ws.cell(row=row_num, column=col, value=avg)
            col += 1
        
        all_avgs = []
        for task in tasks:
            task_row = tasks.index(task) + 2
            val = ws.cell(row=task_row, column=col).value
            if val and val > 0:
                all_avgs.append(val)
        total_avg = round(sum(all_avgs) / len(all_avgs), 2) if all_avgs else 0
        ws.cell(row=row_num, column=col, value=total_avg)
        
        summary_font = Font(bold=True)
        summary_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        for c in range(1, col + 1):
            cell = ws.cell(row=row_num, column=c)
            cell.font = summary_font
            cell.fill = summary_fill
    
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 16
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 14