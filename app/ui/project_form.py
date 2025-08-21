from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QDateEdit,
    QComboBox, QCheckBox, QPushButton, QDialogButtonBox, QFileDialog,
    QLabel, QListWidget, QListWidgetItem, QMessageBox, QSpinBox, QWidget
)

from PySide6.QtCore import QDate
from PySide6.QtGui import QDoubleValidator, QIntValidator
import os

class ProjectFormDialog(QDialog):
    def __init__(self, parent=None, project_data=None):
        super().__init__(parent)
        self.setWindowTitle("Projet")
        self.project_data = project_data  # None pour création, dict pour modif
        self.image_paths = []
        self._build()
        self._wire()
        if project_data:
            self._populate(project_data)
        self._apply_visibility()
        self.investments = []
        self.invest_container = QVBoxLayout()


    # ---------------------- UI BUILD ---------------------- #
    def _build(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Champs de base
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("EX: PRJ-2025-001")
        self.name_edit = QLineEdit()
        self.themes_edit = QLineEdit()
        self.details_edit = QTextEdit()

        # Dates: affichage et logique MM/yyyy uniquement
        self.start_date = self._make_month_year_dateedit()
        self.end_date = self._make_month_year_dateedit()

        self.deliverables_edit = QTextEdit()
        self.owner_edit = QLineEdit()

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Futur", "En cours", "Terminé"])



        self.sub_check = QCheckBox("Subvention")
        self.sub_amount = QLineEdit()
        self.sub_amount.setPlaceholderText("Montant en €")
        self.sub_amount.setValidator(QDoubleValidator(0.0, 1e12, 2, self))

        # Investissement + champs conditionnels
        self.invest_check = QCheckBox("Investissement")
        self.invest_amount = QLineEdit()
        self.invest_amount.setPlaceholderText("Montant en €")
        self.invest_amount.setValidator(QDoubleValidator(0.0, 1e12, 2, self))

        self.invest_date = self._make_month_year_dateedit()

        self.invest_amort_months = QSpinBox()
        self.invest_amort_months.setRange(1, 1200)
        self.invest_amort_months.setValue(36)
        self.invest_amort_months.setSuffix(" mois")
        self.invest_amort_months.setToolTip("Durée d'amortissement de l'investissement en mois")

        # Images
        self.image_btn = QPushButton("Ajouter image(s)")
        self.image_btn.clicked.connect(self._add_images)
        self.image_list = QListWidget()

        self.btn_add_invest = QPushButton("Ajouter un investissement")
        self.investments = []

        form.addRow("Investissements", self.btn_add_invest)
        self.btn_add_invest.clicked.connect(self._add_invest_row)
        self.invest_container = QVBoxLayout()
        form.addRow(self._make_invest_container())

        self.team_layout = QVBoxLayout()
        self.team_rows = {}

        btn_add_role = QPushButton("Ajouter un rôle")
        btn_add_role.clicked.connect(self._add_team_role)

        form.addRow(QLabel("Équipe"))
        form.addRow(btn_add_role)
        form.addRow(self._make_team_container())

        def _make_team_container(self):
            widget = QWidget()
            widget.setLayout(self.team_layout)
            return widget

        def _add_team_role(self):
            from PySide6.QtWidgets import QInputDialog
            role, ok = QInputDialog.getText(self, "Rôle", "Nom du rôle :")
            if ok and role:
                self._create_team_row(role)

        def _create_team_row(self, role, value=0):
            row = QWidget()
            layout = QHBoxLayout(row)

            label = QLabel(role)
            spin = QSpinBox()
            spin.setRange(0, 100)
            spin.setValue(value)

            btn_del = QPushButton("X")
            btn_del.setMaximumWidth(30)
            btn_del.clicked.connect(lambda: self._remove_team_row(role, row))

            layout.addWidget(label)
            layout.addWidget(spin)
            layout.addWidget(btn_del)

            self.team_layout.addWidget(row)
            self.team_rows[role] = spin

        def _remove_team_row(self, role, row):
            self.team_layout.removeWidget(row)
            row.deleteLater()
            del self.team_rows[role]

        def _collect_team(self):
            return {role: spin.value() for role, spin in self.team_rows.items()}


        def _make_invest_container(self):
            widget = QWidget()
            widget.setLayout(self.invest_container)
            return widget

        def _add_invest_row(self, preset=None):
            row = QWidget()
            layout = QHBoxLayout(row)

            montant = QLineEdit()
            montant.setPlaceholderText("Montant €")
            montant.setValidator(QDoubleValidator(0.0, 1e12, 2, self))

            date = self._make_month_year_dateedit()

            duree = QSpinBox()
            duree.setRange(1, 1200)
            duree.setSuffix(" mois")
            duree.setValue(36)

            btn_del = QPushButton("Suppr")
            btn_del.setMaximumWidth(60)
            btn_del.clicked.connect(lambda: self._remove_invest_row(row))

            layout.addWidget(montant)
            layout.addWidget(date)
            layout.addWidget(duree)
            layout.addWidget(btn_del)

            self.investments.append((row, montant, date, duree))
            self.invest_container.addWidget(row)

            if preset:
                if "montant" in preset:
                    montant.setText(str(preset["montant"]))
                if "date" in preset:
                    self._set_month_year(date, preset["date"])
                if "duree_mois" in preset:
                    duree.setValue(preset["duree_mois"])

        def _remove_invest_row(self, row):
            for item in self.investments:
                if item[0] == row:
                    self.invest_container.removeWidget(row)
                    row.deleteLater()
                    self.investments.remove(item)
                    break

        def _collect_investissements(self):
            out = []
            for _, montant, date, duree in self.investments:
                m = self._to_float_or_none(montant.text())
                d = self._qdateedit_to_ym_string(date)
                mo = duree.value()
                if m and d:
                    out.append({"montant": m, "date": d, "duree_mois": mo})
            return out

        # Placement des champs
        form.addRow("Code projet", self.code_edit)
        form.addRow("Nom projet", self.name_edit)
        form.addRow("Thèmes (séparés par virgules)", self.themes_edit)
        form.addRow("Détails projet", self.details_edit)
        form.addRow("Date début (MM/AAAA)", self.start_date)
        form.addRow("Date fin (MM/AAAA)", self.end_date)
        form.addRow("Livrables", self.deliverables_edit)
        form.addRow("Chef de projet", self.owner_edit)
        form.addRow("État", self.status_combo)

        form.addRow("Montant CIR", self.cir_amount)
        form.addRow("Subvention", self.sub_check)
        form.addRow("Montant subvention", self.sub_amount)

        form.addRow("Investissement", self.invest_check)
        form.addRow("Montant investissement", self.invest_amount)
        form.addRow("Date d'achat (MM/AAAA)", self.invest_date)
        form.addRow("Durée amortissement (mois)", self.invest_amort_months)

        form.addRow(QLabel("Images"))
        form.addRow(self.image_btn)
        form.addRow(self.image_list)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _make_invest_container(self):
        widget = QWidget()
        widget.setLayout(self.invest_container)
        return widget

    def _make_month_year_dateedit(self) -> QDateEdit:
        de = QDateEdit()
        de.setDisplayFormat("MM/yyyy")
        de.setCalendarPopup(True)
        # Permettre le vide (affichage) et éviter le jour
        de.setSpecialValueText("")
        de.setDateRange(QDate(1900, 1, 1), QDate(7999, 12, 31))
        # Valeur par défaut vide à l'affichage
        de.setDate(QDate(1900, 1, 1))
        de.lineEdit().clear()
        de.setToolTip("Saisir mois/année uniquement")
        return de

    # ---------------------- SIGNALS ---------------------- #
    def _wire(self):
        self.sub_check.toggled.connect(self._apply_visibility)
        self.invest_check.toggled.connect(self._apply_visibility)

    def _apply_visibility(self):
        # Champs montants activés uniquement si coché

        self.sub_amount.setEnabled(self.sub_check.isChecked())
        if not self.sub_check.isChecked():
            self.sub_amount.clear()

        inv_on = self.invest_check.isChecked()
        for w in (self.invest_amount, self.invest_date, self.invest_amort_months):
            w.setEnabled(inv_on)
        if not inv_on:
            self.invest_amount.clear()
            self.invest_date.lineEdit().clear()
            self.invest_amort_months.setValue(36)

    # ---------------------- HELPERS ---------------------- #
    def _qdateedit_is_empty(self, de: QDateEdit) -> bool:
        return de.lineEdit().text().strip() == ""

    def _qdateedit_to_ym_string(self, de: QDateEdit):
        """Retourne 'YYYY-MM' ou None si vide."""
        if self._qdateedit_is_empty(de):
            return None
        # Force le jour au 1er du mois
        txt = de.lineEdit().text().strip()
        # Tente le parsing direct MM/yyyy
        qd = QDate.fromString(txt, "MM/yyyy")
        if not qd.isValid():
            return None
        return f"{qd.year():04d}-{qd.month():02d}"

    def _set_month_year(self, de: QDateEdit, value: str):
        if not value:
            de.lineEdit().clear()
            return
        # Supporte 'yyyy-MM' et 'yyyy-MM-dd'
        qd = QDate.fromString(value, "yyyy-MM")
        if not qd.isValid():
            qd = QDate.fromString(value, "yyyy-MM-dd")
        if qd.isValid():
            de.setDate(qd)
        else:
            de.lineEdit().setText("")

    # ---------------------- DATA BINDING ---------------------- #
    def _add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Choisir des images", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        for f in files:
            if f not in self.image_paths:
                self.image_paths.append(f)
                self.image_list.addItem(QListWidgetItem(os.path.basename(f)))

    def _populate(self, data: dict):
        self.code_edit.setText(data.get("code", ""))
        self.name_edit.setText(data.get("name", ""))
        self.themes_edit.setText(", ".join(data.get("themes", [])))
        self.details_edit.setPlainText(data.get("description", ""))

        if data.get("start_date"):
            self._set_month_year(self.start_date, data["start_date"])
        if data.get("end_date"):
            self._set_month_year(self.end_date, data["end_date"])

        self.deliverables_edit.setPlainText(data.get("deliverables", ""))
        self.owner_edit.setText(data.get("owner", ""))
        self.status_combo.setCurrentText(data.get("status", "Futur"))

        # Subvention
        self.sub_check.setChecked(bool(data.get("subvention", False)))
        self.sub_amount.setText(str(data.get("subvention_montant", "")))
        for inv in data.get("investissement", []):
            self._add_invest_row(inv)

        for role, val in data.get("team", {}).items():
            self._create_team_row(role, val)

        # Investissement structuré
        import json

        inv_raw = getattr(self.project_data, "investissement", None)
        inv = {}
        if inv_raw:
            try:
                if isinstance(inv_raw, str):
                    inv = json.loads(inv_raw) or {}
                elif isinstance(inv_raw, dict):
                    inv = inv_raw
            except Exception:
                inv = {}

        if inv.get("montant") is not None:
            self.invest_amount.setText(str(inv.get("montant")))

    def _add_invest_row(self, preset=None):
        row = QWidget()
        layout = QHBoxLayout(row)

        montant = QLineEdit()
        montant.setPlaceholderText("Montant €")
        montant.setValidator(QDoubleValidator(0.0, 1e12, 2, self))

        date = self._make_month_year_dateedit()

        duree = QSpinBox()
        duree.setRange(1, 1200)
        duree.setSuffix(" mois")
        duree.setValue(36)

        btn_del = QPushButton("Suppr")
        btn_del.setMaximumWidth(60)
        btn_del.clicked.connect(lambda: self._remove_invest_row(row))

        layout.addWidget(montant)
        layout.addWidget(date)
        layout.addWidget(duree)
        layout.addWidget(btn_del)

        self.investments.append((row, montant, date, duree))
        self.invest_container.addWidget(row)

        if preset:
            if "montant" in preset:
                montant.setText(str(preset["montant"]))
            if "date" in preset:
                self._set_month_year(date, preset["date"])
            if "duree_mois" in preset:
                duree.setValue(preset["duree_mois"])


    def _remove_invest_row(self, row):
        for item in self.investments:
            if item[0] == row:
                self.invest_container.removeWidget(row)
                row.deleteLater()
                self.investments.remove(item)
                break

    def get_data(self) -> dict:
        data = {
            "code": self.code_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "themes": [t.strip() for t in self.themes_edit.text().split(",") if t.strip()],
            "description": self.details_edit.toPlainText().strip(),
            "start_date": self._qdateedit_to_ym_string(self.start_date),  # 'YYYY-MM' ou None
            "end_date": self._qdateedit_to_ym_string(self.end_date),      # 'YYYY-MM' ou None
            "deliverables": self.deliverables_edit.toPlainText().strip(),
            "owner": self.owner_edit.text().strip(),
            "status": self.status_combo.currentText(),
            "subvention": self.sub_check.isChecked(),
            
        }

        # Montants conditionnels
        if self.sub_check.isChecked():
            data["subvention_montant"] = self._to_float_or_none(self.sub_amount.text())

        if self.invest_check.isChecked():
            data["investissement"] = {
                "montant": self._to_float_or_none(self.invest_amount.text()),
                "date": self._qdateedit_to_ym_string(self.invest_date),  # 'YYYY-MM'
                "duree_mois": int(self.invest_amort_months.value()),
            }
        data["investissement"] = self._collect_investissements()
        data["images"] = self.image_paths[:]
        data["team"] = self._collect_team()

        return data

    def _to_float_or_none(self, s: str):
        s = (s or "").replace(" ", "").replace(",", ".")
        try:
            return float(s) if s != "" else None
        except ValueError:
            return None

    # ---------------------- VALIDATION ---------------------- #
    def validate(self) -> bool:
        # Obligatoires
        if not self.code_edit.text().strip() or not self.name_edit.text().strip():
            QMessageBox.warning(self, "Champs requis", "Code et nom du projet sont obligatoires.")
            return False

        # Dates cohérentes (si présentes)
        sd = self._qdateedit_to_ym_string(self.start_date)
        ed = self._qdateedit_to_ym_string(self.end_date)
        if sd and ed and sd > ed:
            QMessageBox.warning(self, "Dates incohérentes", "La date de début doit être antérieure ou égale à la date de fin.")
            return False

        # Montants si cases cochées
        if self.sub_check.isChecked():
            v = self._to_float_or_none(self.sub_amount.text())
            if v is None or v < 0:
                QMessageBox.warning(self, "Montant subvention", "Veuillez saisir un montant de subvention valide (≥ 0).")
                return False

        if self.invest_check.isChecked():
            mv = self._to_float_or_none(self.invest_amount.text())
            if mv is None or mv <= 0:
                QMessageBox.warning(self, "Investissement", "Veuillez saisir un montant d'investissement valide (> 0).")
                return False
            if self._qdateedit_is_empty(self.invest_date):
                QMessageBox.warning(self, "Investissement", "Veuillez saisir la date d'achat (MM/AAAA).")
                return False
            if int(self.invest_amort_months.value()) <= 0:
                QMessageBox.warning(self, "Investissement", "Veuillez saisir une durée d'amortissement en mois (> 0).")
                return False

        return True

    def accept(self):
        if not self.validate():
            return
        super().accept()
