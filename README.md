# Fansat - Face Recognition API

A comprehensive Flask-based REST API for intelligent face detection, clustering, and gallery management using MongoDB and advanced face recognition algorithms with base64 storage for cloud-friendly deployment.

## Features

### Core Face Recognition
- **Image Upload & Processing**: Single and batch image upload with automatic face detection
- **Base64 Image Storage**: Cloud-friendly storage system using base64 encoding in MongoDB
- **Intelligent Face Clustering**: Advanced face recognition using `face_recognition` library with configurable tolerance
- **Smart Person Assignment**: Automatic face-to-person matching during upload with intelligent clustering
- **Face Search by Image**: Upload an image to find similar faces in your database
- **Manual Face Management**: Move faces between persons or create new persons when clustering is incorrect

### Person & Image Management  
- **Person Management**: Create, rename, and manage detected persons
- **Protected Manual Assignments**: Manual face assignments are preserved during re-clustering
- **Image Gallery**: Comprehensive image management with face detection information
- **Cropped Face Storage**: Automatic extraction and base64 storage of detected faces
- **Face Location Tracking**: Precise face coordinates and bounding boxes

### Organization & Structure
- **Album Management**: Create and organize images into albums
- **Section Management**: Group images by sections for better organization
- **Filtering & Search**: Filter images by albums, sections, and search terms
- **Hierarchical Organization**: Support for album-section-image hierarchy

### Advanced Features
- **Re-clustering**: Re-run clustering while preserving manual assignments
- **Database Statistics**: Comprehensive stats on persons, faces, images, albums, and sections
- **Auto-cleanup**: Automatic deletion of empty persons when faces are moved
- **Database Reset**: Complete database cleanup functionality
- **Image Compression**: Automatic image optimization for faster processing

### Technical Features
- **Base64 Storage System**: Database-only storage eliminating file system dependencies
- **Cloud-Ready Architecture**: Serverless and containerization friendly
- **Flexible Configuration**: Environment-based configuration with development/production modes
- **MongoDB Integration**: Robust MongoDB connection with fallback mechanisms
- **Error Handling**: Comprehensive error handling and validation
- **CORS Support**: Cross-origin resource sharing for web client integration
- **File Validation**: Support for PNG, JPG, JPEG, GIF formats with size limits
- **Upload Progress Tracking**: Real-time upload progress with timeout handling

## Prerequisites

- Python 3.8+
- MongoDB (running on localhost:27017)
- Visual Studio Build Tools (for dlib compilation on Windows)

## Installation

1. Navigate to the api directory:
   ```bash
   cd api
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Make sure MongoDB is running on localhost:27017

2. Start the Flask application:
   ```bash
   python app.py
   ```

3. The API will be available at `http://localhost:5000`

## API Endpoints

### Image Management
- **POST** `/images/upload` - Upload single image with optional album/section assignment
- **POST** `/images/upload-multiple` - Upload multiple images in batch with progress tracking
- **GET** `/images/` - Get all images with filtering by album/section
- **GET** `/images/<image_id>` - Get detailed information about specific image
- **GET** `/images/<image_id>/file` - Serve uploaded images from base64 data
- **POST** `/images/search-by-image` - Search for similar faces using uploaded image

### Person Management
- **GET** `/persons/` - Get all persons with thumbnails and statistics
- **GET** `/persons/<person_id>` - Get detailed person information with all faces
- **PUT** `/persons/<person_id>/rename` - Rename a person

### Face Management
- **GET** `/faces/<face_id>` - Serve cropped face images from base64 data
- **PUT** `/faces/<face_id>/move` - Move face to existing person (manual assignment)
- **PUT** `/faces/<face_id>/move-to-new` - Move face to new person

### Clustering & Intelligence
- **GET** `/cluster/` - Re-cluster faces (preserves manual assignments)

### Album Management
- **GET** `/albums/` - Get all albums with image counts
- **POST** `/albums/` - Create new album
- **GET** `/albums/<album_id>` - Get specific album details
- **PUT** `/albums/<album_id>` - Update album name and description
- **DELETE** `/albums/<album_id>` - Delete album

### Section Management
- **GET** `/sections/` - Get all sections with image counts
- **POST** `/sections/` - Create new section
- **GET** `/sections/<section_id>` - Get specific section details
- **PUT** `/sections/<section_id>` - Update section name and description
- **DELETE** `/sections/<section_id>` - Delete section

### Statistics & System
- **GET** `/stats/` - Get comprehensive database statistics
- **GET** `/` - API information and available endpoints
- **DELETE** `/reset` - Reset entire database (use with caution)

## Database Structure

The application uses MongoDB with five main collections:

