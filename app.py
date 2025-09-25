import json
import os
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import face_recognition
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
from sklearn.cluster import DBSCAN
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from config import config
from PIL import Image
import datetime

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
persons_col = db["persons"]
faces_col = db["faces"]
images_col = db["images"]

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

def crop_and_save_face(image_array, face_location, face_index, image_filename):
    """Crop face from image and save it as a separate file"""
    try:
        from PIL import Image as PILImage
        
        # face_location is in format (top, right, bottom, left)
        top, right, bottom, left = face_location
        
        # Convert numpy array to PIL Image
        pil_image = PILImage.fromarray(image_array)
        
        # Add padding around the face (10% of face dimensions)
        face_height = bottom - top
        face_width = right - left
        padding_h = int(face_height * 0.1)
        padding_w = int(face_width * 0.1)
        
        # Calculate crop coordinates with padding
        crop_top = max(0, top - padding_h)
        crop_bottom = min(pil_image.height, bottom + padding_h)
        crop_left = max(0, left - padding_w)
        crop_right = min(pil_image.width, right + padding_w)
        
        # Crop the face
        face_image = pil_image.crop((crop_left, crop_top, crop_right, crop_bottom))
        
        # Generate face filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        face_filename = f"{os.path.splitext(image_filename)[0]}_face_{face_index}_{timestamp}.jpg"
        face_path = os.path.join(app.config['FACES_FOLDER'], face_filename)
        
        # Save cropped face
        face_image.save(face_path, 'JPEG', quality=90)
        
        return face_path, face_filename
    except Exception as e:
        print(f"Error cropping face: {e}")
        return None, None

def serialize_doc(doc):
    """Convert ObjectId to string for JSON serialization"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, list):
                result[key] = [str(item) if isinstance(item, ObjectId) else item for item in value]
            else:
                result[key] = value
        return result
    return doc

@app.route('/')
def index():
    return jsonify({"message": "Face Clustering API", "version": "1.0"})

@app.route('/upload', methods=['POST'])
def upload_image():
    """Upload a single image for face detection and clustering"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Check if file is allowed
        if file and allowed_file(file.filename):
            return process_single_image(file)
        
        return jsonify({"error": "Invalid file type"}), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload-multiple', methods=['POST'])
