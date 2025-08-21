from contextlib import contextmanager
from typing import Optional, List
from datetime import date, datetime

from .models import (
    SessionLocal, Base, engine,
    Project, BudgetLine, ProjectNews
)

# --- Initialisation DB ---
def init_db() -> None:
    """Crée les tables si absentes."""
    Base.metadata.create_all(bind=engine)

# --- Session ---
@contextmanager
def get_session():
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()

# --- CRUD Projects ---
def create_project(code: str, name: str, owner: Optional[str] = None,
                   start_date: Optional[date] = None, end_date: Optional[date] = None,
                   description: Optional[str] = None, deliverables: Optional[str] = None,
                   status: Optional[str] = None,
                   cir: bool = False, cir_montant: Optional[float] = None,
                   subvention: bool = False, subvention_montant: Optional[float] = None,
                   amortissement: bool = False,
                   investissement: Optional[dict] = None,
                   themes: Optional[list] = None,
                   images: Optional[list] = None, team: Optional[dict] = None) -> Project:
    with get_session() as s:
        p = Project(
            code=code,
            name=name,
            owner=owner,
            start_date=start_date,
            end_date=end_date,
            description=description,
            deliverables=deliverables,
            status=status,
            cir=cir,
            cir_montant=cir_montant,
            subvention=subvention,
            subvention_montant=subvention_montant,
            amortissement=amortissement,
            themes=themes,
            images=images,
            investissement=investissement,
            team=team,
        )
        s.add(p)
        s.flush()
        return p

def list_projects() -> List[Project]:
    with get_session() as s:
        return s.query(Project).order_by(Project.created_at.desc()).all()

def get_project(project_id: int) -> Optional[Project]:
    with get_session() as s:
        return s.get(Project, project_id)

def update_project(project_id: int, **fields) -> Optional[Project]:
    with get_session() as s:
        p = s.get(Project, project_id)
        if not p: return None
        for k, v in fields.items():
            if hasattr(p, k):
                setattr(p, k, v)
        s.flush()
        return p

def delete_project(project_id: int) -> bool:
    with get_session() as s:
        p = s.get(Project, project_id)
        if not p: return False
        s.delete(p)
        return True

# --- CRUD Budget lines ---
def add_budget_line(project_id: int, label: str, amount_cents: int,
                    is_capex: bool = True, value_date: Optional[date] = None) -> Optional[BudgetLine]:
    with get_session() as s:
        if not s.get(Project, project_id):
            return None
        bl = BudgetLine(
            project_id=project_id,
            label=label,
            amount_cents=amount_cents,
            is_capex=is_capex,
            value_date=value_date
        )
        s.add(bl)
        s.flush()
        return bl

def list_budget_lines(project_id: int) -> List[BudgetLine]:
    with get_session() as s:
        return (
            s.query(BudgetLine)
            .filter(BudgetLine.project_id == project_id)
            .order_by(BudgetLine.created_at.asc())
            .all()
        )

# --- CRUD Actualités projets ---
def list_project_news(project_id: int) -> List[dict]:
    with get_session() as s:
        return [
            {
                "id": n.id,
                "project_id": n.project_id,
                "text": n.text,
                "created_at": n.created_at.isoformat()
            }
            for n in s.query(ProjectNews)
                     .filter(ProjectNews.project_id == project_id)
                     .order_by(ProjectNews.created_at.desc())
                     .all()
        ]

def create_project_news(project_id: int, text: str, created_at: Optional[datetime] = None) -> dict:
    with get_session() as s:
        if not s.get(Project, project_id):
            raise ValueError("Projet introuvable")
        news = ProjectNews(
            project_id=project_id,
            text=text.strip(),
            created_at=created_at or datetime.utcnow()
        )
        s.add(news)
        s.flush()
        return {
            "id": news.id,
            "project_id": news.project_id,
            "text": news.text,
            "created_at": news.created_at.isoformat()
        }
    
def update_project_news(news_id: int, new_text: str) -> bool:
    with get_session() as s:
        news = s.get(ProjectNews, news_id)
        if not news:
            return False
        news.text = new_text.strip()
        s.flush()
        return True
def delete_project_news(news_id: int) -> bool:
    with get_session() as s:
        news = s.get(ProjectNews, news_id)
        if not news:
            return False
        s.delete(news)
        return True


# --- Seed démo ---
def seed_demo_if_empty() -> None:
    with get_session() as s:
        if s.query(Project.id).first():
            return
        p = Project(code="PRJ-2025-001", name="Migration ERP", owner="Direction Financière")
        s.add(p); s.flush()
        s.add_all([
            BudgetLine(project_id=p.id, label="Licences ERP", amount_cents=120_000_00, is_capex=True),
            BudgetLine(project_id=p.id, label="Presta intégration", amount_cents=80_000_00, is_capex=True),
            BudgetLine(project_id=p.id, label="Formation", amount_cents=15_000_00, is_capex=False),
        ])
