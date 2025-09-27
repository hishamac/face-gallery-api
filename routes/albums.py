from flask import Blueprint, request, jsonify
import datetime
from bson import ObjectId
from bson.errors import InvalidId

albums_bp = Blueprint('albums', __name__)

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

@albums_bp.route('/', methods=['GET'])
def get_all_albums():
    """Get all albums"""
    try:
        from flask import current_app
        
        db = current_app.db
        albums_col = db.albums
        images_col = db.images
        
        albums = list(albums_col.find())
        album_list = []
        
        for album in albums:
            # Count images in this album
            image_count = images_col.count_documents({"album_id": str(album["_id"])})
            
            album_data = {
                "album_id": str(album["_id"]),
                "name": album.get("name", "Untitled Album"),
                "description": album.get("description", ""),
                "created_at": album.get("created_at"),
                "image_count": image_count
            }
            album_list.append(album_data)
        
        # Sort by creation date (newest first)
        album_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return jsonify({
            "status": "success",
            "message": f"Retrieved {len(album_list)} albums",
            "albums": album_list,
            "total": len(album_list)
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@albums_bp.route('/', methods=['POST'])
def create_album():
    """Create a new album"""
    try:
        from flask import current_app
        
        db = current_app.db
        albums_col = db.albums
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"status": "error", "message": "Album name is required"}), 400
        
        # Check if album with same name exists
        existing = albums_col.find_one({"name": name})
        if existing:
            return jsonify({"status": "error", "message": "Album with this name already exists"}), 400
        
        album_doc = {
            "name": name,
            "description": data.get("description", "").strip(),
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        
        result = albums_col.insert_one(album_doc)
        album_doc["album_id"] = str(result.inserted_id)
        album_doc.pop("_id", None)
        
        return jsonify({
            "status": "success",
            "message": "Album created successfully",
            "album": album_doc
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@albums_bp.route('/<album_id>', methods=['GET'])
def get_album(album_id):
    """Get a specific album"""
    try:
        from flask import current_app
        
        db = current_app.db
        albums_col = db.albums
        images_col = db.images
        
        if not ObjectId.is_valid(album_id):
            return jsonify({"status": "error", "message": "Invalid album ID"}), 400
        
        album = albums_col.find_one({"_id": ObjectId(album_id)})
        if not album:
            return jsonify({"status": "error", "message": "Album not found"}), 404
        
        # Count images in this album
        image_count = images_col.count_documents({"album_id": album_id})
        
        album_data = {
            "album_id": str(album["_id"]),
            "name": album.get("name", "Untitled Album"),
            "description": album.get("description", ""),
            "created_at": album.get("created_at"),
            "updated_at": album.get("updated_at"),
            "image_count": image_count
        }
        
        return jsonify({
            "status": "success",
            "message": "Album retrieved successfully",
            "album": album_data
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@albums_bp.route('/<album_id>', methods=['PUT'])
def update_album(album_id):
    """Update an album"""
    try:
        from flask import current_app
        
        db = current_app.db
        albums_col = db.albums
        
        if not ObjectId.is_valid(album_id):
            return jsonify({"status": "error", "message": "Invalid album ID"}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"status": "error", "message": "Album name is required"}), 400
        
        # Check if another album with same name exists
        existing = albums_col.find_one({
            "name": name, 
            "_id": {"$ne": ObjectId(album_id)}
        })
        if existing:
            return jsonify({"status": "error", "message": "Album with this name already exists"}), 400
        
        update_data = {
            "name": name,
            "description": data.get("description", "").strip(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        
        result = albums_col.update_one(
            {"_id": ObjectId(album_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({"status": "error", "message": "Album not found"}), 404
        
        return jsonify({
            "status": "success",
            "message": "Album updated successfully"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@albums_bp.route('/<album_id>', methods=['DELETE'])
def delete_album(album_id):
    """Delete an album"""
    try:
        from flask import current_app
        
        db = current_app.db
        albums_col = db.albums
        images_col = db.images
        
        if not ObjectId.is_valid(album_id):
            return jsonify({"status": "error", "message": "Invalid album ID"}), 400
        
        # Check if album exists
        album = albums_col.find_one({"_id": ObjectId(album_id)})
        if not album:
            return jsonify({"status": "error", "message": "Album not found"}), 404
        
        # Remove album_id from all images in this album
        images_col.update_many(
            {"album_id": album_id},
            {"$unset": {"album_id": ""}}
        )
        
        # Delete the album
        result = albums_col.delete_one({"_id": ObjectId(album_id)})
        
        if result.deleted_count == 0:
            return jsonify({"status": "error", "message": "Failed to delete album"}), 500
        
        return jsonify({
            "status": "success",
            "message": "Album deleted successfully",
            "album_name": album.get("name", "Unknown")
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