def upload_multiple_images():
    """Upload multiple images for face detection and clustering"""
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({"error": "No files part"}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "No files selected"}), 400
        
        results = []
        total_faces = 0
        successful_uploads = 0
        errors = []
        
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    result = process_single_image(file)
                    if isinstance(result, tuple):  # Error response
                        errors.append(f"{file.filename}: {result[0]['error']}")
                    else:
                        # result is already a dictionary, not a Response object
                        results.append({
                            "filename": file.filename,
                            "faces_detected": result.get("faces_detected", 0),
                            "persons_assigned": result.get("persons_assigned", 0),
                            "image_id": result.get("image_id")
                        })
                        total_faces += result.get("faces_detected", 0)
                        successful_uploads += 1
                except Exception as e:
                    errors.append(f"{file.filename}: {str(e)}")
            else:
                errors.append(f"{file.filename}: Invalid file type")
        
        return jsonify({
            "message": f"Multiple upload completed",
            "successful_uploads": successful_uploads,
            "total_files": len(files),
            "total_faces_detected": total_faces,
            "results": results,
            "errors": errors if errors else None
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_single_image(file):
    """Helper function to process a single image"""
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Load image and detect faces
    image_data = face_recognition.load_image_file(file_path)
    face_locations = face_recognition.face_locations(image_data)
    face_encodings = face_recognition.face_encodings(image_data, face_locations)
    
    # Save image document
    image_doc = {
        "file_path": file_path,
        "filename": filename,
        "faces": [],
        "persons": []
    }
    image_result = images_col.insert_one(image_doc)
    image_id = image_result.inserted_id
    
    # Save faces with cropped images and intelligent person assignment
    face_ids = []
    assigned_persons = set()
    face_person_assignments = []  # Keep track of face-person assignments in order
    
    # Get all existing face encodings for comparison
    existing_faces = list(faces_col.find({}, {"embedding": 1, "person_id": 1}))
    known_encodings = []
    known_person_ids = []
    
    for face in existing_faces:
        if face.get("embedding") and face.get("person_id"):
            known_encodings.append(np.array(face["embedding"]))
            known_person_ids.append(face["person_id"])
    
    print(f"Found {len(known_encodings)} existing faces for comparison")
    
    for i, (encoding, location) in enumerate(zip(face_encodings, face_locations)):
        person_id = None
        
        # First check against existing faces using face_recognition library
        if known_encodings:
            matches = face_recognition.compare_faces(
                known_encodings, 
                encoding, 
                tolerance=app_config.FACE_RECOGNITION_TOLERANCE
            )
            
            if any(matches):
                # Found a match - get the person_id of the first match
                match_index = matches.index(True)
                person_id = known_person_ids[match_index]
                print(f"Face {i} matched to existing person: {person_id}")
        
        # If no match found, create new person
        if person_id is None:
            person_count = persons_col.count_documents({}) + 1
            person_doc = {
                "name": f"Person {person_count}",
                "faces": [],
                "images": []
            }
            person_result = persons_col.insert_one(person_doc)
            person_id = person_result.inserted_id
            print(f"Face {i} assigned to new person: {person_id}")
        
        # Crop and save the face
        face_path, face_filename = crop_and_save_face(image_data, location, i, filename)
        
        face_doc = {
            "embedding": encoding.tolist(),
            "person_id": person_id,  # Now assigned immediately
            "image_id": image_id,
            "face_location": {
                "top": int(location[0]),
                "right": int(location[1]),
                "bottom": int(location[2]),
                "left": int(location[3])
            },
            "cropped_face_path": face_path,
            "cropped_face_filename": face_filename
        }
        face_result = faces_col.insert_one(face_doc)
        face_ids.append(face_result.inserted_id)
        assigned_persons.add(person_id)
        face_person_assignments.append({"face_id": str(face_result.inserted_id), "person_id": str(person_id)})
        
        # Update person document with this face and image
        persons_col.update_one(
            {"_id": person_id},
            {
                "$addToSet": {
                    "faces": face_result.inserted_id,
                    "images": image_id
                }
            }
        )
        
        # Add the new encoding to known_encodings for comparing within this batch
        known_encodings.append(encoding)
        known_person_ids.append(person_id)
    
    # Update image with face IDs and assigned persons
    images_col.update_one(
        {"_id": image_id},
        {"$set": {
            "faces": face_ids,
            "persons": list(assigned_persons)
        }}
    )
    
    # Handle response for both cases (with and without faces)
    if len(face_encodings) > 0:
        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "filename": filename,
            "faces_detected": len(face_encodings),
            "persons_assigned": len(assigned_persons),
            "image_id": str(image_id),
            "face_assignments": face_person_assignments,
            "note": "Faces detected and assigned using intelligent matching. Use /cluster endpoint to re-cluster if needed."
        }
    else:
        return {
            "message": "File uploaded successfully (no faces detected)",
            "file_path": file_path,
            "filename": filename,
            "faces_detected": 0,
            "persons_assigned": 0,
            "image_id": str(image_id),
            "note": "Image saved but no faces detected. This is normal for landscape photos, objects, etc."
        }

@app.route('/cluster-preview', methods=['POST'])
def preview_clustering():
    """
    Preview clustering results with different parameters without saving
    """
    try:
        data = request.get_json()
        eps = float(data.get('eps', app_config.DBSCAN_EPS))
        min_samples = int(data.get('min_samples', app_config.DBSCAN_MIN_SAMPLES))
        
        # Get all faces from database
        faces = list(faces_col.find())
        
        if not faces:
            return jsonify({"message": "No faces to preview"})
        
        # Extract embeddings
        embeddings = [np.array(face["embedding"]) for face in faces]
        
        # Perform clustering with custom parameters
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean").fit(embeddings)
        
        # Analyze results
        unique_labels = set(int(label) for label in clustering.labels_)  # Convert to Python int
        cluster_stats = {}
        for label in unique_labels:
            cluster_stats[int(label)] = sum(1 for l in clustering.labels_ if int(l) == label)
        
        return jsonify({
            "preview_results": {
                "total_faces": len(faces),
                "unique_clusters": len(unique_labels) - (1 if -1 in unique_labels else 0),
                "outliers": cluster_stats.get(-1, 0),
                "cluster_sizes": {k: v for k, v in cluster_stats.items() if k != -1},
                "parameters": {"eps": eps, "min_samples": min_samples}
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cluster', methods=['GET'])
def cluster_faces():
    """
    Re-cluster faces using face_recognition logic, preserving manual assignments.
    Only automatically assigned faces will be re-clustered.
    """
    try:
        # Get all faces that are NOT manually assigned
        faces = list(faces_col.find({
            "$or": [
                {"is_manual_assignment": {"$exists": False}},  # Old faces without the field
                {"is_manual_assignment": False},               # Explicitly not manual
                {"is_manual_assignment": {"$ne": True}}        # Not manually assigned
            ]
        }))
        
        manually_assigned_count = faces_col.count_documents({"is_manual_assignment": True})
        
        if not faces:
            return jsonify({
                "message": "No faces to cluster (all faces are manually assigned)",
                "manually_assigned_faces": manually_assigned_count
            })
        
        print(f"Clustering {len(faces)} faces (preserving {manually_assigned_count} manually assigned faces)")
        
        # Extract embeddings
        embeddings = []
        face_ids = []
        
        for face in faces:
            if face.get("embedding"):
                embeddings.append(np.array(face["embedding"]))
                face_ids.append(face["_id"])
        
        if len(embeddings) < 2:
            return jsonify({"message": "Need at least 2 faces for clustering"})
        
        # Use the same face_recognition logic as upload (not DBSCAN)
        print("Re-clustering using face_recognition.compare_faces (same as upload)")
        
        # PRESERVE EXISTING PERSONS - only reassign faces, don't delete persons
        print("Preserving existing persons and their custom names...")
        
        # Get all existing persons with their faces
        existing_persons = list(persons_col.find())
        existing_person_encodings = {}
        
        # Build a map of existing persons to their face encodings
        for person in existing_persons:
            person_id = person["_id"]
            person_faces = list(faces_col.find({"person_id": person_id}))
            if person_faces:
                # Use the first face of each person as the representative encoding
                representative_encoding = np.array(person_faces[0]["embedding"])
                existing_person_encodings[str(person_id)] = {
                    "encoding": representative_encoding,
                    "person_id": person_id,
                    "name": person.get("name", f"Person {len(existing_person_encodings) + 1}")
                }
        
        print(f"Found {len(existing_person_encodings)} existing persons to preserve")
        
        # Clear face assignments only for non-manually assigned faces
        faces_col.update_many({
            "$or": [
                {"is_manual_assignment": {"$exists": False}},  # Old faces without the field
                {"is_manual_assignment": False},               # Explicitly not manual
                {"is_manual_assignment": {"$ne": True}}        # Not manually assigned
            ]
        }, {"$unset": {"person_id": ""}})
        
        # Process faces one by one using face_recognition logic
        processed_faces = []
        new_person_count = len(existing_person_encodings)
        
        for i, face in enumerate(faces):
            encoding = np.array(face["embedding"])
            person_id = None
            
            # First, try to match against existing persons
            if existing_person_encodings:
                existing_encodings = [data["encoding"] for data in existing_person_encodings.values()]
                existing_person_ids = [data["person_id"] for data in existing_person_encodings.values()]
                
                matches = face_recognition.compare_faces(
                    existing_encodings, 
                    encoding, 
                    tolerance=app_config.FACE_RECOGNITION_TOLERANCE
                )
                
                if any(matches):
                    # Found match with existing person
                    match_index = matches.index(True)
                    person_id = existing_person_ids[match_index]
                    print(f"Face {i} matched to existing person: {person_id}")
            
            # If no match with existing persons, try matching with newly processed faces
            if person_id is None and processed_faces:
                processed_encodings = [np.array(f["embedding"]) for f in processed_faces]
                processed_person_ids = [f["person_id"] for f in processed_faces]
                
                matches = face_recognition.compare_faces(
                    processed_encodings, 
                    encoding, 
                    tolerance=app_config.FACE_RECOGNITION_TOLERANCE
                )
                
                if any(matches):
                    # Found a match with newly processed face
                    match_index = matches.index(True)
                    person_id = processed_person_ids[match_index]
                    print(f"Face {i} matched to newly processed person: {person_id}")
            
            # If still no match found, create new person
            if person_id is None:
                new_person_count += 1
                person_doc = {
                    "name": f"Person {new_person_count}",
                    "faces": [],
                    "images": []
                }
                person_result = persons_col.insert_one(person_doc)
                person_id = person_result.inserted_id
                print(f"Face {i} assigned to new person: {person_id} (Person {new_person_count})")
            
            # Update face with person assignment
            faces_col.update_one(
                {"_id": face["_id"]},
                {"$set": {"person_id": person_id}}
            )
            
            # Track processed face
            face["person_id"] = person_id
            processed_faces.append(face)
        
        # Update person documents with face and image references
        print("Updating person documents...")
        
        # Get all unique person IDs from assigned faces
        all_person_ids = set()
        for face in faces_col.find({"person_id": {"$exists": True}}):
            if face.get("person_id"):
                all_person_ids.add(face["person_id"])
        
        for person_id in all_person_ids:
            # Get faces for this person
            person_faces = faces_col.find({"person_id": person_id})
            face_ids = []
            image_ids = set()

            for face in person_faces:
                face_ids.append(face["_id"])
                image_ids.add(face["image_id"])

            # Update person document
            persons_col.update_one(
                {"_id": person_id},
                {"$set": {
                    "faces": face_ids,
                    "images": list(image_ids)
                }}
            )        # Update image documents
        print("Updating image documents...")
        all_images = images_col.find({})
        for image in all_images:
            # Get persons in this image
            image_faces = faces_col.find({"image_id": image["_id"]})
            person_ids = set()
            
            for face in image_faces:
                if face.get("person_id"):
                    person_ids.add(face["person_id"])
            
            images_col.update_one(
                {"_id": image["_id"]},
                {"$set": {"persons": list(person_ids)}}
            )
        
        total_persons = persons_col.count_documents({})
        total_faces_assigned = faces_col.count_documents({"person_id": {"$exists": True}})
        
        return jsonify({
            "message": "Clustering completed (preserving manual assignments and person names)",
            "total_faces": len(faces),
            "total_faces_assigned": total_faces_assigned,
            "total_persons": total_persons,
            "manually_assigned_faces_preserved": manually_assigned_count,
            "existing_persons_preserved": len(existing_person_encodings),
            "new_persons_created": new_person_count - len(existing_person_encodings),
            "parameters": {
                "tolerance": app_config.FACE_RECOGNITION_TOLERANCE,
                "method": "face_recognition.compare_faces"
            }
        })
        
    except Exception as e:
        print(f"Clustering error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/images/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/faces/<filename>')
def serve_cropped_face(filename):
    """Serve cropped face images"""
    return send_from_directory(app.config['FACES_FOLDER'], filename)

@app.route('/all-images', methods=['GET'])
def get_all_images():
    """Get all uploaded images (with and without faces)"""
    try:
        images = list(images_col.find())
        
        all_images = []
        for image in images:
            # Get faces in this image (if any)
            image_faces = list(faces_col.find({"image_id": image["_id"]}))
            
            # Get persons in this image (if any)
            person_ids = image.get("persons", [])
            persons_in_image = []
            if person_ids:
                persons = list(persons_col.find({"_id": {"$in": person_ids}}))
                persons_in_image = [{"person_id": str(p["_id"]), "person_name": p.get("name", "Unknown")} for p in persons]
            
            image_data = {
                "image_id": str(image["_id"]),
                "filename": image.get("filename", ""),
                "file_path": image.get("file_path", ""),
                "faces_count": len(image_faces),
                "persons_count": len(persons_in_image),
                "persons": persons_in_image,
                "has_faces": len(image_faces) > 0,
                "upload_date": image.get("created_at", "Unknown")
            }
            all_images.append(image_data)
        
        # Sort by upload date (newest first)
        all_images.sort(key=lambda x: x.get("upload_date", ""), reverse=True)
        
        return jsonify({
            "images": all_images,
            "total_images": len(all_images),
            "images_with_faces": len([img for img in all_images if img["has_faces"]]),
            "images_without_faces": len([img for img in all_images if not img["has_faces"]])
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/person/<person_id>')
def get_person_details(person_id):
    """Get detailed information about a specific person"""
    try:
        # Validate ObjectId
        try:
            person_obj_id = ObjectId(person_id)
        except InvalidId:
            return jsonify({"error": "Invalid person ID"}), 400
        
        # Get person document
        person = persons_col.find_one({"_id": person_obj_id})
        if not person:
            return jsonify({"error": "Person not found"}), 404
        
        # Get all faces for this person
        faces = list(faces_col.find({"person_id": person_obj_id}))
        
        # Get all images that contain this person's faces
        image_ids = list(set([face["image_id"] for face in faces]))
        images = list(images_col.find({"_id": {"$in": image_ids}}))
        
        # Organize data
        person_faces = []
        person_images = []
        
        for face in faces:
            face_data = {
                "face_id": str(face["_id"]),
                "image_id": str(face["image_id"]),
                "cropped_face_filename": face.get("cropped_face_filename"),
                "face_location": face.get("face_location", {})
            }
            person_faces.append(face_data)
        
        for image in images:
            image_data = {
                "image_id": str(image["_id"]),
                "filename": image["filename"],
                "file_path": image["file_path"]
            }
            person_images.append(image_data)
        
        return jsonify({
            "person_id": str(person["_id"]),
            "person_name": person["name"],
            "total_faces": len(person_faces),
            "total_images": len(person_images),
            "faces": person_faces,
            "images": person_images
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/person/<person_id>/rename', methods=['PUT'])
def rename_person(person_id):
    """Rename a person"""
    try:
        # Validate ObjectId
        try:
            person_obj_id = ObjectId(person_id)
        except InvalidId:
            return jsonify({"error": "Invalid person ID"}), 400
        
        # Get new name from request
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"error": "Name is required"}), 400
        
        new_name = data['name'].strip()
        if not new_name:
            return jsonify({"error": "Name cannot be empty"}), 400
        
        # Check if person exists
        person = persons_col.find_one({"_id": person_obj_id})
        if not person:
            return jsonify({"error": "Person not found"}), 404
        
        # Update person name
        result = persons_col.update_one(
            {"_id": person_obj_id},
            {"$set": {"name": new_name, "updated_at": datetime.datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            return jsonify({
                "message": "Person renamed successfully",
                "person_id": str(person_obj_id),
                "old_name": person["name"],
                "new_name": new_name
            })
        else:
            return jsonify({"error": "Failed to update person name"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/image/<image_id>')
def get_image_details(image_id):
    """Get detailed information about a specific image"""
    try:
        # Validate ObjectId
        try:
            image_obj_id = ObjectId(image_id)
        except InvalidId:
            return jsonify({"error": "Invalid image ID"}), 400
        
        # Get image document
        image = images_col.find_one({"_id": image_obj_id})
        if not image:
            return jsonify({"error": "Image not found"}), 404
        
        # Get all faces in this image
        faces = list(faces_col.find({"image_id": image_obj_id}))
        
        # Get person information for each face
        image_faces = []
        for face in faces:
            person_info = None
            if face.get("person_id"):
                person = persons_col.find_one({"_id": face["person_id"]})
                if person:
                    person_info = {
                        "person_id": str(person["_id"]),
                        "person_name": person["name"]
                    }
            
            face_data = {
                "face_id": str(face["_id"]),
                "cropped_face_filename": face.get("cropped_face_filename"),
                "face_location": face.get("face_location", {}),
                "person": person_info
            }
            image_faces.append(face_data)
        
        return jsonify({
            "image_id": str(image["_id"]),
            "filename": image["filename"],
            "file_path": image["file_path"],
            "total_faces": len(image_faces),
            "faces": image_faces
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        total_persons = persons_col.count_documents({})
        total_images = images_col.count_documents({})
        total_faces = faces_col.count_documents({})
        
        # Get additional statistics
        images_with_faces = images_col.count_documents({"faces": {"$ne": []}})
        images_without_faces = total_images - images_with_faces
        manual_assignments = faces_col.count_documents({"is_manual_assignment": True})
        
        return jsonify({
            "total_persons": total_persons,
            "total_images": total_images,
            "total_faces": total_faces,
            "images_with_faces": images_with_faces,
            "images_without_faces": images_without_faces,
            "manual_face_assignments": manual_assignments,
            "gallery_stats": {
                "face_coverage": round((images_with_faces / total_images * 100) if total_images > 0 else 0, 1),
                "avg_faces_per_image": round((total_faces / images_with_faces) if images_with_faces > 0 else 0, 1),
                "avg_faces_per_person": round((total_faces / total_persons) if total_persons > 0 else 0, 1)
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['DELETE'])
def reset_database():
    """Reset the entire database (use with caution!)"""
    try:
        persons_col.delete_many({})
        images_col.delete_many({})
        faces_col.delete_many({})
        
        # Optionally, remove uploaded files
        # for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        #     os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        return jsonify({"message": "Database reset successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/face/<face_id>/move', methods=['PUT'])
def move_face_to_person(face_id):
    """Move a face from its current person to another existing person"""
    try:
        # Validate face ObjectId
        try:
            face_obj_id = ObjectId(face_id)
        except InvalidId:
            return jsonify({"error": "Invalid face ID"}), 400
        
        # Get request data
        data = request.get_json()
        if not data or 'target_person_id' not in data:
            return jsonify({"error": "target_person_id is required"}), 400
        
        # Validate target person ObjectId
        try:
            target_person_obj_id = ObjectId(data['target_person_id'])
        except InvalidId:
            return jsonify({"error": "Invalid target person ID"}), 400
        
        # Check if face exists
        face = faces_col.find_one({"_id": face_obj_id})
        if not face:
            return jsonify({"error": "Face not found"}), 404
        
        # Check if target person exists
        target_person = persons_col.find_one({"_id": target_person_obj_id})
        if not target_person:
            return jsonify({"error": "Target person not found"}), 404
        
        # Get current person (if any)
        current_person_id = face.get("person_id")
        current_person = None
        if current_person_id:
            current_person = persons_col.find_one({"_id": current_person_id})
        
        # Update face to new person and mark as manually assigned
        faces_col.update_one(
            {"_id": face_obj_id},
            {"$set": {
                "person_id": target_person_obj_id, 
                "is_manual_assignment": True,  # Mark as manually assigned
                "manual_assignment_date": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow()
            }}
        )
        
        # Update current person (remove face and image references)
        deleted_person_name = None
        if current_person:
            persons_col.update_one(
                {"_id": current_person_id},
                {
                    "$pull": {"faces": face_obj_id},
                    "$set": {"updated_at": datetime.datetime.utcnow()}
                }
            )
            
            # Check if current person has any remaining faces
            remaining_faces = faces_col.count_documents({"person_id": current_person_id})
            
            if remaining_faces == 0:
                # Person has no more faces, delete the person
                deleted_person_name = current_person["name"]
                persons_col.delete_one({"_id": current_person_id})
                print(f"Deleted empty person: {deleted_person_name}")
            else:
                # Check if image should be removed from current person
                image_faces = faces_col.count_documents({
                    "image_id": face["image_id"],
                    "person_id": current_person_id
                })
                if image_faces == 0:
                    persons_col.update_one(
                        {"_id": current_person_id},
                        {"$pull": {"images": face["image_id"]}}
                    )
        
        # Update target person (add face and image references)
        persons_col.update_one(
            {"_id": target_person_obj_id},
            {
                "$addToSet": {
                    "faces": face_obj_id,
                    "images": face["image_id"]
                },
                "$set": {"updated_at": datetime.datetime.utcnow()}
            }
        )
        
        # Update image document
        images_col.update_one(
            {"_id": face["image_id"]},
            {
                "$addToSet": {"persons": target_person_obj_id},
                "$set": {"updated_at": datetime.datetime.utcnow()}
            }
        )
        
        # Remove image from current person if no more faces
        if current_person_id:
            image_faces_count = faces_col.count_documents({
                "image_id": face["image_id"],
                "person_id": current_person_id
            })
            if image_faces_count == 0:
                images_col.update_one(
                    {"_id": face["image_id"]},
                    {"$pull": {"persons": current_person_id}}
                )
        
        return jsonify({
            "message": "Face moved successfully",
            "face_id": str(face_obj_id),
            "from_person": current_person["name"] if current_person else "No person",
            "to_person": target_person["name"],
            "target_person_id": str(target_person_obj_id),
            "deleted_empty_person": deleted_person_name
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/face/<face_id>/move-to-new', methods=['PUT'])
def move_face_to_new_person(face_id):
    """Move a face from its current person to a new person"""
    try:
        # Validate face ObjectId
        try:
            face_obj_id = ObjectId(face_id)
        except InvalidId:
            return jsonify({"error": "Invalid face ID"}), 400
        
        # Check if face exists
        face = faces_col.find_one({"_id": face_obj_id})
        if not face:
            return jsonify({"error": "Face not found"}), 404
        
        # Get current person (if any)
        current_person_id = face.get("person_id")
        current_person = None
        if current_person_id:
            current_person = persons_col.find_one({"_id": current_person_id})
        
        # Create new person with auto-generated name
        person_count = persons_col.count_documents({}) + 1
        new_person_doc = {
            "name": f"Person {person_count}",
            "faces": [face_obj_id],
            "images": [face["image_id"]],
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        
        new_person_result = persons_col.insert_one(new_person_doc)
        new_person_id = new_person_result.inserted_id
        
        # Update face to new person and mark as manually assigned
        faces_col.update_one(
            {"_id": face_obj_id},
            {"$set": {
                "person_id": new_person_id, 
                "is_manual_assignment": True,  # Mark as manually assigned
                "manual_assignment_date": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow()
            }}
        )
        
        # Update current person (remove face and image references)
        deleted_person_name = None
        if current_person:
            persons_col.update_one(
                {"_id": current_person_id},
                {
                    "$pull": {"faces": face_obj_id},
                    "$set": {"updated_at": datetime.datetime.utcnow()}
                }
            )
            
            # Check if current person has any remaining faces
            remaining_faces = faces_col.count_documents({"person_id": current_person_id})
            
            if remaining_faces == 0:
                # Person has no more faces, delete the person
                deleted_person_name = current_person["name"]
                persons_col.delete_one({"_id": current_person_id})
                print(f"Deleted empty person: {deleted_person_name}")
            else:
                # Check if image should be removed from current person
                image_faces = faces_col.count_documents({
                    "image_id": face["image_id"],
                    "person_id": current_person_id
                })
                if image_faces == 0:
                    persons_col.update_one(
                        {"_id": current_person_id},
                        {"$pull": {"images": face["image_id"]}}
                    )
        
        # Update image document
        images_col.update_one(
            {"_id": face["image_id"]},
            {
                "$addToSet": {"persons": new_person_id},
                "$set": {"updated_at": datetime.datetime.utcnow()}
            }
        )
        
        # Remove image from current person if no more faces
        if current_person_id:
            image_faces_count = faces_col.count_documents({
                "image_id": face["image_id"],
                "person_id": current_person_id
            })
            if image_faces_count == 0:
                images_col.update_one(
                    {"_id": face["image_id"]},
                    {"$pull": {"persons": current_person_id}}
                )
        
        return jsonify({
            "message": "Face moved to new person successfully",
            "face_id": str(face_obj_id),
            "from_person": current_person["name"] if current_person else "No person",
            "new_person_id": str(new_person_id),
            "new_person_name": f"Person {person_count}",
            "deleted_empty_person": deleted_person_name
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search-by-image', methods=['POST'])
def search_by_image():
    """Search for similar faces using an uploaded image"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Check if file is allowed
        if not (file and allowed_file(file.filename)):
            return jsonify({"error": "Invalid file type"}), 400
        
        # Save temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Load image and detect faces
            image_data = face_recognition.load_image_file(temp_path)
            face_locations = face_recognition.face_locations(image_data)
            face_encodings = face_recognition.face_encodings(image_data, face_locations)
            
            # Check face count
            if len(face_encodings) == 0:
                return jsonify({
                    "error": "No faces detected in the uploaded image",
                    "message": "Please upload an image with at least one visible face"
                }), 400
            
            if len(face_encodings) > 1:
                return jsonify({
                    "error": "Multiple faces detected in the uploaded image",
                    "message": "Please upload an image with exactly one face for search",
                    "faces_detected": len(face_encodings)
                }), 400
            
            # Get the single face encoding
            search_encoding = face_encodings[0]
            
            # Get all faces from database
            all_faces = list(faces_col.find({}, {
                "embedding": 1, 
                "person_id": 1, 
                "image_id": 1, 
                "cropped_face_filename": 1,
                "_id": 1
            }))
            
            if not all_faces:
                return jsonify({
                    "message": "No faces in database to search against",
                    "matches": []
                })
            
            # Compare against all faces
            known_encodings = []
            face_data = []
            
            for face in all_faces:
                if face.get("embedding"):
                    known_encodings.append(np.array(face["embedding"]))
                    face_data.append(face)
            
            # Find matches with configurable tolerance
            search_tolerance = float(request.form.get('tolerance', app_config.FACE_RECOGNITION_TOLERANCE))
            matches = face_recognition.compare_faces(
                known_encodings, 
                search_encoding, 
                tolerance=search_tolerance
            )
            
            # Get distances for ranking
            distances = face_recognition.face_distance(known_encodings, search_encoding)
            
            # Collect matches with their confidence scores
            match_results = []
            for i, (is_match, distance) in enumerate(zip(matches, distances)):
                if is_match:
                    face = face_data[i]
                    
                    # Get person information
                    person = persons_col.find_one({"_id": face["person_id"]}) if face.get("person_id") else None
                    
                    # Get image information
                    image = images_col.find_one({"_id": face["image_id"]}) if face.get("image_id") else None
                    
                    confidence = max(0, 1 - (distance / search_tolerance))
                    
                    match_result = {
                        "face_id": str(face["_id"]),
                        "confidence": round(confidence * 100, 1),  # Percentage
                        "distance": round(float(distance), 4),
                        "person": {
                            "person_id": str(person["_id"]) if person else None,
                            "person_name": person.get("name", "Unknown") if person else "Unknown"
                        } if person else None,
                        "image": {
                            "image_id": str(image["_id"]) if image else None,
                            "filename": image.get("filename", "") if image else ""
                        } if image else None,
                        "cropped_face_filename": face.get("cropped_face_filename")
                    }
                    match_results.append(match_result)
            
            # Sort by confidence (highest first)
            match_results.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Limit results
            max_results = int(request.form.get('max_results', 20))
            match_results = match_results[:max_results]
            
            return jsonify({
                "message": f"Found {len(match_results)} matching faces",
                "search_params": {
                    "tolerance": search_tolerance,
                    "max_results": max_results
                },
                "matches": match_results,
                "total_faces_searched": len(known_encodings)
            })
            
        finally:
            # Clean up temporary file
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/all-persons', methods=['GET'])
def get_all_persons():
    """Get all persons with their first cropped face as thumbnail"""
    try:
        persons = list(persons_col.find())
        person_list = []
        
        for person in persons:
            # Get the first face for this person as thumbnail
            first_face = faces_col.find_one({"person_id": person["_id"]})
            thumbnail_filename = None
            
            if first_face and first_face.get("cropped_face_filename"):
                thumbnail_filename = first_face["cropped_face_filename"]
            
            person_data = {
                "person_id": str(person["_id"]),
                "person_name": person.get("name", "Unknown"),
                "total_faces": len(person.get("faces", [])),
                "total_images": len(person.get("images", [])),
                "thumbnail": thumbnail_filename  # cropped face filename
            }
            person_list.append(person_data)
        
        # Sort by person name
        person_list.sort(key=lambda x: x["person_name"])
        
        return jsonify({
            "persons": person_list,
            "total": len(person_list)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=app_config.DEBUG, host='0.0.0.0', port=5000)