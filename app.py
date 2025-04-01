from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from newsapi import NewsApiClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from extensions import db
from models import User, Bookmark, Comment, UserFollowing, FavoriteSource
from werkzeug.utils import secure_filename
import json

load_dotenv()

# Ensure we're in the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///news.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(script_dir, 'static/uploads/avatars')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('newsapp.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('News App startup')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db.init_app(app)
newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))

AVAILABLE_TOPICS = [
    'Artificial Intelligence', 'Technology', 'Science', 'Health', 'Sports',
    'Politics', 'Business', 'Entertainment', 'Environment', 'Education',
    'World News', 'Technology', 'Science', 'Health', 'Sports'
]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_ai_articles(topics=None, kids_mode=False):
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    if topics:
        query = ' OR '.join(topics)
    else:
        query = 'artificial intelligence OR machine learning OR deep learning'
    
    articles = newsapi.get_everything(
        q=query,
        from_param=from_date,
        language='en',
        sort_by='relevancy'
    )
    
    if kids_mode:
        # Filter out articles with potentially inappropriate content
        articles['articles'] = [
            article for article in articles['articles']
            if not any(keyword in article.get('title', '').lower() or 
                      keyword in article.get('description', '').lower()
                      for keyword in ['violence', 'crime', 'death', 'war', 'terror'])
        ]
    
    return articles['articles']

@app.route('/')
@login_required
def index():
    topics = current_user.get_topics() if current_user.is_authenticated else None
    kids_mode = current_user.is_kids_mode if current_user.is_authenticated else False
    articles = get_ai_articles(topics, kids_mode)
    return render_template('index.html', articles=articles, topics=AVAILABLE_TOPICS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        
        user = User(
            username=request.form['username'],
            email=request.form['email']
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('select_topics'))
    return render_template('signup.html')

@app.route('/select-topics', methods=['GET', 'POST'])
@login_required
def select_topics():
    if request.method == 'POST':
        selected_topics = request.form.getlist('topics')
        current_user.set_topics(selected_topics)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('select_topics.html', topics=AVAILABLE_TOPICS)

@app.route('/toggle-kids-mode')
@login_required
def toggle_kids_mode():
    current_user.is_kids_mode = not current_user.is_kids_mode
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/update-topics', methods=['POST'])
@login_required
def update_topics():
    selected_topics = request.form.getlist('topics')
    current_user.set_topics(selected_topics)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/article/<int:index>')
def article_detail(index):
    articles = get_ai_articles()
    if 0 <= index < len(articles):
        article = articles[index]
        return render_template('article_detail.html', article=article)
    return "Article not found", 404

@app.route('/account')
@login_required
def account():
    return render_template('account.html', topics=AVAILABLE_TOPICS)

@app.route('/update-account', methods=['POST'])
@login_required
def update_account():
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{current_user.id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.avatar_url = f"/static/uploads/avatars/{filename}"
    
    current_user.full_name = request.form.get('full_name')
    current_user.username = request.form.get('username')
    current_user.email = request.form.get('email')
    current_user.is_kids_mode = 'kids_mode' in request.form
    
    if request.form.get('new_password'):
        if request.form.get('new_password') == request.form.get('confirm_password'):
            current_user.set_password(request.form.get('new_password'))
        else:
            flash('Passwords do not match')
            return redirect(url_for('account'))
    
    selected_topics = request.form.getlist('topics')
    current_user.set_topics(selected_topics)
    
    db.session.commit()
    flash('Account updated successfully')
    return redirect(url_for('account'))

@app.route('/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{current_user.id}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_user.avatar_url = f"/static/uploads/avatars/{filename}"
        db.session.commit()
        return jsonify({'success': True, 'avatar_url': current_user.avatar_url})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/bookmark', methods=['POST'])
@login_required
def bookmark_article():
    data = request.get_json()
    article = data.get('article')
    
    if not article:
        return jsonify({'error': 'No article data provided'}), 400
    
    bookmark = Bookmark(
        user_id=current_user.id,
        article_url=article.get('url'),
        article_title=article.get('title'),
        article_description=article.get('description'),
        article_image=article.get('urlToImage'),
        source_name=article.get('source', {}).get('name')
    )
    
    db.session.add(bookmark)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Article bookmarked'})

@app.route('/unbookmark', methods=['POST'])
@login_required
def unbookmark_article():
    article_url = request.json.get('article_url')
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, article_url=article_url).first()
    
    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Article unbookmarked'})
    
    return jsonify({'error': 'Bookmark not found'}), 404

@app.route('/bookmarks')
@login_required
def bookmarks():
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.created_at.desc()).all()
    return render_template('bookmarks.html', bookmarks=bookmarks)

@app.route('/comment', methods=['POST'])
@login_required
def add_comment():
    data = request.get_json()
    article_url = data.get('article_url')
    content = data.get('content')
    
    if not article_url or not content:
        return jsonify({'error': 'Missing required fields'}), 400
    
    comment = Comment(
        user_id=current_user.id,
        article_url=article_url,
        content=content
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'username': current_user.username,
            'avatar_url': current_user.avatar_url
        }
    })

