from backend.database.engine import SessionLocal
from backend.database.models import RubricTemplate, TemplateShare
db = SessionLocal()

templates = db.query(RubricTemplate).all()
print('所有模板:')
for t in templates:
    print(f'  id={t.id}, name={t.name}, created_by={t.created_by}, share_type={t.share_type}')

shares = db.query(TemplateShare).all()
print('\n所有共享记录:')
for s in shares:
    print(f'  template_id={s.template_id}, shared_with={s.shared_with}')

db.close()