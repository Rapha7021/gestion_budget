from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QTableView, QMessageBox
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from datetime import datetime

from app.db.repo import list_projects, create_project, update_project, delete_project
from .project_form import ProjectFormDialog
from .project_detail import ProjectDetailDialog
from PySide6.QtWidgets import QDialog


def parse_ym_to_date(s: str):
    try:
        return datetime.strptime(s, "%Y-%m").date() if s else None
    except ValueError:
        return None


class ProjectTableModel(QAbstractTableModel):
    HEADERS = ["Code", "Nom", "Responsable", "Début", "Fin"]

    def __init__(self):
        super().__init__()
        self._rows = []

    def load(self):
        self.beginResetModel()
        self._rows = list_projects()  # objets Project
        self.endResetModel()

    # Qt model API
    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        p = self._rows[index.row()]
        col = index.column()
        if col == 0:
            return p.code
        if col == 1:
            return p.name
        if col == 2:
            return p.owner or ""
        if col == 3:
            return p.start_date.isoformat() if p.start_date else ""
        if col == 4:
            return p.end_date.isoformat() if p.end_date else ""
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return str(section + 1)

    # util
    def count(self) -> int:
        return len(self._rows)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Gestion budgétaire — Projets")
        self.model = ProjectTableModel()
        self._setup_ui()
        self.refresh()
        self.table.doubleClicked.connect(self.on_row_double_clicked)


    def on_row_double_clicked(self, index: QModelIndex):
        if not index.isValid():
            return
        row = index.row()
        if row < 0 or row >= self.model.count():
            return
        project = self.model._rows[row]
        dlg = ProjectDetailDialog(project, self)
        dlg.exec()

    def _setup_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)

        # Barre d'actions
        actions = QHBoxLayout()
        btn_new = QPushButton("Nouveau projet")
        btn_new.clicked.connect(self.on_new_project)
        actions.addWidget(btn_new)

        btn_edit = QPushButton("Modifier projet")
        btn_edit.clicked.connect(self.on_edit_project)
        actions.addWidget(btn_edit)

        btn_delete = QPushButton("Supprimer projet")
        btn_delete.clicked.connect(self.on_delete_project)
        actions.addWidget(btn_delete)

        actions.addStretch(1)
        layout.addLayout(actions)

        # Table
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)  # activable plus tard
        layout.addWidget(self.table)

        # Placeholder si vide
        self.empty_label = QLabel("Aucun projet pour le moment.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)
        self.empty_label.hide()

        self.setCentralWidget(root)

    def refresh(self):
        self.model.load()
        count = self.model.count()
        self.setWindowTitle(f"Gestion budgétaire — {count} projet(s)")
        self.table.setVisible(count > 0)
        self.empty_label.setVisible(count == 0)
        if count > 0:
            self.table.resizeColumnsToContents()
            self.table.horizontalHeader().setStretchLastSection(True)

    def on_new_project(self):
        dlg = ProjectFormDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            data["start_date"] = parse_ym_to_date(data.get("start_date"))
            data["end_date"] = parse_ym_to_date(data.get("end_date"))
            try:
                create_project(**data)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du projet :\n{e}")
                return
            self.refresh()

    def on_edit_project(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.information(self, "Modifier projet", "Veuillez sélectionner un projet à modifier.")
            return

        row = indexes[0].row()
        project = self.model._rows[row]

        data = {
            "code": project.code,
            "name": project.name,
            "owner": project.owner,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "description": project.description,
            "deliverables": project.deliverables,
            "status": project.status,
            "cir": project.cir,
            "cir_montant": project.cir_montant,
            "subvention": project.subvention,
            "subvention_montant": project.subvention_montant,
            "amortissement": project.amortissement,
            "investissement": project.investissement,
            "themes": project.themes,
            "images": project.images,
        }

        dlg = ProjectFormDialog(self, project_data=data)
        if dlg.exec() == QDialog.Accepted:
            updated = dlg.get_data()
            updated["start_date"] = parse_ym_to_date(updated.get("start_date"))
            updated["end_date"] = parse_ym_to_date(updated.get("end_date"))
            if "investissement" in updated and updated["investissement"]:
                date_obj = parse_ym_to_date(updated["investissement"].get("date"))
                updated["investissement"]["date"] = date_obj.strftime("%Y-%m") if date_obj else None

            try:
                update_project(project.id, **updated)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour du projet :\n{e}")
                return
            self.refresh()

    def on_delete_project(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.information(self, "Suppression projet", "Veuillez sélectionner un projet à supprimer.")
            return

        row = indexes[0].row()
        project = self.model._rows[row]

        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Supprimer le projet « {project.name} » ({project.code}) ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            delete_project(project.id)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression du projet :\n{e}")
            return

        self.refresh()
