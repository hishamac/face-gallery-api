from flask import Blueprint, request, jsonify, send_from_directory
import datetime
from bson import ObjectId
from bson.errors import InvalidId

persons_bp = Blueprint('persons', __name__)

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

@persons_bp.route('/', methods=['GET'])
def get_all_persons():
    """Get all persons with their first cropped face as thumbnail"""
    try:
        from flask import current_app
        
        db = current_app.db
        persons_col = db.persons
        faces_col = db.faces
        
        persons = list(persons_col.find())
        person_list = []
        
        for person in persons:
            # Get the first face for this person as thumbnail
            first_face = faces_col.find_one({"person_id": person["_id"]})
            thumbnail_face_id = None
            
            if first_face:
                thumbnail_face_id = str(first_face["_id"])
            
            person_data = {
                "person_id": str(person["_id"]),
                "person_name": person.get("name", "Unknown"),
                "total_faces": len(person.get("faces", [])),
                "total_images": len(person.get("images", [])),
                "thumbnail": thumbnail_face_id  # face ID for thumbnail
            }
            person_list.append(person_data)
        
        # Sort by person name
        person_list.sort(key=lambda x: x["person_name"])
        
        return jsonify({
            "status": "success",
            "message": f"Retrieved {len(person_list)} persons",
            "persons": person_list,
            "total": len(person_list)
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@persons_bp.route('/<person_id>', methods=['GET'])
def get_person_details(person_id):
    """Get detailed information about a specific person"""
    try:
        from flask import current_app
        
        db = current_app.db
        persons_col = db.persons
        faces_col = db.faces
        images_col = db.images
        
        # Validate ObjectId
        try:
            person_obj_id = ObjectId(person_id)
        except InvalidId:
            return jsonify({"status": "error", "message": "Invalid person ID"}), 400
        
        # Get person document
        person = persons_col.find_one({"_id": person_obj_id})
        if not person:
            return jsonify({"status": "error", "message": "Person not found"}), 404
        
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
                "mime_type": image.get("mime_type", "image/jpeg")
            }
            person_images.append(image_data)
        
        return jsonify({
            "status": "success",
            "message": f"Person details retrieved successfully",
            "person_id": str(person["_id"]),
            "person_name": person["name"],
            "total_faces": len(person_faces),
            "total_images": len(person_images),
            "faces": person_faces,
            "images": person_images
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@persons_bp.route('/<person_id>/rename', methods=['PUT'])
def rename_person(person_id):
    """Rename a person"""
    try:
        from flask import current_app
        
        db = current_app.db
        persons_col = db.persons
        
        # Validate ObjectId
        try:
            person_obj_id = ObjectId(person_id)
        except InvalidId:
            return jsonify({"status": "error", "message": "Invalid person ID"}), 400
        
        # Get new name from request
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"status": "error", "message": "Name is required"}), 400
        
        new_name = data['name'].strip()
        if not new_name:
            return jsonify({"status": "error", "message": "Name cannot be empty"}), 400
        
        # Check if person exists
        person = persons_col.find_one({"_id": person_obj_id})
        if not person:
            return jsonify({"status": "error", "message": "Person not found"}), 404
        
        # Update person name
        result = persons_col.update_one(
            {"_id": person_obj_id},
            {"$set": {"name": new_name, "updated_at": datetime.datetime.utcnow().isoformat()}}
        )
        
        if result.modified_count > 0:
            return jsonify({
                "status": "success",
                "message": "Person renamed successfully",
                "person_id": str(person_obj_id),
                "old_name": person["name"],
                "new_name": new_name
            })
        else:
            return jsonify({"status": "error", "message": "Failed to update person name"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
