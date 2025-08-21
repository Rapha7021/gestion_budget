import os
from datetime import date
from typing import Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, Date, Text, Boolean, ForeignKey,
    DateTime, func, UniqueConstraint, Float, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL", "sqlite:///./media/app.db")

# Pour SQLite + threads (Qt), on force check_same_thread=False
engine = create_engine(
    DB_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True, expire_on_commit=False)
Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("code", name="uq_project_code"),)

    id = Column(Integer, primary_key=True)
    code = Column(String(32), nullable=False)
    name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    deliverables = Column(Text, nullable=True)
    status = Column(String(64), nullable=True)

    cir = Column(Boolean, nullable=False, default=False)
    cir_montant = Column(Float, nullable=True)
    subvention = Column(Boolean, nullable=False, default=False)
    subvention_montant = Column(Float, nullable=True)
    amortissement = Column(Boolean, nullable=False, default=False)

    investissement = Column(JSON, nullable=True)  # dict {montant, date, duree_mois}
    themes = Column(JSON, nullable=True)          # liste de str
    images = Column(JSON, nullable=True)          # liste de chemins

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    budget_lines = relationship("BudgetLine", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project id={self.id} code={self.code} name={self.name!r}>"


class BudgetLine(Base):
    __tablename__ = "budget_lines"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    label = Column(String(255), nullable=False)      # ex: "Serveurs", "Prestations", "Licences"
    is_capex = Column(Boolean, nullable=False, default=True)
    amount_cents = Column(Integer, nullable=False, default=0)
    value_date = Column(Date, nullable=True)         # date de dépense / engagement

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project", back_populates="budget_lines")

    def __repr__(self) -> str:
        sign = "-" if (self.amount_cents or 0) < 0 else ""
        return f"<BudgetLine id={self.id} {sign}{abs(self.amount_cents)}c {self.label!r}>"

class ProjectNews(Base):
    __tablename__ = "project_news"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
