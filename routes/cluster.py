from flask import Blueprint, request, jsonify
import numpy as np
import datetime
from sklearn.cluster import DBSCAN
import face_recognition

cluster_bp = Blueprint('cluster', __name__)

@cluster_bp.route('/preview', methods=['POST'])
def preview_clustering():
    """
    Preview clustering results with different parameters without saving
    """
    try:
        from flask import current_app
        from config import config
        import os
        
        # Get configuration
        env = os.getenv('FLASK_ENV', 'development')
        app_config = config.get(env, config['default'])
        
        db = current_app.db
        faces_col = db.faces
        
        data = request.get_json()
        eps = float(data.get('eps', app_config.DBSCAN_EPS))
        min_samples = int(data.get('min_samples', app_config.DBSCAN_MIN_SAMPLES))
        
        # Get all faces from database
        faces = list(faces_col.find())
        
        if not faces:
            return jsonify({
                "status": "success",
                "message": "No faces to preview"
            })
        
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
            "status": "success",
            "message": "Clustering preview completed successfully",
            "preview_results": {
                "total_faces": len(faces),
                "unique_clusters": len(unique_labels) - (1 if -1 in unique_labels else 0),
                "outliers": cluster_stats.get(-1, 0),
                "cluster_sizes": {k: v for k, v in cluster_stats.items() if k != -1},
                "parameters": {"eps": eps, "min_samples": min_samples}
            }
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@cluster_bp.route('/', methods=['GET'])
def cluster_faces():
    """
    Re-cluster faces using face_recognition logic, preserving manual assignments.
    Only automatically assigned faces will be re-clustered.
    """
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
                "status": "success",
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
            return jsonify({
                "status": "success",
                "message": "Need at least 2 faces for clustering"
            })
        
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
                    "images": [],
                    "created_at": datetime.datetime.utcnow().isoformat()
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
                    "images": list(image_ids),
                    "updated_at": datetime.datetime.utcnow().isoformat()
                }}
            )
        
        # Update image documents
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
                {"$set": {
                    "persons": list(person_ids),
                    "updated_at": datetime.datetime.utcnow().isoformat()
                }}
            )
        
        total_persons = persons_col.count_documents({})
        total_faces_assigned = faces_col.count_documents({"person_id": {"$exists": True}})
        
        return jsonify({
            "status": "success",
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
        return jsonify({"status": "error", "message": str(e)}), 500
