
# Image Processing and Tagging Pipeline

A system for automatic image analysis, description generation, and metadata tagging using LLM vision models.

## Overview

This project provides a complete pipeline for processing images, generating detailed descriptions, and tagging them with relevant metadata. The system uses Ollama's vision models for image analysis and text generation, then uploads processed images to Cloudinary with their associated metadata.

## Features

- **Multi-Tier Processing**: Uses vision models to generate descriptions, then extracts relevant tags
- **Cloudinary Integration**: Automatically uploads processed images with metadata to Cloudinary
- **Fault Tolerance**: Includes state persistence with automatic backups
- **Configurable Models**: Flexible model selection for different processing stages
- **Category Validation**: Ensures tags match predefined product categories

## Project Structure

```
├── main.py                 # Core image processing and metadata generation
├── manage_cloud.py         # Cloudinary upload management
├── requirements.txt        # Python dependencies
├── data/
│   ├── categories.json     # Valid product tags/categories
│   ├── image_metadata.json # Generated metadata storage
│   └── README.md           # This documentation
├── images/
│   └── menswear/           # Source product images
└── __pycache__/            # Compiled Python bytecode
```

## Setup & Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in .env:
   ```
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   CLOUD_NAME=your_cloud_name
   ANTHROPIC_API_KEY=your_anthropic_key
   ```
4. Ensure Ollama is installed and running

## Usage

### Image Processing Pipeline

Run the main processing script to generate descriptions and tags:

```bash
python main.py
```

This will:
1. Scan the configured image folder
2. Generate detailed product descriptions using vision models
3. Extract relevant tags based on the descriptions
4. Save all metadata to image_metadata.json

### Cloudinary Upload

After processing images, upload them to Cloudinary with:

```bash
python manage_cloud.py
```

This script:
- Checks if images already exist in Cloudinary to prevent duplicates
- Uploads new images with their descriptions and tags as metadata
- Stores images in a "tagged" folder in your Cloudinary account

## Configuration

Key configuration parameters can be adjusted in the source files:

- main.py:
  - `VISION_MODEL`: Model for generating descriptions (default: "llama3.2:3b")
  - `TAGGING_MODEL`: Model for extracting tags (default: "llama3.2:3b")
  - `IMAGE_FOLDER`: Location of source images (default: "images/menswear")
  - `RESET`: Whether to purge existing metadata (default: True)

- manage_cloud.py:
  - `FOLDER_PATH`: Source image folder (default: "images/menswear")
  - `RATE_LIMIT_UPLOAD`: Delay between uploads in seconds (default: 1)

## 🔄 Workflow

1. Place product images in the configured image folder
2. Run main.py to process images and generate metadata
3. Review the generated metadata in image_metadata.json
4. Run manage_cloud.py to upload images with metadata to Cloudinary
5. Access your tagged images in the Cloudinary dashboard
