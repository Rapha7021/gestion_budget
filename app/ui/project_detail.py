from __future__ import annotations
from pathlib import Path
from datetime import date, datetime
from typing import Optional, List, Dict, Any
import json
from PySide6.QtWidgets import QSplitter 

from PySide6.QtCore import QLocale, Qt, QSize
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QScrollArea, QWidget, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QGroupBox, QInputDialog, QListWidget, QListWidgetItem, QFrame
)

# --- Hooks repo (à implémenter côté app.db.repo)
try:
    from app.db.repo import list_budget_lines, list_project_news, create_project_news
except Exception:
    # Fallback minimal pour que l'UI tourne sans repo d'actus
    def list_project_news(project_id: int) -> List[Dict[str, Any]]:
        return getattr(ProjectDetailDialog, "_mem_news", {}).get(project_id, [])

    def create_project_news(project_id: int, text: str, created_at: datetime) -> Dict[str, Any]:
        store = getattr(ProjectDetailDialog, "_mem_news", {})
        store.setdefault(project_id, [])
        item = {"project_id": project_id, "text": text, "created_at": created_at.isoformat()}
        store[project_id].insert(0, item)  # plus récent en haut
        setattr(ProjectDetailDialog, "_mem_news", store)
        return item

EURO = QLocale(QLocale.Language.French, QLocale.Country.France)

def fmt_month_yyyy(d: Optional[date]) -> str:
    if not d:
        return "—"
    return EURO.toString(d, "MMMM yyyy")

