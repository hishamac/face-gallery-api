# Face Gallery API

A powerful, cloud-ready Flask REST API for intelligent face recognition, clustering, and photo gallery management. Built with advanced AI algorithms, MongoDB database, and designed for seamless deployment in serverless and containerized environments.

## 🌟 Overview

Face Gallery API is a comprehensive backend service that provides intelligent face recognition capabilities for organizing photo collections. Using state-of-the-art machine learning algorithms, it automatically detects faces, groups similar faces into persons, and provides powerful management tools for photo organization.

### Key Highlights

- **🤖 Advanced AI Recognition**: Powered by `face_recognition` library with 99.38% accuracy
- **☁️ Cloud-Native Architecture**: Base64 storage system eliminates file system dependencies
- **🔄 Intelligent Clustering**: DBSCAN algorithm for automatic face grouping with manual override
- **🚀 Scalable Design**: Horizontal scaling support with stateless architecture
- **🛡️ Privacy-First**: All processing done locally, no cloud API dependencies
- **⚡ High Performance**: Optimized for speed with MongoDB indexing and caching

## ✨ Features

### 🎯 Core Face Recognition
- **Automatic Face Detection**: Real-time face detection in uploaded images using dlib's ResNet model
- **Face Encoding Generation**: 128-dimensional face embeddings for accurate comparison
- **Intelligent Clustering**: DBSCAN algorithm groups similar faces with configurable tolerance
- **Face Similarity Search**: Upload a photo to find matching faces across your entire database
- **Batch Processing**: Efficient handling of multiple image uploads simultaneously
- **Face Location Tracking**: Precise bounding box coordinates for each detected face

### 👥 Person Management
- **Smart Person Creation**: Automatically creates persons from clustered faces
- **Manual Face Assignment**: Move faces between persons with protected status
- **Person Naming & Renaming**: Custom names with persistence across re-clustering
- **Person Statistics**: Face count, image count, and creation timestamps
- **Auto-Cleanup**: Automatic deletion of empty persons when faces are reassigned
- **Thumbnail Generation**: Dynamic person thumbnails from best-quality face

### 📸 Image Management
- **Multi-Format Support**: PNG, JPG, JPEG, GIF with automatic format detection
- **Base64 Storage System**: Database-only storage for cloud deployment compatibility
- **Image Compression**: Automatic optimization while preserving face detection quality
- **Metadata Extraction**: EXIF data processing and storage for organization
- **Batch Upload**: Process multiple images with progress tracking
- **Face Overlay Data**: Detailed face locations and confidence scores

### 🗂️ Organization System
- **Album Management**: Create, edit, delete albums for event-based organization
- **Section Management**: Sub-categorize images within albums using sections
- **Hierarchical Structure**: Support for album → section → image relationships
- **Filtering & Search**: Advanced filtering by albums, sections, persons, and dates
- **Batch Assignment**: Assign multiple images to albums/sections during upload

### ⚙️ Advanced Operations
- **Re-clustering**: Re-analyze all faces while preserving manual assignments
- **Database Reset**: Complete system cleanup with confirmation safeguards
- **Statistics Dashboard**: Comprehensive analytics on collection contents
- **Confidence Scoring**: Quality metrics for face detection and matching
- **Error Recovery**: Robust error handling and data integrity checks

### 🔧 Technical Features
- **RESTful API Design**: Clean, consistent endpoint structure with proper HTTP methods
- **MongoDB Integration**: Scalable NoSQL database with optimized indexing
- **Environment Configuration**: Flexible configuration for development/production
- **CORS Support**: Cross-origin resource sharing for web client integration
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Health Checks**: System status endpoints for monitoring and load balancing

## 🛠️ Technology Stack

