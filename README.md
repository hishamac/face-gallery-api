# Face Clustering Flask API

A Flask-based REST API for face detection, clustering, and gallery management using MongoDB.

## Features

- Upload images with automatic face detection
- Face clustering using DBSCAN algorithm
- Person and face management
- Gallery view with organized persons
- Image serving endpoint
- Database statistics and reset functionality

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

### Upload Image
- **POST** `/upload`
- Upload an image file for face detection
- Supported formats: PNG, JPG, JPEG, GIF
- Returns: File info and number of faces detected

### Cluster Faces
- **GET** `/cluster`
- Performs face clustering using DBSCAN algorithm
- Groups similar faces into persons
- Returns: Clustering results and number of unique persons

### Get Gallery
- **GET** `/gallery`
- Retrieves all persons with their associated faces and images
- Returns: Organized gallery data

### Get Image
- **GET** `/images/<filename>`
- Serves uploaded images
- Returns: Image file

### Get Statistics
- **GET** `/stats`
- Returns database statistics (total persons, images, faces)

### Reset Database
- **DELETE** `/reset`
- Clears all data from the database
- Use with caution!

## Database Structure

The application uses MongoDB with three collections:

### persons
```json
{
  "_id": ObjectId,
  "name": "Person 1",
  "faces": [face_id1, face_id2, ...],
  "images": [image_id1, image_id2, ...]
}
```

### images
```json
{
  "_id": ObjectId,
  "file_path": "uploads/image1.jpg",
  "filename": "image1.jpg",
  "faces": [face_id1, face_id2, ...],
  "persons": [person_id1, person_id2]
}
```

### faces
```json
{
  "_id": ObjectId,
  "embedding": [...],
  "person_id": ObjectId,
  "image_id": ObjectId
}
```

## Configuration

- MongoDB URL: `mongodb://localhost:27017`
- Database name: `face_gallery`
- Upload folder: `uploads/`
- Supported file types: PNG, JPG, JPEG, GIF
- CORS: Enabled for all origins

## Error Handling

The API includes comprehensive error handling for:
- Invalid file types
- Missing files
- Database connection issues
- Face detection errors
- Clustering failures

## Development

For development with auto-reload:
```bash
export FLASK_ENV=development  # Linux/macOS
set FLASK_ENV=development     # Windows
python app.py
```

## Notes

- Face detection uses the `face_recognition` library
- Clustering parameters (eps=0.6, min_samples=1) can be adjusted in the code
- Images are stored locally in the `uploads/` folder
- Face embeddings are stored as arrays in MongoDB