# reset_db.py

from app.db.models import Base, engine

if __name__ == "__main__":
    print("⚠️  ATTENTION : Suppression et recréation de toutes les tables !")
    confirm = input("Es-tu sûr ? (o/n) : ")
    if confirm.lower() == "o":
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ Base de données réinitialisée.")
    else:
        print("❌ Opération annulée.")
