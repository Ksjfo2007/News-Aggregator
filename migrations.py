from app import app, db
from models import User
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Drop existing table and recreate with all columns
        db.drop_all()
        db.create_all()
        print("Database tables recreated successfully!")

if __name__ == '__main__':
    migrate() 