from flask import Blueprint, jsonify

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        from flask import current_app
        
        db = current_app.db
        persons_col = db.persons
        images_col = db.images
        faces_col = db.faces
        albums_col = db.albums
        sections_col = db.sections
        
        total_persons = persons_col.count_documents({})
        total_images = images_col.count_documents({})
        total_faces = faces_col.count_documents({})
        total_albums = albums_col.count_documents({})
        total_sections = sections_col.count_documents({})
        
        # Get additional statistics
        images_with_faces = images_col.count_documents({"faces": {"$ne": []}})
        images_without_faces = total_images - images_with_faces
        manual_assignments = faces_col.count_documents({"is_manual_assignment": True})
        
        return jsonify({
            "status": "success",
            "data": {
                "total_persons": total_persons,
                "total_images": total_images,
                "total_faces": total_faces,
                "total_albums": total_albums,
                "total_sections": total_sections,
                "images_with_faces": images_with_faces,
                "images_without_faces": images_without_faces,
                "manual_face_assignments": manual_assignments,
                "gallery_stats": {
                    "face_coverage": round((images_with_faces / total_images * 100) if total_images > 0 else 0, 1),
                    "avg_faces_per_image": round((total_faces / images_with_faces) if images_with_faces > 0 else 0, 1),
                    "avg_faces_per_person": round((total_faces / total_persons) if total_persons > 0 else 0, 1)
                }
            },
            "message": "Statistics retrieved successfully"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
