import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from dotenv import load_dotenv

from app.ui.main_window import MainWindow
from app.db.repo import init_db, seed_demo_if_empty, list_projects

def ensure_media_dir() -> None:
    media_dir = Path("media")
    media_dir.mkdir(parents=True, exist_ok=True)

def create_app() -> QApplication:
    load_dotenv()
    ensure_media_dir()

    # Init DB (tables) + petit jeu de données si vide
    init_db()
    seed_demo_if_empty()

    app = QApplication([])
    app.setApplicationName(os.getenv("APP_NAME", "Gestion budgétaire"))
    return app

def main() -> None:
    app = create_app()
    win = MainWindow()
    # Info légère: nombre de projets pour vérifier la DB
    try:
        projects = list_projects()
        win.setWindowTitle(f"Gestion budgétaire — {len(projects)} projet(s)")
    except Exception:
        # en cas de souci DB, on laisse le titre par défaut
        pass

    win.resize(980, 640)
    win.setWindowState(Qt.WindowState.WindowActive)
    win.show()
    app.exec()

if __name__ == "__main__":
    main()
