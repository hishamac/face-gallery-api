from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from config import config
import os

# Import blueprints
from routes.images import images_bp
from routes.albums import albums_bp
from routes.sections import sections_bp
from routes.persons import persons_bp
from routes.faces import faces_bp
from routes.cluster import cluster_bp
from routes.stats import stats_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get configuration
env = os.getenv('FLASK_ENV', 'development')
app_config = config.get(env, config['default'])

# Configure Flask app
app.config['SECRET_KEY'] = app_config.SECRET_KEY
app.config['DEBUG'] = app_config.DEBUG
app.config['MAX_CONTENT_LENGTH'] = app_config.MAX_CONTENT_LENGTH

# Configure CORS
CORS(app, origins=app_config.CORS_ORIGINS)

# MongoDB connection
try:
    # First try with standard connection
    client = MongoClient(app_config.MONGODB_URI)
    # Test the connection
    client.admin.command('ismaster')
    print(f"✅ Connected to MongoDB: {app_config.MONGODB_URI}")
except Exception as e:
    print(f"⚠️ Standard connection failed: {e}")
    try:
        # Try with SSL settings for MongoDB Atlas
        client = MongoClient(
            app_config.MONGODB_URI,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        client.admin.command('ismaster')
        print(f"✅ Connected to MongoDB with relaxed SSL: {app_config.MONGODB_URI}")
    except Exception as e2:
        print(f"❌ MongoDB connection failed: {e2}")
        print("Falling back to local MongoDB...")
        client = MongoClient("mongodb://localhost:27017")

db = client[app_config.DATABASE_NAME]

# Store database reference in app context
app.db = db

# Ensure upload folder exists
UPLOAD_FOLDER = app_config.UPLOAD_FOLDER
FACES_FOLDER = app_config.FACES_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(FACES_FOLDER):
    os.makedirs(FACES_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FACES_FOLDER'] = FACES_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = app_config.ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Store allowed_file function in app context
app.allowed_file = allowed_file

# Register blueprints with proper URL prefixes
app.register_blueprint(images_bp, url_prefix='/images')
app.register_blueprint(albums_bp, url_prefix='/albums')
app.register_blueprint(sections_bp, url_prefix='/sections')
app.register_blueprint(persons_bp, url_prefix='/persons')
app.register_blueprint(faces_bp, url_prefix='/faces')
app.register_blueprint(cluster_bp, url_prefix='/cluster')
app.register_blueprint(stats_bp, url_prefix='/stats')

@app.route('/')
def index():
    return jsonify({
        "message": "Face Clustering API",
        "version": "2.0",
        "endpoints": {
            "images": "/images",
            "albums": "/albums", 
            "sections": "/sections",
            "persons": "/persons",
            "faces": "/faces",
            "cluster": "/cluster",
            "stats": "/stats"
        }
    })

@app.route('/reset', methods=['DELETE'])
def reset_database():
    """Reset the entire database (use with caution!)"""
    try:
        db.persons.delete_many({})
        db.images.delete_many({})
        db.faces.delete_many({})
        db.albums.delete_many({})
        db.sections.delete_many({})
        
        # Optionally, remove uploaded files
        # for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        #     os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        return jsonify({"message": "Database reset successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# For Vercel deployment, the app needs to be available at module level
# The app instance is already created above and will be used by Vercel

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)