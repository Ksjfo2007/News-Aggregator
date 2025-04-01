from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    topics = db.Column(db.String(500), nullable=True)
    is_kids_mode = db.Column(db.Boolean, default=False, nullable=False)
    avatar_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Reading preferences
    font_size = db.Column(db.String(20), default='medium', nullable=False)
    font_type = db.Column(db.String(50), default='system', nullable=False)
    color_scheme = db.Column(db.String(50), default='default', nullable=False)
    layout_preference = db.Column(db.String(50), default='grid', nullable=False)
    focus_mode = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    bookmarks = db.relationship('Bookmark', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    following = db.relationship('UserFollowing', foreign_keys='UserFollowing.follower_id', backref='follower', lazy=True)
    followers = db.relationship('UserFollowing', foreign_keys='UserFollowing.followed_id', backref='followed', lazy=True)
    favorite_sources = db.relationship('FavoriteSource', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_topics(self):
        return self.topics.split(',') if self.topics else []

    def set_topics(self, topics):
        self.topics = ','.join(topics) if topics else None

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_url = db.Column(db.String(500), nullable=False)
    article_title = db.Column(db.String(200), nullable=False)
    article_description = db.Column(db.Text)
    article_image = db.Column(db.String(500))
    source_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_url = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserFollowing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FavoriteSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 