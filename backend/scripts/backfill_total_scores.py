"""
回填历史 total_score：将旧数据（原始指标得分之和）重算为百分制总分。

背景
----
早期版本把 total_score 存为「所有启用指标的原始得分直接相加」（量纲 = 满分之和，
例如 4 维度 13 个指标、每个满分 10，则 total_score 落在 0~130 区间），而维度得分
final_score_* 是百分制（0~100）。这导致学生画像的「综合得分」（平均 total_score）
与维度得分口径不一致。

本次修复后，新评分（score_exercise / review_submission / fallback）已统一按百分制存储：
    total_score = 启用指标得分之和 / 启用指标满分之和 × 100

本脚本用于把库里已存在的旧 total_score 一次性回填为百分制，无需重跑 AI 评分。

用法（在项目根目录执行）：
    python -m backend.scripts.backfill_total_scores            # 直接回填
    python -m backend.scripts.backfill_total_scores --dry-run  # 只预览，不写库
"""
import argparse

from backend.database.engine import SessionLocal
from backend.database.models import (
    Submission,
    SubmissionScore,
    Task,
    TaskRubric,
    TaskRubricIndicator,
)


def _get_indicator_max_scores(db, task_id):
    """返回 {indicator_key: max_score}，来自该任务的评分快照，缺省 10。"""
    max_scores = {}
    rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task_id).first()
    if rubric:
        indicators = db.query(TaskRubricIndicator).filter(
            TaskRubricIndicator.task_rubric_id == rubric.id
        ).all()
        for ind in indicators:
            max_scores[ind.indicator_key] = ind.max_score
    return max_scores


def backfill(dry_run=False):
    db = SessionLocal()
    try:
        scored_ids = [row[0] for row in db.query(SubmissionScore.submission_id).distinct().all()]
        if not scored_ids:
            print("未发现已评分的提交，无需回填。")
            return

        submissions = db.query(Submission).filter(Submission.id.in_(scored_ids)).all()

        updated = 0
        unchanged = 0
        for sub in submissions:
            scores = db.query(SubmissionScore).filter(
                SubmissionScore.submission_id == sub.id
            ).all()
            indicator_score_dict = {s.indicator_key: s.score for s in scores}

            task = db.query(Task).filter(Task.id == sub.task_id).first()
            enabled = task.get_enabled_indicators_list() if task else []
            max_scores = _get_indicator_max_scores(db, sub.task_id)

            total_raw = 0.0
            total_max = 0.0
            for key, score in indicator_score_dict.items():
                if enabled and key not in enabled:
                    continue
                if score is None:
                    continue
                total_raw += score
                total_max += max_scores.get(key, 10)

            new_total = round(total_raw / total_max * 100, 2) if total_max > 0 else 0.0
            old_total = sub.total_score or 0.0

            if abs(old_total - new_total) < 0.01:
                unchanged += 1
                continue

            if not dry_run:
                sub.total_score = new_total
            updated += 1
            print(f"  #{sub.id} 学生={sub.student_username}  旧={old_total} -> 新={new_total}")

        if not dry_run:
            db.commit()
            print(f"\n✅ 已回填 {updated} 条 total_score（{unchanged} 条无需变化）")
        else:
            print(f"\n[dry-run] 将回填 {updated} 条（{unchanged} 条无需变化），未写入数据库")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="回填历史 total_score 为百分制")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写库")
    args = parser.parse_args()
    backfill(dry_run=args.dry_run)
