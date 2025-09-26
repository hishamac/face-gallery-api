from flask import Blueprint, request, jsonify, send_from_directory
import datetime
from bson import ObjectId
from bson.errors import InvalidId

faces_bp = Blueprint('faces', __name__)

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

@faces_bp.route('/<filename>')
def serve_cropped_face(filename):
    """Serve cropped face images"""
    from flask import current_app
    return send_from_directory(current_app.config['FACES_FOLDER'], filename)

@faces_bp.route('/<face_id>/move', methods=['PUT'])
def move_face_to_person(face_id):
    """Move a face from its current person to another existing person"""
    try:
        from flask import current_app
        
        db = current_app.db
        faces_col = db.faces
        persons_col = db.persons
        images_col = db.images
        
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
                "manual_assignment_date": datetime.datetime.utcnow().isoformat(),
                "updated_at": datetime.datetime.utcnow().isoformat()
            }}
        )
        
        # Update current person (remove face and image references)
        deleted_person_name = None
        if current_person:
            persons_col.update_one(
                {"_id": current_person_id},
                {
                    "$pull": {"faces": face_obj_id},
                    "$set": {"updated_at": datetime.datetime.utcnow().isoformat()}
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
                "$set": {"updated_at": datetime.datetime.utcnow().isoformat()}
            }
        )
        
        # Update image document
        images_col.update_one(
            {"_id": face["image_id"]},
            {
                "$addToSet": {"persons": target_person_obj_id},
                "$set": {"updated_at": datetime.datetime.utcnow().isoformat()}
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

@faces_bp.route('/<face_id>/move-to-new', methods=['PUT'])
def move_face_to_new_person(face_id):
    """Move a face from its current person to a new person"""
    try:
        from flask import current_app
        
        db = current_app.db
        faces_col = db.faces
        persons_col = db.persons
        images_col = db.images
        
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
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        
        new_person_result = persons_col.insert_one(new_person_doc)
        new_person_id = new_person_result.inserted_id
        
        # Update face to new person and mark as manually assigned
        faces_col.update_one(
            {"_id": face_obj_id},
            {"$set": {
                "person_id": new_person_id, 
                "is_manual_assignment": True,  # Mark as manually assigned
                "manual_assignment_date": datetime.datetime.utcnow().isoformat(),
                "updated_at": datetime.datetime.utcnow().isoformat()
            }}
        )
        
        # Update current person (remove face and image references)
        deleted_person_name = None
        if current_person:
            persons_col.update_one(
                {"_id": current_person_id},
                {
                    "$pull": {"faces": face_obj_id},
                    "$set": {"updated_at": datetime.datetime.utcnow().isoformat()}
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
                "$set": {"updated_at": datetime.datetime.utcnow().isoformat()}
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