### Core Technologies
- **[Flask 2.3.3](https://flask.palletsprojects.com/)** - Lightweight, flexible web framework
- **[Python 3.8+](https://www.python.org/)** - Modern Python with type hints support
- **[MongoDB 4.6+](https://www.mongodb.com/)** - Document database for scalable storage
- **[PyMongo 4.6](https://pymongo.readthedocs.io/)** - Official MongoDB Python driver

### Machine Learning & AI
- **[face_recognition 1.3.0](https://github.com/ageitgey/face_recognition)** - Industry-standard face recognition
- **[dlib 19.24.1](http://dlib.net/)** - Machine learning algorithms and tools
- **[scikit-learn 1.3.2](https://scikit-learn.org/)** - Machine learning library with DBSCAN clustering
- **[NumPy 1.24.3](https://numpy.org/)** - Numerical computing for array operations

### Image Processing
- **[Pillow 10.1.0](https://python-pillow.org/)** - Image processing and manipulation
- **[OpenCV 4.8.1](https://opencv.org/)** - Computer vision and image processing
- **Base64 Encoding** - Cloud-friendly image storage system

### Development & Deployment
- **[Flask-CORS 4.0.0](https://flask-cors.readthedocs.io/)** - Cross-origin resource sharing
- **[python-dotenv 1.0.0](https://python-dotenv.readthedocs.io/)** - Environment variable management
- **[Gunicorn 21.2.0](https://gunicorn.org/)** - WSGI HTTP Server for production
- **[Werkzeug 2.3.7](https://werkzeug.palletsprojects.com/)** - WSGI utilities and debugging tools

## 📁 Project Structure

```
api/
├── app.py                    # Main Flask application with setup
├── config.py                 # Configuration management and environments
├── requirements.txt          # Python dependencies and versions
├── Dockerfile               # Container configuration for deployment
├── app.yaml                 # Google App Engine configuration
├── vm-setup.sh             # Virtual machine setup script
├── QUICK_VM_SETUP.md       # VM deployment instructions
├── gcs_helper.py           # Google Cloud Storage utilities (optional)
├── routes/                  # API route blueprints
│   ├── images.py           # Image upload and management endpoints
│   ├── persons.py          # Person management and operations
│   ├── faces.py            # Face operations and base64 serving
│   ├── albums.py           # Album CRUD operations
│   ├── sections.py         # Section management operations  
│   ├── cluster.py          # Face clustering algorithms
│   └── stats.py            # Statistics and analytics endpoints
└── __pycache__/            # Python bytecode cache (auto-generated)
    ├── app.cpython-311.pyc
    ├── config.cpython-311.pyc
    └── routes/
        ├── albums.cpython-311.pyc
        ├── cluster.cpython-311.pyc
        ├── faces.cpython-311.pyc
        ├── images.cpython-311.pyc
        ├── persons.cpython-311.pyc
        ├── sections.cpython-311.pyc
        └── stats.cpython-311.pyc
```

## 🚀 Getting Started

### Prerequisites

Before setting up the Face Gallery API, ensure you have:

- **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
- **MongoDB 4.4+** - [Install from mongodb.com](https://www.mongodb.com/try/download/community)
- **Visual Studio Build Tools** - Required for dlib compilation on Windows
- **Git** - For cloning the repository

### Quick Start

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd api
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start MongoDB**
   ```bash
   # Windows (if installed as service)
   net start MongoDB
   
   # macOS with Homebrew
   brew services start mongodb/brew/mongodb-community
   
   # Linux
   sudo systemctl start mongod
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Verify Installation**
   Navigate to `http://localhost:5000` to see the API documentation

### Development Setup

1. **Environment Configuration**
   Create a `.env` file in the api directory:
   ```env
   FLASK_ENV=development
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   MONGODB_URI=mongodb://localhost:27017
   DATABASE_NAME=face_gallery
   ```

2. **MongoDB Setup**
   The application will automatically create the necessary collections:
   - `persons` - Person entities with face associations
   - `faces` - Individual face data with embeddings
   - `images` - Image metadata and base64 data
   - `albums` - Photo album organization
   - `sections` - Sub-album categorization

3. **Test the Setup**
   ```bash
   # Check if API is running
   curl http://localhost:5000/
   
   # Check database connection
   curl http://localhost:5000/stats/
   ```

## 📚 API Documentation

### Base URL
All API requests should be made to: `http://localhost:5000`

### Response Format
All responses are in JSON format with consistent structure:
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Handling
Errors return appropriate HTTP status codes with descriptive messages:
```json
{
  "success": false,
  "error": "Descriptive error message",
  "code": 400,
  "details": "Additional context when available"
}
```

## 🛣️ API Endpoints

### 📸 Image Management

#### Upload Single Image
```http
POST /images/upload
Content-Type: multipart/form-data

Parameters:
- file: Image file (required)
- album_id: Album ID (optional)
- section_id: Section ID (optional)

Response:
{
  "success": true,
  "data": {
    "image_id": "507f1f77bcf86cd799439011",
    "faces_detected": 3,
    "persons_created": 2,
    "processing_time": 1.234
  }
}
```

#### Upload Multiple Images
```http
POST /images/upload-multiple
Content-Type: multipart/form-data

Parameters:
- files: Multiple image files (required)
- album_id: Album ID (optional)
- section_id: Section ID (optional)

Response:
{
  "success": true,
  "data": {
    "total_images": 10,
    "successful_uploads": 8,
    "failed_uploads": 2,
    "total_faces_detected": 15,
    "processing_time": 12.5
  }
}
```

#### Get All Images
```http
GET /images/

Query Parameters:
- album_id: Filter by album
- section_id: Filter by section
- person_id: Filter by person
- limit: Number of results (default: 50)
- offset: Skip number of results (default: 0)

Response:
{
  "success": true,
  "data": {
    "images": [...],
    "total": 150,
    "limit": 50,
    "offset": 0
  }
}
```

#### Get Image Details
```http
GET /images/{image_id}

Response:
{
  "success": true,
  "data": {
    "_id": "507f1f77bcf86cd799439011",
    "filename": "family_photo.jpg",
    "faces": [...],
    "persons": [...],
    "album_id": "507f1f77bcf86cd799439012",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Serve Image File
```http
GET /images/{image_id}/file

Returns: Raw image data with appropriate Content-Type header
```

#### Search by Image
```http
POST /images/search-by-image
Content-Type: multipart/form-data

Parameters:
- file: Search image file (required)
- tolerance: Similarity threshold (default: 0.6)
- limit: Max results (default: 10)

Response:
{
  "success": true,
  "data": {
    "matches": [
      {
        "person_id": "507f1f77bcf86cd799439013",
        "confidence": 0.85,
        "face_id": "507f1f77bcf86cd799439014"
      }
    ],
    "total_matches": 5
  }
}
```

### 👤 Person Management

#### Get All Persons
```http
GET /persons/

Query Parameters:
- limit: Number of results (default: 50)
- offset: Skip number of results (default: 0)
- sort: Sort order (name, created_at, face_count)

Response:
{
  "success": true,
  "data": {
    "persons": [
      {
        "_id": "507f1f77bcf86cd799439015",
        "name": "Person 1",
        "face_count": 12,
        "image_count": 8,
        "thumbnail_url": "/faces/507f1f77bcf86cd799439016"
      }
    ],
    "total": 25
  }
}
```

#### Get Person Details
```http
GET /persons/{person_id}

Response:
{
  "success": true,
  "data": {
    "_id": "507f1f77bcf86cd799439015",
    "name": "John Doe",
    "faces": [...],
    "images": [...],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z"
  }
}
```

#### Rename Person
```http
PUT /persons/{person_id}/rename
Content-Type: application/json

Body:
{
  "name": "New Name"
}

Response:
{
  "success": true,
  "data": {
    "person_id": "507f1f77bcf86cd799439015",
    "old_name": "Person 1",
    "new_name": "John Doe"
  }
}
```

### 😊 Face Operations

#### Serve Face Image
```http
GET /faces/{face_id}

Returns: Cropped face image with appropriate Content-Type header
```

#### Move Face to Existing Person
```http
PUT /faces/{face_id}/move
Content-Type: application/json

Body:
{
  "target_person_id": "507f1f77bcf86cd799439017"
}

Response:
{
  "success": true,
  "data": {
    "face_id": "507f1f77bcf86cd799439018",
    "from_person_id": "507f1f77bcf86cd799439015",
    "to_person_id": "507f1f77bcf86cd799439017",
    "is_manual_assignment": true
  }
}
```

#### Move Face to New Person
```http
PUT /faces/{face_id}/move-to-new
Content-Type: application/json

Body:
{
  "new_person_name": "Jane Doe" // optional
}

Response:
{
  "success": true,
  "data": {
    "face_id": "507f1f77bcf86cd799439018",
    "old_person_id": "507f1f77bcf86cd799439015",
    "new_person_id": "507f1f77bcf86cd799439019",
    "new_person_name": "Person 3"
  }
}
```

### 📁 Album Management

#### Get All Albums
```http
GET /albums/

Response:
{
  "success": true,
  "data": {
    "albums": [
      {
        "_id": "507f1f77bcf86cd799439020",
        "name": "Vacation 2024",
        "description": "Summer vacation photos",
        "image_count": 45,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

#### Create Album
```http
POST /albums/
Content-Type: application/json

Body:
{
  "name": "New Album",
  "description": "Album description" // optional
}

Response:
{
  "success": true,
  "data": {
    "album_id": "507f1f77bcf86cd799439021",
    "name": "New Album",
    "description": "Album description"
  }
}
```

#### Update Album
```http
PUT /albums/{album_id}
Content-Type: application/json

Body:
{
  "name": "Updated Album Name",
  "description": "Updated description"
}
```

#### Delete Album
```http
DELETE /albums/{album_id}

Response:
{
  "success": true,
  "data": {
    "deleted_album_id": "507f1f77bcf86cd799439020",
    "images_unassigned": 45
  }
}
```

### 📂 Section Management

#### Get All Sections
```http
GET /sections/
```

#### Create Section
```http
POST /sections/
Content-Type: application/json

Body:
{
  "name": "Beach Photos",
  "description": "Photos from the beach"
}
```

#### Update Section
```http
PUT /sections/{section_id}
```

#### Delete Section
```http
DELETE /sections/{section_id}
```

### 🔄 Clustering & Intelligence

#### Trigger Face Clustering
```http
GET /cluster/

Query Parameters:
- tolerance: Face matching tolerance (default: 0.6)
- preserve_manual: Preserve manual assignments (default: true)

Response:
{
  "success": true,
  "data": {
    "faces_processed": 150,
    "persons_created": 25,
    "persons_merged": 5,
    "manual_assignments_preserved": 12,
    "processing_time": 8.5
  }
}
```

### 📊 Statistics & System

#### Get System Statistics
```http
GET /stats/

Response:
{
  "status": "success",
  "data": {
    "total_persons": 187,
    "total_images": 1250,
    "total_faces": 2800,
    "total_albums": 12,
    "total_sections": 8,
    "images_with_faces": 1100,
    "images_without_faces": 150,
    "manual_face_assignments": 45,
    "gallery_stats": {
      "face_coverage": 88.0,
      "avg_faces_per_image": 2.5,
      "avg_faces_per_person": 15.0
    }
  },
  "message": "Statistics retrieved successfully"
}
```

#### System Reset
```http
DELETE /reset

Response:
{
  "message": "Database reset successfully"
}
```

## 🗄️ Database Schema

The Face Gallery API uses MongoDB with five main collections optimized for performance and scalability.

### Collection Indexes
```javascript
// Compound indexes for optimal query performance
db.images.createIndex({ "album_id": 1, "created_at": -1 })
db.images.createIndex({ "section_id": 1, "created_at": -1 })
db.faces.createIndex({ "person_id": 1, "created_at": -1 })
db.faces.createIndex({ "image_id": 1 })
db.persons.createIndex({ "name": "text" }) // Text search support
```

### 👤 persons Collection
Stores person entities with associated faces and metadata.

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "name": "John Doe",                    // Custom name or auto-generated
  "faces": [                             // Array of associated face IDs
    ObjectId("507f1f77bcf86cd799439012"),
    ObjectId("507f1f77bcf86cd799439013")
  ],
  "images": [                            // Array of image IDs containing this person
    ObjectId("507f1f77bcf86cd799439014"),
    ObjectId("507f1f77bcf86cd799439015")
  ],
  "created_at": ISODate("2024-01-01T00:00:00Z"),
  "updated_at": ISODate("2024-01-02T00:00:00Z")
}
```

### 😊 faces Collection
Stores individual face data with embeddings and metadata.

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  "person_id": ObjectId("507f1f77bcf86cd799439011"), // Associated person
  "image_id": ObjectId("507f1f77bcf86cd799439014"),  // Source image
  "embedding": [                         // 128-dimensional face encoding
    -0.12345, 0.67890, -0.24680, ...
  ],
  "face_location": {                     // Face bounding box coordinates
    "top": 100,
    "right": 200,
    "bottom": 180,
    "left": 120
  },
  "cropped_face_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABg...",
  "cropped_face_filename": "face_507f1f77bcf86cd799439012.jpg",
  "is_manual_assignment": false,         // Whether manually moved by user
  "created_at": ISODate("2024-01-01T00:00:00Z")
}
```

### 📸 images Collection
Stores image metadata and base64 data for cloud deployment.

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439014"),
  "filename": "family_vacation.jpg",     // Original filename
  "original_image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABg...",
  "mime_type": "image/jpeg",             // MIME type for proper serving
  "faces": [                             // Array of detected face IDs
    ObjectId("507f1f77bcf86cd799439012"),
    ObjectId("507f1f77bcf86cd799439013")
  ],
  "persons": [                           // Array of person IDs in this image
    ObjectId("507f1f77bcf86cd799439011"),
    ObjectId("507f1f77bcf86cd799439016")
  ],
  "album_id": ObjectId("507f1f77bcf86cd799439017"),    // Optional album assignment
  "section_id": ObjectId("507f1f77bcf86cd799439018"),   // Optional section assignment
  "created_at": ISODate("2024-01-01T00:00:00Z")
}
```

### 📁 albums Collection
Organizes images into albums for event-based grouping.

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439017"),
  "name": "Summer Vacation 2024",        // Album name
  "description": "Our amazing summer trip to Europe", // Optional description
  "created_at": ISODate("2024-01-01T00:00:00Z"),
  "updated_at": ISODate("2024-01-05T00:00:00Z")
}
```

### 📂 sections Collection
Provides sub-categorization within albums or standalone.

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439018"),
  "name": "Beach Day",                   // Section name
  "description": "Photos from our day at the beach", // Optional description
  "created_at": ISODate("2024-01-01T00:00:00Z"),
  "updated_at": ISODate("2024-01-03T00:00:00Z")
}
```

### 📊 Database Relationships

```mermaid
erDiagram
    PERSONS ||--o{ FACES : "has many"
    IMAGES ||--o{ FACES : "contains"
    ALBUMS ||--o{ IMAGES : "organizes"
    SECTIONS ||--o{ IMAGES : "categorizes"
    ALBUMS ||--o{ SECTIONS : "contains"
    
    PERSONS {
        ObjectId _id PK
        string name
        array faces FK
        array images FK
        int face_count
        date created_at
    }
    
    FACES {
        ObjectId _id PK
        ObjectId person_id FK
        ObjectId image_id FK
        array embedding
        object face_location
        string cropped_face_base64
        boolean is_manual_assignment
        date created_at
    }
    
    IMAGES {
        ObjectId _id PK
        string filename
        string original_image_base64
        array faces FK
        array persons FK
        ObjectId album_id FK
        ObjectId section_id FK
        date created_at
    }
    
    ALBUMS {
        ObjectId _id PK
        string name
        string description
        int image_count
        date created_at
    }
    
    SECTIONS {
        ObjectId _id PK
        string name
        ObjectId album_id FK
        int image_count
        date created_at
    }
```

### 🔍 Query Patterns

Common query patterns optimized by the database design:

```javascript
// Find all images in an album
db.images.find({ "album_id": ObjectId("...") })
  .sort({ "created_at": -1 })
  .limit(50)

// Find all faces for a person
db.faces.find({ "person_id": ObjectId("...") })
  .sort({ "is_primary": -1, "quality_score": -1 })

// Search persons by name
db.persons.find({ $text: { $search: "john doe" } })

// Get statistics
db.images.aggregate([
  { $group: { _id: null, 
              total: { $sum: 1 },
              with_faces: { $sum: { $cond: [{ $gt: ["$face_count", 0] }, 1, 0] } }
            }}
])

// Find similar faces using embedding similarity (application level)
// Note: MongoDB does not have native vector similarity search
// This would be implemented in the Python application layer
```

### 🚀 Performance Considerations

- **Denormalized Counts**: Face counts and image counts stored redundantly for fast access
- **Compound Indexes**: Multi-field indexes for common query patterns
- **Base64 Storage**: Eliminates file system I/O for better containerization
- **Selective Field Loading**: Only load required fields for list views
- **Connection Pooling**: MongoDB connection pooling for concurrent requests
- **Memory Management**: Efficient face embedding storage and comparison

## ⚙️ Configuration

The Face Gallery API supports flexible environment-based configuration for different deployment scenarios.

### Environment Variables

Create a `.env` file in the api directory:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=True
HOST=0.0.0.0
PORT=5000

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=face_gallery

# Alternative MongoDB Atlas Configuration
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
# DATABASE_NAME=face_gallery_prod

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216  # 16MB in bytes
ALLOWED_EXTENSIONS=png,jpg,jpeg,gif,webp

# Face Recognition Parameters
FACE_RECOGNITION_TOLERANCE=0.6        # Lower = more strict matching
DBSCAN_EPS=0.6                       # Clustering density parameter
DBSCAN_MIN_SAMPLES=1                 # Minimum samples per cluster
FACE_DETECTION_MODEL=hog             # hog (faster) or cnn (more accurate)
FACE_CROP_PADDING=0.1                # Padding around detected faces (10%)

# Image Processing
IMAGE_MAX_DIMENSION=1920             # Max width/height for processing
IMAGE_QUALITY=85                     # JPEG compression quality (1-100)
THUMBNAIL_SIZE=200                   # Thumbnail dimensions in pixels

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://yourdomain.com
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization

# Logging Configuration
LOG_LEVEL=INFO                       # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Configuration Classes

The API uses different configuration classes for different environments:

```python
# config.py structure
class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'face_gallery')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'
    CORS_ORIGINS = ['http://localhost:5173', 'http://localhost:3000']

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_NAME = 'face_gallery_test'
    WTF_CSRF_ENABLED = False
```

### Face Recognition Parameters

Fine-tune face recognition accuracy and performance:

```python
# Face detection and recognition settings
FACE_RECOGNITION_SETTINGS = {
    'tolerance': 0.6,              # Face matching tolerance (0.0-1.0)
    'model': 'hog',                # Detection model: 'hog' or 'cnn'
    'num_jitters': 1,              # Face encoding iterations
    'face_crop_padding': 0.1,      # Crop padding percentage
}

# Clustering algorithm parameters
CLUSTERING_SETTINGS = {
    'eps': 0.6,                    # DBSCAN epsilon parameter
    'min_samples': 1,              # Minimum samples per cluster
    'metric': 'euclidean',         # Distance metric
    'algorithm': 'auto',           # Algorithm selection
}
```

### Storage Configuration

The API uses base64 storage for cloud compatibility:

```python
# Storage settings
STORAGE_SETTINGS = {
    'use_base64': True,            # Store images as base64 in database
    'compress_images': True,       # Compress images before storage
    'max_dimension': 1920,         # Maximum image dimension
    'jpeg_quality': 85,            # JPEG compression quality
    'thumbnail_size': 200,         # Thumbnail dimensions
}
```

## 🚀 Deployment

### Local Development

1. **Start MongoDB**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   
   # Or using local installation
   mongod --dbpath /path/to/your/db
   ```

2. **Run Development Server**
   ```bash
   # With auto-reload
   python app.py
   
   # Or using Flask CLI
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run --host=0.0.0.0 --port=5000
   ```

### Production Deployment

#### Using Gunicorn (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# With configuration file
gunicorn -c gunicorn.conf.py app:app
```

Create `gunicorn.conf.py`:
```python
import multiprocessing
import os

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"
```

#### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install system dependencies for dlib and OpenCV
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/stats/ || exit 1

# Run application
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
```

Build and run Docker container:
```bash
# Build image
docker build -t face-gallery-api .

# Run container
docker run -d \
  -p 5000:5000 \
  -e MONGODB_URI=mongodb://host.docker.internal:27017 \
  -e FLASK_ENV=production \
  --name face-gallery-api \
  face-gallery-api
```

#### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017
      - DATABASE_NAME=face_gallery
      - FLASK_ENV=production
    depends_on:
      - mongodb
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init:/docker-entrypoint-initdb.d
    restart: unless-stopped
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - api
    restart: unless-stopped

volumes:
  mongodb_data:
```

#### Cloud Deployment Options

##### Google Cloud Platform (App Engine)

Create `app.yaml`:
```yaml
runtime: python311
service: face-gallery-api

env_variables:
  MONGODB_URI: "mongodb+srv://username:password@cluster.mongodb.net/"
  DATABASE_NAME: "face_gallery_prod"
  FLASK_ENV: "production"
  SECRET_KEY: "your-production-secret-key"

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6

resources:
  cpu: 2
  memory_gb: 4

handlers:
- url: /.*
  script: auto
```

Deploy:
```bash
gcloud app deploy app.yaml
```

##### AWS Elastic Beanstalk

Create `.ebextensions/python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
  aws:elasticbeanstalk:application:environment:
    MONGODB_URI: "your-mongodb-connection-string"
    FLASK_ENV: "production"
    SECRET_KEY: "your-production-secret-key"
```

##### Heroku

Create `Procfile`:
```
web: gunicorn app:app
```

Create `runtime.txt`:
```
python-3.11.0
```

Deploy:
```bash
heroku create face-gallery-api
heroku addons:create mongolab:sandbox
git push heroku main
```

##### DigitalOcean App Platform

Create `.do/app.yaml`:
```yaml
name: face-gallery-api
services:
- name: api
  source_dir: /
  github:
    repo: your-username/face-gallery-api
    branch: main
  run_command: gunicorn app:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  env:
  - key: MONGODB_URI
    value: "your-mongodb-connection-string"
  - key: FLASK_ENV
    value: "production"
  - key: SECRET_KEY
    value: "your-production-secret-key"
```

### Performance Optimization

#### MongoDB Optimization

```javascript
// Create optimal indexes for common queries
db.images.createIndex({ "album_id": 1, "created_at": -1 })
db.images.createIndex({ "section_id": 1, "created_at": -1 })
db.faces.createIndex({ "person_id": 1, "created_at": -1 })
db.faces.createIndex({ "image_id": 1 })
db.persons.createIndex({ "name": "text" })

// Enable MongoDB profiling
db.setProfilingLevel(1, { slowms: 100 })
```

#### Application Performance

```python
# Connection pooling configuration
from pymongo import MongoClient
client = MongoClient(
    MONGODB_URI,
    maxPoolSize=20,
    minPoolSize=5,
    maxIdleTimeMS=30000,
    serverSelectionTimeoutMS=5000,
    socketTimeoutMS=20000
)
```

#### Nginx Configuration

```nginx
upstream face_gallery_api {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;  # Multiple instances
}

server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 20M;
    client_body_timeout 300s;

    location / {
        proxy_pass http://face_gallery_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /images/ {
        proxy_pass http://face_gallery_api;
        proxy_cache_valid 200 1h;
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

## 🔧 Development

### Development Environment Setup

1. **Python Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate (Windows)
   venv\Scripts\activate
   
   # Activate (macOS/Linux)
   source venv/bin/activate
   
   # Install development dependencies
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8 mypy
   ```

2. **MongoDB Setup**
   ```bash
   # Using Docker for development
   docker run -d -p 27017:27017 --name mongodb-dev mongo:latest
   
   # Or install locally
   # macOS: brew install mongodb-community
   # Ubuntu: apt install mongodb
   # Windows: Download from mongodb.com
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### Code Quality Tools

#### Linting and Formatting

```bash
# Format code with Black
black app.py routes/

# Lint with Flake8
flake8 app.py routes/

# Type checking with MyPy
mypy app.py
```

#### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=routes --cov-report=html

# Run specific test file
pytest tests/test_images.py

# Run with verbose output
pytest -v
```

Create `pytest.ini`:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

#### Pre-commit Hooks

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.11
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
```

### API Testing

#### Manual Testing with cURL

```bash
# Test image upload
curl -X POST -F "file=@test_image.jpg" http://localhost:5000/images/upload

# Test face search
curl -X POST -F "file=@search_face.jpg" -F "tolerance=0.6" \
  http://localhost:5000/images/search-by-image

# Test person renaming
curl -X PUT -H "Content-Type: application/json" \
  -d '{"name": "John Doe"}' \
  http://localhost:5000/persons/507f1f77bcf86cd799439011/rename

# Test statistics
curl http://localhost:5000/stats/
```

#### Testing with Python Requests

```python
import requests

# Upload image
with open('test_image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/images/upload',
        files={'file': f}
    )
    print(response.json())

# Search by image
with open('search_face.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/images/search-by-image',
        files={'file': f},
        data={'tolerance': 0.6}
    )
    print(response.json())
```

### Debugging

#### Flask Debug Mode

```python
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,  # Enable debug mode
        use_reloader=True,  # Auto-reload on changes
        use_debugger=True   # Enable debugger
    )
```

#### Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler(
        'face_gallery.log', 
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Performance Profiling

#### Profile API Endpoints

```python
from werkzeug.middleware.profiler import ProfilerMiddleware
from werkzeug.serving import WSGIRequestHandler

# Enable profiling middleware
if app.debug:
    app.wsgi_app = ProfilerMiddleware(
        app.wsgi_app, 
        restrictions=[30]  # Show top 30 functions
    )

# Custom request handler
class ProfilingRequestHandler(WSGIRequestHandler):
    def make_environ(self):
        environ = WSGIRequestHandler.make_environ(self)
        environ['wsgi.multiprocess'] = True
        return environ
```

#### Memory Usage Monitoring

```python
import psutil
import gc

@app.route('/debug/memory')
def memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss / 1024 / 1024,  # MB
        'vms': memory_info.vms / 1024 / 1024,  # MB
        'gc_objects': len(gc.get_objects()),
        'gc_stats': gc.get_stats()
    }
```

## 🐛 Error Handling

The API implements comprehensive error handling for robustness and debugging.

### Error Response Format

All errors return consistent JSON responses:

```json
{
  "success": false,
  "error": "Descriptive error message",
  "error_type": "ValidationError",
  "code": 400,
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_123456789"
}
```

### Error Categories

#### File Upload Errors

```python
# Invalid file format
{
  "error": "File format not supported. Allowed formats: PNG, JPG, JPEG, GIF",
  "error_type": "FileValidationError",
  "code": 400
}

# File size exceeded
{
  "error": "File size exceeds maximum limit of 16MB",
  "error_type": "FileSizeError", 
  "code": 413
}

# No faces detected
{
  "error": "No faces detected in the uploaded image",
  "error_type": "FaceDetectionError",
  "code": 422
}
```

#### Database Errors

```python
# Connection failure
{
  "error": "Database connection failed",
  "error_type": "DatabaseConnectionError",
  "code": 503
}

# Document not found
{
  "error": "Person not found with ID: 507f1f77bcf86cd799439011",
  "error_type": "DocumentNotFoundError",
  "code": 404
}

# Invalid ObjectId
{
  "error": "Invalid ObjectId format",
  "error_type": "ValidationError",
  "code": 400
}
```

#### Face Recognition Errors

```python
# Face recognition failure
{
  "error": "Face encoding generation failed",
  "error_type": "FaceRecognitionError",
  "code": 500
}

# Clustering error
{
  "error": "Face clustering algorithm failed",
  "error_type": "ClusteringError",
  "code": 500
}
```

### Global Error Handler

```python
from flask import Flask, jsonify
import traceback

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'code': 400
    }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'code': 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'code': 500
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the full traceback
    app.logger.error(f'Unhandled exception: {str(e)}\n{traceback.format_exc()}')
    
    return jsonify({
        'success': False,
        'error': 'An unexpected error occurred',
        'code': 500
    }), 500
```

## 🔐 Security

### Input Validation

```python
from werkzeug.utils import secure_filename
import re

def validate_file(file):
    if not file:
        raise ValueError("No file provided")
    
    if file.filename == '':
        raise ValueError("No file selected")
    
    # Secure filename
    filename = secure_filename(file.filename)
    
    # Validate file extension
    if not allowed_file(filename):
        raise ValueError(f"File type not allowed: {filename}")
    
    # Validate file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)     # Reset position
    
    if size > app.config['MAX_CONTENT_LENGTH']:
        raise ValueError("File size too large")
    
    return filename

def validate_objectid(id_string):
    from bson import ObjectId
    from bson.errors import InvalidId
    
    try:
        return ObjectId(id_string)
    except InvalidId:
        raise ValueError("Invalid ObjectId format")
```

### Authentication (Future Enhancement)

```python
from functools import wraps
from flask_jwt_extended import JWTManager, verify_jwt_in_request

# JWT configuration
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        verify_jwt_in_request()
        return f(*args, **kwargs)
    return decorated

```

### Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

@app.route('/images/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_image():
    # Implementation
    pass
```

## 🤝 Contributing

We welcome contributions to the Face Gallery API! Please follow these guidelines:

### Getting Started

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/face-gallery-api.git
   cd face-gallery-api
   ```

2. **Create Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

### Development Guidelines

- **Code Style**: Follow PEP 8 and use Black formatter
- **Type Hints**: Add type hints for all functions
- **Documentation**: Update docstrings and README
- **Tests**: Add tests for new features
- **Commit Messages**: Use conventional commit format

### Testing

```bash
# Run all tests
pytest

# Run specific test category
pytest -m unit
pytest -m integration

# Run with coverage
pytest --cov=routes --cov-report=html
```

### Submitting Changes

1. **Run Quality Checks**
   ```bash
   black .
   flake8 .
   mypy .
   pytest
   ```

2. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```

3. **Push and Create PR**
   ```bash
   git push origin feature/amazing-feature
   ```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **face_recognition** - Adam Geitgey for the excellent face recognition library
- **dlib** - Davis King for the machine learning algorithms
- **Flask Community** - For the robust web framework
- **MongoDB Team** - For the scalable database platform
- **scikit-learn** - For machine learning algorithms and clustering
- **OpenCV Community** - For computer vision tools
- **Open Source Community** - For all the amazing libraries and contributions

---

## 📞 Support

For support and questions:

1. **Documentation**: Check this README and inline code documentation
2. **Issues**: Create an issue on GitHub for bugs or feature requests
3. **Discussions**: Use GitHub Discussions for general questions
4. **Email**: Contact the development team

### Common Issues

- **dlib Installation**: Install Visual Studio Build Tools on Windows
- **MongoDB Connection**: Ensure MongoDB is running and accessible
- **Memory Usage**: Monitor memory usage during face processing
- **Performance**: Consider using SSD storage for better I/O performance

**Happy coding! 🚀✨**