### persons
```json
{
  "_id": ObjectId,
  "name": "Person 1",
  "faces": [face_id1, face_id2, ...],
  "images": [image_id1, image_id2, ...],
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### images
```json
{
  "_id": ObjectId,
  "original_image_base64": "base64-encoded-image-data",
  "filename": "image1.jpg",
  "mime_type": "image/jpeg",
  "faces": [face_id1, face_id2, ...],
  "persons": [person_id1, person_id2, ...],
  "album_id": "album_id",
  "section_id": "section_id",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### faces
```json
{
  "_id": ObjectId,
  "embedding": [128-dimensional face encoding],
  "person_id": ObjectId,
  "image_id": ObjectId,
  "face_location": {
    "top": 100,
    "right": 200,
    "bottom": 180,
    "left": 120
  },
  "cropped_face_base64": "base64-encoded-face-data",
  "cropped_face_filename": "cropped_face.jpg",
  "is_manual_assignment": false,
  "created_at": "ISO8601"
}
```

### albums
```json
{
  "_id": ObjectId,
  "name": "Vacation 2024",
  "description": "Summer vacation photos",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### sections
```json
{
  "_id": ObjectId,
  "name": "Beach Photos",
  "description": "Photos from the beach",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

## Configuration

The API supports environment-based configuration through `.env` files:

### Environment Variables
```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key
DEBUG=True

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=face_gallery

# File Upload Configuration (Legacy - Files now stored as base64 in database)
MAX_CONTENT_LENGTH=16777216  # 16MB
ALLOWED_EXTENSIONS=png,jpg,jpeg,gif

# Face Recognition Configuration
FACE_RECOGNITION_TOLERANCE=0.6
DBSCAN_EPS=0.6
DBSCAN_MIN_SAMPLES=1

# CORS Configuration
CORS_ORIGINS=*
```

### Configuration Classes
- **Development**: Debug mode, local MongoDB, relaxed CORS
- **Production**: Optimized for deployment, secure settings
- **Testing**: Test database isolation, mock settings

### Storage System
- **Database-Only Storage**: All images and faces stored as base64 in MongoDB
- **Cloud-Friendly Architecture**: No file system dependencies for serverless deployment
- **Automatic Compression**: Images optimized for storage while maintaining quality

### Face Recognition Parameters
- **Tolerance**: Face matching sensitivity (0.6 default, lower = stricter)
- **DBSCAN**: Clustering algorithm parameters for grouping
- **Padding**: Face crop padding (10% of face dimensions)
- **Image Compression**: Automatic resizing (max 1920px) with quality optimization

## Error Handling

The API includes comprehensive error handling for:

### File Upload Errors
- Invalid file types and formats
- Missing files in requests
- File size limit exceeded
- Corrupted or unreadable images

### Database Errors
- MongoDB connection failures with fallback
- Invalid ObjectId formats
- Document not found scenarios
- Constraint violations and data integrity

### Face Recognition Errors
- No faces detected in images
- Face detection algorithm failures
- Invalid face embeddings
- Clustering algorithm errors

### Validation Errors
- Invalid request parameters
- Missing required fields
- Malformed JSON payloads
- Invalid album/section references

### Response Format
```json
{
  "error": "Descriptive error message",
  "details": "Additional context when available",
  "code": 400
}
```

## Development

### Development Server
```bash
export FLASK_ENV=development  # Linux/macOS
set FLASK_ENV=development     # Windows
python app.py
```

### API Testing
```bash
# Upload image
curl -X POST -F "file=@image.jpg" http://localhost:5000/images/upload

# Upload with album/section
curl -X POST -F "file=@image.jpg" -F "album_id=ALBUM_ID" http://localhost:5000/images/upload

# Upload multiple files with progress tracking
curl -X POST -F "files=@image1.jpg" -F "files=@image2.jpg" http://localhost:5000/images/upload-multiple

# Search by image
curl -X POST -F "file=@search.jpg" -F "tolerance=0.6" http://localhost:5000/images/search-by-image

# Get image via base64 endpoint
curl http://localhost:5000/images/IMAGE_ID/file

# Get cropped face via base64 endpoint  
curl http://localhost:5000/faces/FACE_ID
```

### Development Features
- **Hot Reload**: Automatic server restart on code changes
- **Debug Mode**: Detailed error traces and debugging information
- **MongoDB Atlas Support**: Cloud database integration with SSL
- **Local Development**: Fallback to local MongoDB instance
- **Logging**: Comprehensive logging for debugging and monitoring

### Code Structure
```
api/
├── app.py              # Main Flask application
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── routes/            # API route blueprints
│   ├── images.py      # Image upload and base64 management
│   ├── persons.py     # Person management
│   ├── faces.py       # Face operations and base64 serving
│   ├── albums.py      # Album management
│   ├── sections.py    # Section management
│   ├── cluster.py     # Clustering algorithms
│   └── stats.py       # Statistics and analytics
```

## Notes

### Face Recognition Technology
- **Algorithm**: Uses `face_recognition` library (based on dlib's ResNet model)
- **Accuracy**: 99.38% accuracy on Labeled Faces in the Wild benchmark
- **Speed**: ~1-2 seconds per image on modern hardware
- **Clustering**: Intelligent face matching with configurable tolerance
- **Robustness**: Handles varying lighting, angles, and image quality

### Performance Considerations
- **Memory Usage**: ~100MB RAM per 1000 face encodings
- **Storage**: Database-only storage with base64 compression
- **Database**: MongoDB with proper indexing for fast queries
- **Scalability**: Horizontal scaling support with database replication
- **Upload Optimization**: Image compression and progress tracking

### Security & Privacy
- **Data Protection**: All face data stored locally in database, no cloud processing
- **Access Control**: CORS configuration for secure web access
- **File Validation**: Strict file type and size validation with 16MB limit
- **Error Sanitization**: Secure error messages without data leakage
- **Upload Timeouts**: Configurable timeouts to prevent resource exhaustion

### Cloud Deployment Benefits
- **Serverless Compatible**: No file system dependencies
- **Container Ready**: Database-only storage eliminates volume mounts
- **Auto Scaling**: Stateless architecture supports horizontal scaling
- **Platform Agnostic**: Works on any platform with MongoDB support

### Best Practices
- **Image Quality**: Higher resolution images yield better face detection
- **Batch Processing**: Use multiple upload for processing many images
- **Manual Corrections**: Review and correct clustering results for accuracy
- **Regular Clustering**: Re-run clustering after adding many new faces
- **Backup Strategy**: Regular MongoDB backups recommended for production

### Known Limitations
- **Face Angle**: Works best with frontal face views (±30 degrees)
- **Image Size**: Very small faces (<50px) may not be detected reliably
- **Lighting**: Extreme lighting conditions may affect detection accuracy
- **Clustering**: May require manual correction for similar-looking people