def fmt_euros(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return EURO.toCurrencyString(float(v), symbol="€")

def cents_to_euros(cents: Optional[int]) -> Optional[float]:
    if cents is None: return None
    return round(cents / 100.0, 2)

def fmt_dt_hm(dt: datetime | str | None) -> str:
    if not dt:
        return "—"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt
    return dt.strftime("%d/%m/%Y %H:%M")
# [...] Garde tous tes imports actuels + le fallback list_project_news / create_project_news si besoin

from app.db.repo import (
    list_project_news,
    create_project_news,
    update_project_news,
    delete_project_news
)

class ProjectDetailDialog(QDialog):
    def __init__(self, project, parent=None) -> None:
        super().__init__(parent)
        self.project = project
        self.setWindowTitle(f"Détail — {project.name} ({project.code})")
        self.setMinimumSize(QSize(1200, 800))
        self.setWindowState(Qt.WindowMaximized)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        # 1) Bloc infos projet (unique)
        outer.addWidget(self._project_info_panel())

        # 2) Bloc actualités
        outer.addWidget(self._news_panel())

        # 3) Bas de page
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        bottom.addWidget(btn_close)
        outer.addLayout(bottom)

    def _project_info_panel(self) -> QWidget:
        box = QGroupBox("Informations projet")
        h = QHBoxLayout(box)
        h.setContentsMargins(8, 8, 8, 8)
        h.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # --- Colonne 1 : Général + Thèmes
        col1 = QWidget()
        v1 = QVBoxLayout(col1)
        v1.setContentsMargins(0, 0, 0, 0)
        v1.setSpacing(6)
        v1.addWidget(self._section_general())
        v1.addWidget(self._section_themes())
        v1.addStretch(1)

        # --- Colonne 2 : Contenu
        col2 = QWidget()
        v2 = QVBoxLayout(col2)
        v2.setContentsMargins(0, 0, 0, 0)
        v2.setSpacing(6)
        v2.addWidget(self._section_contenu())
        v2.addStretch(1)

        # --- Colonne 3 : Financements + Investissement + Images + Métadonnées
        col3 = QWidget()
        v3 = QVBoxLayout(col3)
        v3.setContentsMargins(0, 0, 0, 0)
        v3.setSpacing(6)
        v3.addWidget(self._section_financements())
        v3.addWidget(self._section_investissement())
        v3.addWidget(self._section_images())
        v3.addWidget(self._section_metadonnees())
        v3.addStretch(1)

        splitter.addWidget(col1)
        splitter.addWidget(col2)
        splitter.addWidget(col3)

        # Largeur relative des colonnes (ajuste si besoin)
        splitter.setStretchFactor(0, 1)  # Général
        splitter.setStretchFactor(1, 2)  # Contenu (plus large)
        splitter.setStretchFactor(2, 1)  # Finances/Images/Meta

        h.addWidget(splitter)
        return box

    # ---------- Helpers sections en colonnes ----------

    def _mk_section(self, title: str) -> QGroupBox:
        gb = QGroupBox(title)
        form = QFormLayout(gb)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(4)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        return gb

    def _section_general(self) -> QWidget:
        gb = self._mk_section("Général")
        gb.layout().addRow("Code projet", QLabel(self.project.code))
        gb.layout().addRow("Nom projet", QLabel(self.project.name))
        gb.layout().addRow("Chef(fe) de projet", QLabel(self.project.owner or "—"))
        gb.layout().addRow("Période", QLabel(f"{fmt_month_yyyy(self.project.start_date)} → {fmt_month_yyyy(self.project.end_date)}"))
        gb.layout().addRow("État", QLabel(self.project.status or "—"))
        return gb

    def _section_themes(self) -> QWidget:
        gb = self._mk_section("Thèmes")
        themes_raw = getattr(self.project, "themes", None)
        try:
            themes_list = json.loads(themes_raw) if isinstance(themes_raw, str) else themes_raw or []
        except Exception:
            themes_list = []
        gb.layout().addRow("Thèmes", QLabel(", ".join(themes_list) if themes_list else "—"))
        return gb

    def _section_contenu(self) -> QWidget:
        gb = self._mk_section("Contenu")
        det = self._multiline(self.project.description)
        liv = self._multiline(self.project.deliverables)
        gb.layout().addRow("Détails", det)
        gb.layout().addRow("Livrables", liv)
        return gb

    def _section_financements(self) -> QWidget:
        gb = self._mk_section("Financements / Crédits")
        gb.layout().addRow("Subvention", QLabel("Oui" if self.project.subvention else "Non"))
        gb.layout().addRow("Montant subvention", QLabel(fmt_euros(self.project.subvention_montant)))
        return gb

    def _section_investissement(self) -> QWidget:
        gb = self._mk_section("Investissement")
        inv_list = self.project.investissement or []
        if isinstance(inv_list, dict):
            inv_list = [inv_list]

        table = QTableWidget(len(inv_list), 3)
        table.setHorizontalHeaderLabels(["Montant", "Date", "Durée"])
        for i, inv in enumerate(inv_list):
            table.setItem(i, 0, QTableWidgetItem(fmt_euros(inv.get("montant"))))
            table.setItem(i, 1, QTableWidgetItem(str(inv.get("date") or "")))
            table.setItem(i, 2, QTableWidgetItem(str(inv.get("duree_mois") or "")))
        gb.layout().addRow(table)

        gb.layout().addRow("Montant", QLabel(fmt_euros(inv.get("montant"))))
        gb.layout().addRow("Date d’achat", QLabel(self._fmt_inv_date(inv.get("date"))))
        gb.layout().addRow("Durée (mois)", QLabel(str(inv.get("duree_mois") or "—")))
        return gb

    def _section_equipe(self) -> QWidget:
        gb = self._mk_section("Équipe")
        team = self.project.team or {}
        if isinstance(team, str):
            import json
            team = json.loads(team)
        if not team:
            gb.layout().addRow("Aucun membre")
            return gb
        for role, nb in team.items():
            gb.layout().addRow(role, QLabel(str(nb)))
        return gb

    def _section_images(self) -> QWidget:
        gb = self._mk_section("Images")
        images_raw = self.project.images or []
        if isinstance(images_raw, str):
            try:
                images_raw = json.loads(images_raw)
            except Exception:
                images_raw = []
        gb.layout().addRow("Fichiers", self._images_widget(images_raw))
        return gb

    def _section_metadonnees(self) -> QWidget:
        gb = self._mk_section("Métadonnées")
        gb.layout().addRow("Créé le", QLabel(self._fmt_dt(getattr(self.project, "created_at", None))))
        gb.layout().addRow("Mis à jour le", QLabel(self._fmt_dt(getattr(self.project, "updated_at", None))))
        return gb


    def _news_panel(self) -> QWidget:
        panel = QGroupBox("Actualités")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        btn_add = QPushButton("＋ Ajouter une actu")
        btn_add.setMaximumWidth(180)
        btn_add.clicked.connect(self._add_news_dialog)
        layout.addWidget(btn_add)

        self.news_list = QListWidget()
        self.news_list.setWordWrap(True)
        self.news_list.setFrameShape(QFrame.NoFrame)
        self.news_list.setMaximumHeight(200)
        self.news_list.setMinimumHeight(40)
        self.news_list.setSpacing(2)
        layout.addWidget(self.news_list)

        self._reload_news()
        return panel



    def _reload_news(self):
        self.news_list.clear()
        try:
            items = list_project_news(self.project.id)
        except Exception:
            items = []

        for news in items:
            txt = news["text"]
            dt = fmt_dt_hm(news["created_at"])
            item_widget = QWidget()
            row = QHBoxLayout(item_widget)
            row.setContentsMargins(0, 0, 0, 0)

            label = QLabel(f"{dt} — {txt}")
            label.setWordWrap(True)
            row.addWidget(label, 1)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(28, 28)
            btn_edit.clicked.connect(lambda _, nid=news["id"], txt=txt: self._edit_news(nid, txt))
            row.addWidget(btn_edit)

            btn_del = QPushButton("🗑️")
            btn_del.setFixedSize(28, 28)
            btn_del.clicked.connect(lambda _, nid=news["id"]: self._delete_news(nid))
            row.addWidget(btn_del)

            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            self.news_list.addItem(item)
            self.news_list.setItemWidget(item, item_widget)

    def _add_news_dialog(self):
        txt, ok = QInputDialog.getMultiLineText(self, "Nouvelle actualité", "Message :", "")
        if ok and txt.strip():
            try:
                create_project_news(self.project.id, txt.strip(), datetime.now())
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Ajout impossible : {e}")
            self._reload_news()

    def _edit_news(self, news_id: int, current_text: str):
        txt, ok = QInputDialog.getMultiLineText(self, "Modifier l’actualité", "Message :", current_text)
        if ok and txt.strip():
            try:
                update_project_news(news_id, txt.strip())
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Modification impossible : {e}")
            self._reload_news()

    def _delete_news(self, news_id: int):
        confirm = QMessageBox.question(self, "Supprimer", "Supprimer cette actualité ?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                delete_project_news(news_id)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Suppression impossible : {e}")
            self._reload_news()

    # --- Helpers
    def _title(self, txt: str) -> QLabel:
        lab = QLabel(f"<h3 style='margin:8px 0'>{txt}</h3>")
        lab.setTextFormat(Qt.RichText)
        return lab

    def _multiline(self, text: Optional[str]) -> QLabel:
        lab = QLabel(text or "—")
        lab.setWordWrap(True)
        lab.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return lab

    def _images_widget(self, images: List[Dict[str, Any]]) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        if not images:
            row.addWidget(QLabel("—"))
            return w
        for img in images:
            path = img.get("url") or img if isinstance(img, str) else "inconnu"
            btn = QPushButton(Path(path).name)
            btn.setToolTip(path)
            btn.clicked.connect(lambda _, p=path: QDesktopServices.openUrl(f"file:///{Path(p).resolve()}"))
            row.addWidget(btn)
        row.addStretch(1)
        return w

    def _fmt_dt(self, dt: Any) -> str:
        if not dt: return "—"
        try:
            return EURO.toString(dt, "dd/MM/yyyy HH:mm")
        except Exception:
            return str(dt)

    def _fmt_inv_date(self, v: Any) -> str:
        if isinstance(v, date):
            return fmt_month_yyyy(v)
        if not v:
            return "—"
        return str(v)

    def _to_dict(self, p) -> Dict[str, Any]:
        return {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "owner": p.owner,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "description": p.description,
            "deliverables": p.deliverables,
            "status": p.status,
            "cir": p.cir,
            "cir_montant": p.cir_montant,
            "subvention": p.subvention,
            "subvention_montant": p.subvention_montant,
            "investissement": p.investissement,
            "themes": p.themes,
            "images": p.images,
            "created_at": getattr(p, "created_at", None),
            "updated_at": getattr(p, "updated_at", None),
        }
