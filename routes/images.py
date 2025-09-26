from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import face_recognition
import numpy as np
import datetime
import os
from bson import ObjectId
from bson.errors import InvalidId
import tempfile

images_bp = Blueprint('images', __name__)

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

def crop_and_save_face(image_array, face_location, face_index, image_filename):
    """Crop face from image and save it as a separate file"""
    from flask import current_app
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
        face_path = os.path.join(current_app.config['FACES_FOLDER'], face_filename)
        
        # Save cropped face
        face_image.save(face_path, 'JPEG', quality=90)
        
        return face_path, face_filename
    except Exception as e:
        print(f"Error cropping face: {e}")
        return None, None

def process_single_image(file, album_id=None, section_id=None):
    """Helper function to process a single image"""
    from flask import current_app
    from config import config
    import os
    
    # Get configuration
    env = os.getenv('FLASK_ENV', 'development')
    app_config = config.get(env, config['default'])
    
    # Get database collections from current_app
    db = current_app.db
    images_col = db.images
    faces_col = db.faces
    persons_col = db.persons
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
        "persons": [],
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    # Add album_id and section_id if provided
    if album_id:
        image_doc["album_id"] = album_id
    if section_id:
        image_doc["section_id"] = section_id
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
                "images": [],
                "created_at": datetime.datetime.utcnow().isoformat()
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
            "cropped_face_filename": face_filename,
            "created_at": datetime.datetime.utcnow().isoformat()
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
                },
                "$set": {"updated_at": datetime.datetime.utcnow().isoformat()}
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
            "persons": list(assigned_persons),
            "updated_at": datetime.datetime.utcnow().isoformat()
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

@images_bp.route('/', methods=['GET'])
def get_all_images():
    """Get all uploaded images (with and without faces)"""
    try:
        from flask import current_app
        
        db = current_app.db
        images_col = db.images
        faces_col = db.faces
        persons_col = db.persons
        
        # Get query parameters for filtering
        album_id = request.args.get('album_id')
        section_id = request.args.get('section_id')
        
        # Build query filter
        query_filter = {}
        if album_id and ObjectId.is_valid(album_id):
            query_filter['album_id'] = album_id
        if section_id and ObjectId.is_valid(section_id):
            query_filter['section_id'] = section_id
        
        images = list(images_col.find(query_filter))
        
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
            
            # Get album info if exists
            album_info = None
            if image.get("album_id"):
                album = db.albums.find_one({"_id": ObjectId(image["album_id"])})
                if album:
                    album_info = {"album_id": str(album["_id"]), "album_name": album.get("name", "Unknown")}
            
            # Get section info if exists
            section_info = None
            if image.get("section_id"):
                section = db.sections.find_one({"_id": ObjectId(image["section_id"])})
                if section:
                    section_info = {"section_id": str(section["_id"]), "section_name": section.get("name", "Unknown")}
            
            image_data = {
                "image_id": str(image["_id"]),
                "filename": image.get("filename", ""),
                "file_path": image.get("file_path", ""),
                "faces_count": len(image_faces),
                "persons_count": len(persons_in_image),
                "persons": persons_in_image,
                "has_faces": len(image_faces) > 0,
                "album": album_info,
                "section": section_info,
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

@images_bp.route('/upload', methods=['POST'])
def upload_image():
    """Upload a single image for face detection and clustering"""
    try:
        from flask import current_app
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Get optional album_id and section_id
        album_id = request.form.get('album_id')
        section_id = request.form.get('section_id')
        
        # Validate album_id if provided
        if album_id and not ObjectId.is_valid(album_id):
            return jsonify({"error": "Invalid album ID"}), 400
        
        # Validate section_id if provided
        if section_id and not ObjectId.is_valid(section_id):
            return jsonify({"error": "Invalid section ID"}), 400
        
        # Check if file is allowed
        if file and current_app.allowed_file(file.filename):
            return process_single_image(file, album_id, section_id)
        
        return jsonify({"error": "Invalid file type"}), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@images_bp.route('/upload-multiple', methods=['POST'])
def upload_multiple_images():
    """Upload multiple images for face detection and clustering"""
    try:
        from flask import current_app
        
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({"error": "No files part"}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "No files selected"}), 400
        
        # Get optional album_id and section_id
        album_id = request.form.get('album_id')
        section_id = request.form.get('section_id')
        
        # Validate album_id if provided
        if album_id and not ObjectId.is_valid(album_id):
            return jsonify({"error": "Invalid album ID"}), 400
        
        # Validate section_id if provided
        if section_id and not ObjectId.is_valid(section_id):
            return jsonify({"error": "Invalid section ID"}), 400
        
        results = []
        total_faces = 0
        successful_uploads = 0
        errors = []
        
        for file in files:
            if file and file.filename != '' and current_app.allowed_file(file.filename):
                try:
                    result = process_single_image(file, album_id, section_id)
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

@images_bp.route('/<image_id>', methods=['GET'])
def get_image_details(image_id):
    """Get detailed information about a specific image"""
    try:
        from flask import current_app
        
        db = current_app.db
        images_col = db.images
        faces_col = db.faces
        persons_col = db.persons
        
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

@images_bp.route('/<filename>/file')
def serve_image_file(filename):
    """Serve uploaded images"""
    from flask import current_app
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@images_bp.route('/search-by-image', methods=['POST'])
def search_by_image():
    """Search for similar faces using an uploaded image"""
    try:
        from flask import current_app
        from config import config
        import os
        
        # Get configuration
        env = os.getenv('FLASK_ENV', 'development')
        app_config = config.get(env, config['default'])
        
        db = current_app.db
        faces_col = db.faces
        persons_col = db.persons
        images_col = db.images
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Check if file is allowed
        if not (file and current_app.allowed_file(file.filename)):
            return jsonify({"error": "Invalid file type"}), 400
        
        # Save temporary file
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
                        "confidence": round(confidence * 100, 1),
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
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500