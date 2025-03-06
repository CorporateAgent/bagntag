#!/usr/bin/env python3
"""
Simple Cloudinary batch uploader that checks if images exist before uploading.
"""

import os
import json
import time
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
from pathlib import Path

### CONFIGURATION PARAMETERS ###
FOLDER_PATH = "images/menswear"          # Folder containing images to process
METADATA_FILE = "data/image_metadata.json"     # Metadata storage file
RATE_LIMIT_UPLOAD = 1                       # Rate limit in seconds between uploads

# Load environment variables
load_dotenv()

# Cloudinary configuration using environment variables
cloudinary.config(
    cloud_name=os.getenv('CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

def image_exists(image_id):
    """Check if image already exists in Cloudinary."""
    try:
        # Try to get the image details from Cloudinary
        cloudinary.api.resource(f"tagged/{image_id}")
        return True
    except cloudinary.api.NotFound:
        return False

def upload_image(image_path, metadata):
    """Upload a single image to Cloudinary with its metadata."""
    try:
        result = cloudinary.uploader.upload(
            image_path,
            folder="tagged",
            public_id=Path(image_path).stem,
            tags=metadata.get("tags", []),
            context={"caption": metadata.get("description", "")},
            resource_type="auto"
        )
        return result["secure_url"]
    except Exception as e:
        print(f"Failed to upload {image_path}: {e}")
        return None

def process_images(folder_path, metadata_file):
    """Process all images from metadata file."""
    # Load metadata from file
    with open(metadata_file, "r") as f:
        data = json.load(f)

    for image in data.get("images", []):
        image_id = Path(image["filename"]).stem
        
        # Check if image already exists in Cloudinary
        if image_exists(image_id):
            print(f"\nSkipping {image['filename']} - already exists in Cloudinary")
            continue
            
        print(f"\nProcessing: {image['filename']}")
        
        image_path = os.path.join(folder_path, image["filename"])
        url = upload_image(image_path, image.get("metadata", {}))
        
        if url:
            print(f"Success: {url}")
        
        time.sleep(RATE_LIMIT_UPLOAD)

if __name__ == "__main__":
    process_images(FOLDER_PATH, METADATA_FILE)