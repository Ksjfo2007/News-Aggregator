from flask import Flask
from extensions import db
from models import User, Bookmark, Comment, UserFollowing, FavoriteSource
import os

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def migrate_database():
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all tables successfully!")
        
        # Create all tables with new schema
        db.create_all()
        print("Created all tables with new schema!")
        
        # Verify tables and columns
        inspector = db.inspect(db.engine)
        for table_name in inspector.get_table_names():
            print(f"\nTable: {table_name}")
            for column in inspector.get_columns(table_name):
                print(f"- Column: {column['name']} ({column['type']})")

if __name__ == '__main__':
    # Make sure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Delete the database file if it exists
    db_path = 'news.db'
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Deleted existing database file: {db_path}")
        except Exception as e:
            print(f"Error deleting database file: {e}")
    
    migrate_database()
    print("\nDatabase migration completed successfully!") 