@app.route('/comments/<article_url>')
def get_comments(article_url):
    comments = Comment.query.filter_by(article_url=article_url).order_by(Comment.created_at.desc()).all()
    return jsonify([{
        'id': comment.id,
        'content': comment.content,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'username': comment.user.username,
        'avatar_url': comment.user.avatar_url
    } for comment in comments])

@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot follow yourself'}), 400
    
    following = UserFollowing.query.filter_by(
        follower_id=current_user.id,
        followed_id=user_id
    ).first()
    
    if following:
        db.session.delete(following)
        action = 'unfollowed'
    else:
        following = UserFollowing(follower_id=current_user.id, followed_id=user_id)
        db.session.add(following)
        action = 'followed'
    
    db.session.commit()
    return jsonify({'success': True, 'action': action})

@app.route('/favorite-source', methods=['POST'])
@login_required
def add_favorite_source():
    source_name = request.json.get('source_name')
    if not source_name:
        return jsonify({'error': 'Source name required'}), 400
    
    favorite = FavoriteSource(user_id=current_user.id, source_name=source_name)
    db.session.add(favorite)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Source added to favorites'})

@app.route('/remove-favorite-source', methods=['POST'])
@login_required
def remove_favorite_source():
    source_name = request.json.get('source_name')
    if not source_name:
        return jsonify({'error': 'Source name required'}), 400
    
    favorite = FavoriteSource.query.filter_by(
        user_id=current_user.id,
        source_name=source_name
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Source removed from favorites'})
    
    return jsonify({'error': 'Source not found'}), 404

@app.route('/update-preferences', methods=['POST'])
@login_required
def update_preferences():
    data = request.get_json()
    
    current_user.font_size = data.get('font_size', current_user.font_size)
    current_user.font_type = data.get('font_type', current_user.font_type)
    current_user.color_scheme = data.get('color_scheme', current_user.color_scheme)
    current_user.layout_preference = data.get('layout_preference', current_user.layout_preference)
    current_user.focus_mode = data.get('focus_mode', current_user.focus_mode)
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Preferences updated'})

@app.route('/discover')
@login_required
def discover():
    # Get filter parameters
    category = request.args.get('category')
    time_range = request.args.get('timeRange', '7')
    sort_by = request.args.get('sortBy', 'relevancy')
    
    # Get trending topics and popular sources
    trending_topics = ['AI', 'Technology', 'Science', 'Health', 'Business', 'Politics', 'Entertainment']
    popular_sources = ['Reuters', 'AP News', 'Bloomberg', 'The Verge', 'TechCrunch', 'BBC News', 'CNN']
    
    # Get articles from different categories
    articles_by_category = {}
    for topic in trending_topics:
        if not category or category == topic:
            articles = get_ai_articles([topic], current_user.is_kids_mode)
            # Apply time range filter
            from_date = (datetime.now() - timedelta(days=int(time_range))).strftime('%Y-%m-%d')
            articles = [article for article in articles if article['publishedAt'].startswith(from_date)]
            # Apply sorting
            if sort_by == 'popularity':
                articles.sort(key=lambda x: x.get('popularity', 0), reverse=True)
            elif sort_by == 'publishedAt':
                articles.sort(key=lambda x: x['publishedAt'], reverse=True)
            articles_by_category[topic] = articles[:5]  # Limit to 5 articles per category
    
    return render_template('discover.html',
                         trending_topics=trending_topics,
                         popular_sources=popular_sources,
                         articles_by_category=articles_by_category,
                         active_category=category)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/api/articles')
@login_required
def get_more_articles():
    category = request.args.get('category')
    time_range = request.args.get('timeRange', '7')
    sort_by = request.args.get('sortBy', 'relevancy')
    
    articles = get_ai_articles([category] if category else None, current_user.is_kids_mode)
    
    # Apply time range filter
    from_date = (datetime.now() - timedelta(days=int(time_range))).strftime('%Y-%m-%d')
    articles = [article for article in articles if article['publishedAt'].startswith(from_date)]
    
    # Apply sorting
    if sort_by == 'popularity':
        articles.sort(key=lambda x: x.get('popularity', 0), reverse=True)
    elif sort_by == 'publishedAt':
        articles.sort(key=lambda x: x['publishedAt'], reverse=True)
    
    return jsonify({
        'articles': articles,
        'has_more': False  # Since we're using the News API, we don't have pagination
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 