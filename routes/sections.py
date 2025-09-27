from flask import Blueprint, request, jsonify
import datetime
from bson import ObjectId
from bson.errors import InvalidId

sections_bp = Blueprint('sections', __name__)

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

@sections_bp.route('/', methods=['GET'])
def get_all_sections():
    """Get all sections"""
    try:
        from flask import current_app
        
        db = current_app.db
        sections_col = db.sections
        images_col = db.images
        
        sections = list(sections_col.find())
        section_list = []
        
        for section in sections:
            # Count images in this section
            image_count = images_col.count_documents({"section_id": str(section["_id"])})
            
            section_data = {
                "section_id": str(section["_id"]),
                "name": section.get("name", "Untitled Section"),
                "description": section.get("description", ""),
                "created_at": section.get("created_at"),
                "image_count": image_count
            }
            section_list.append(section_data)
        
        # Sort by creation date (newest first)
        section_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return jsonify({
            "status": "success",
            "message": f"Retrieved {len(section_list)} sections",
            "sections": section_list,
            "total": len(section_list)
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@sections_bp.route('/', methods=['POST'])
def create_section():
    """Create a new section"""
    try:
        from flask import current_app
        
        db = current_app.db
        sections_col = db.sections
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"status": "error", "message": "Section name is required"}), 400
        
        # Check if section with same name exists
        existing = sections_col.find_one({"name": name})
        if existing:
            return jsonify({"status": "error", "message": "Section with this name already exists"}), 400
        
        section_doc = {
            "name": name,
            "description": data.get("description", "").strip(),
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        
        result = sections_col.insert_one(section_doc)
        section_doc["section_id"] = str(result.inserted_id)
        section_doc.pop("_id", None)
        
        return jsonify({
            "status": "success",
            "message": "Section created successfully",
            "section": section_doc
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@sections_bp.route('/<section_id>', methods=['GET'])
def get_section(section_id):
    """Get a specific section"""
    try:
        from flask import current_app
        
        db = current_app.db
        sections_col = db.sections
        images_col = db.images
        
        if not ObjectId.is_valid(section_id):
            return jsonify({"status": "error", "message": "Invalid section ID"}), 400
        
        section = sections_col.find_one({"_id": ObjectId(section_id)})
        if not section:
            return jsonify({"status": "error", "message": "Section not found"}), 404
        
        # Count images in this section
        image_count = images_col.count_documents({"section_id": section_id})
        
        section_data = {
            "section_id": str(section["_id"]),
            "name": section.get("name", "Untitled Section"),
            "description": section.get("description", ""),
            "created_at": section.get("created_at"),
            "updated_at": section.get("updated_at"),
            "image_count": image_count
        }
        
        return jsonify({"status": "success", "data": {"section": section_data}})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@sections_bp.route('/<section_id>', methods=['PUT'])
def update_section(section_id):
    """Update a section"""
    try:
        from flask import current_app
        
        db = current_app.db
        sections_col = db.sections
        
        if not ObjectId.is_valid(section_id):
            return jsonify({"status": "error", "message": "Invalid section ID"}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"status": "error", "message": "Section name is required"}), 400
        
        # Check if another section with same name exists
        existing = sections_col.find_one({
            "name": name, 
            "_id": {"$ne": ObjectId(section_id)}
        })
        if existing:
            return jsonify({"status": "error", "message": "Section with this name already exists"}), 400
        
        update_data = {
            "name": name,
            "description": data.get("description", "").strip(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        
        result = sections_col.update_one(
            {"_id": ObjectId(section_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({"status": "error", "message": "Section not found"}), 404
        
        return jsonify({"status": "success", "message": "Section updated successfully"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@sections_bp.route('/<section_id>', methods=['DELETE'])
def delete_section(section_id):
    """Delete a section"""
    try:
        from flask import current_app
        
        db = current_app.db
        sections_col = db.sections
        images_col = db.images
        
        if not ObjectId.is_valid(section_id):
            return jsonify({"status": "error", "message": "Invalid section ID"}), 400
        
        # Check if section exists
        section = sections_col.find_one({"_id": ObjectId(section_id)})
        if not section:
            return jsonify({"status": "error", "message": "Section not found"}), 404
        
        # Remove section_id from all images in this section
        images_col.update_many(
            {"section_id": section_id},
            {"$unset": {"section_id": ""}}
        )
        
        # Delete the section
        result = sections_col.delete_one({"_id": ObjectId(section_id)})
        
        if result.deleted_count == 0:
            return jsonify({"status": "error", "message": "Failed to delete section"}), 500
        
        return jsonify({
            "status": "success",
            "message": "Section deleted successfully",
            "section_name": section.get("name", "Unknown")
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
