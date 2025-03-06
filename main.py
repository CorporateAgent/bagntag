#!/usr/bin/env python3
"""
Advanced Image Processing and Metadata Generation System

Multi-Tier Approach:
    1) First, use a vision model to produce a textual description (description).
    2) Second, use a tagging model to extract relevant tags from the description.

Key Features:
    - Configurable model selection for each task
    - Progressive state saving with automatic backup generation
    - Structured metadata output in JSON format
    - Fault-tolerant processing pipeline with resume capability
    - Flexible and modular design

Technical Requirements:
    pip install ollama colorama tabulate

Last Updated: January 2025
"""

import os
import json
import time
import re
import ollama
import colorama
from colorama import Fore, Style
from tabulate import tabulate

colorama.init(autoreset=True)

### CONFIGURATION PARAMETERS ###
VISION_MODEL = "llama3.2:3b"          # Model for generating explanations from images
TAGGING_MODEL = "llama3.2:3b"      # Model for extracting tags from explanations
IMAGE_FOLDER = "images/menswear"            # Folder containing images to process
JSON_FILE = "data/image_metadata.json"  # Metadata storage file
RATE_LIMIT = 3                     # Rate limit in seconds between API calls
CATEGORIES_FILE = "data/categories.json"  # Path to JSON file with valid tags
RESET = True                      # Set to True to purge past metadata and start fresh

IMAGE_PROMPT = (
    """

“You are an advanced image analysis model assisting in creating detailed descriptions for our e-commerce platform. Analyze the attached image from a product shoot and provide a professional description. Focus exclusively on products relevant to the shoot’s department, which will be one of the following: Home, Sports, Men, Women, Kids, or Tech. We never shoot for all departments at once, so omit products from unrelated departments, even if visible in the image.
Your task:
	1.	Identify the main products from the relevant department, referencing them specifically (e.g., vest, trousers, accessories).
	2.	Describe these products with attention to detail, including aspects like design, material, fit, color, and texture.
	3.	Highlight how the setting complements the products, focusing on how the background and context elevate the items being featured.
	4.	Suggest potential product callouts for marketing (e.g., “Versatile vest,” “Bold trousers”).
	5.	Avoid reasoning or explanation about why the image fits the department; focus solely on providing a polished product description.
	6.	Limit the response to 200 words and format it like an editorial feature.

Expected Output Example:

The image showcases a tranquil outdoor setting, focusing on men’s casualwear. At the center of the frame is a seated male model, dressed in a white sleeveless vest paired with burnt-orange trousers, ideal for a relaxed, sunny day. The vest serves as a versatile wardrobe essential, offering a minimalist yet stylish choice for warm weather. The trousers, with their earthy tone and comfortable fit, add a pop of subtle color, making them a standout piece for outdoor leisure or casual gatherings. Around the model’s neck, a bandana with logo that reads "fabiani" or scarf introduces a tasteful accessory, elevating the outfit with a simple yet impactful detail.
The surrounding setting highlights the versatility of these menswear pieces in natural environments. A tire swing, held by another individual, frames the model and reinforces themes of carefree outdoor living. The lush green grass and vibrant blue sky create a bright, open backdrop that enhances the vibrancy of the clothing. The sunlight highlights the fabric textures and color details, drawing attention to the simplicity and elegance of the menswear ensemble.
This image positions the vest as a must-have for summer layering and the burnt-orange trousers as a bold, fashionable statement piece, perfect for customers seeking stylish comfort.
    """
)

TAG_RULES = (
    "Rules:\n"
    "- Do not invent new tags.\n"
    "- Only choose tags directly relevant to the explanation.\n"
    "- Return the tags as a comma-separated list.\n\n"
)

class BashAutoTagger:
    """
    Core class handling image processing and metadata generation.
    """
    def __init__(self, folder_name):
        self.image_folder = folder_name
        self.json_file = JSON_FILE
        self.image_data = self._load_or_create_metadata()
        self.valid_tags = self.load_valid_tags(CATEGORIES_FILE)

    def load_valid_tags(self, path: str) -> list:
        """
        Load valid tags from a JSON file.
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("valid_tags", [])
        except Exception as e:
            print(f"{Fore.RED}Error loading valid tags from {path}: {e}")
            return []

    def _load_or_create_metadata(self):
        """
        Load existing metadata file or initialize a new state.
        """
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"{Fore.GREEN}Resuming from existing metadata state")
                return data
            except json.JSONDecodeError:
                print(f"{Fore.RED}Metadata file corruption detected. Initializing new state.")

        return {
            "metadata": {
                "total_images": 0,
                "processed_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_folder": self.image_folder,
                "last_processed": None
            },
            "images": []
        }

    def save_metadata(self):
        """
        Saves current state to JSON and creates a backup.
        """
        if os.path.exists(self.json_file):
            backup_file = f"{self.json_file}.bak"
            try:
                with open(self.json_file, 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            except Exception as e:
                print(f"{Fore.RED}Warning: Backup creation failed: {e}")

        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.image_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{Fore.RED}Critical: State persistence failed: {e}")
            raise

    def get_processed_files(self):
        """
        Returns a set of filenames that have been processed so far.
        """
        return {img["filename"] for img in self.image_data["images"]}

    def get_image_description(self, image_path: str) -> str:
        """
        STEP 1: Use the vision model to produce a textual description of the image.

        Args:
            image_path (str): Path to the image file

        Returns:
            str: The text description of the image content (description)
        """
        messages = [
            {
                "role": "user",
                "content": IMAGE_PROMPT,
                "images": [image_path],
            }
        ]

        try:
            response = ollama.chat(model=VISION_MODEL, messages=messages)
            description = response.get("message", {}).get("content", "").strip()
            return description
        except Exception as e:
            print(f"{Fore.RED}Vision Model API call failed: {e}")
            return "Error: Unable to retrieve description."

    def get_tags_from_explanation(self, explanation: str) -> list:
        """
        STEP 2: Use the tagging model to extract relevant tags from the explanation.

        Args:
            explanation (str): The explanation generated from the image description.

        Returns:
            list: A list of valid tags extracted from the explanation.
        """
        tag_prompt = (
            "From the following explanation, select relevant tags ONLY from this list:\n"
            f"{', '.join(self.valid_tags)}\n\n"
            f"{TAG_RULES}"
            f"Explanation:\n{explanation}"
        )

        messages = [
            {
                "role": "user",
                "content": tag_prompt,
            }
        ]

        try:
            response = ollama.chat(model=TAGGING_MODEL, messages=messages)
            # Split tags based on comma and filter by valid_tags
            tags = response.get("message", {}).get("content", "").strip().split(',')
            tags = [tag.strip() for tag in tags if tag.strip() in self.valid_tags]
            return tags
        except Exception as e:
            print(f"{Fore.RED}Tagging Model API call failed: {e}")
            return []

    def process_images(self):
        """
        Main processing pipeline:
            1) Check folder validity
            2) Get list of new images to process
            3) For each image: get description -> extract tags -> save to metadata
        """
        if not os.path.isdir(self.image_folder):
            print(f"{Fore.RED}Target directory '{self.image_folder}' not found. Aborting.")
            return

        image_paths = [
            os.path.join(self.image_folder, f)
            for f in os.listdir(self.image_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
        ]

        processed_files = self.get_processed_files()
        remaining_images = [img for img in image_paths if os.path.basename(img) not in processed_files]

        print(f"{Fore.BLUE}Processing queue: {len(remaining_images)} images")
        print(f"{Fore.BLUE}Previously processed: {len(processed_files)} images")

        for img_path in remaining_images:
            filename = os.path.basename(img_path)
            print(f"\nProcessing: {filename}")

            try:
                # Step 1: Get textual description from vision model
                description = self.get_image_description(img_path)
                # Step 2: From that description, extract relevant tags
                tags = self.get_tags_from_explanation(description)

                image_entry = {
                    "id": os.path.splitext(filename)[0],
                    "filename": filename,
                    "metadata": {
                        "description": description,
                        "tags": tags,
                        "processed_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }

                self.image_data["images"].append(image_entry)
                self.image_data["metadata"]["last_processed"] = filename
                self.image_data["metadata"]["total_images"] = len(self.image_data["images"])

                # Persist results to disk
                self.save_metadata()

                print(f"{Fore.GREEN}Description:\n{description}")
                print(f"{Fore.GREEN}Tags:{Style.BRIGHT}\n{', '.join(tags) if tags else 'No tags found'}")
                print(f"{Style.DIM}Implementing rate limit...")
                time.sleep(RATE_LIMIT)

            except Exception as e:
                print(f"{Fore.RED}Processing failed for {filename}: {e}")
                continue

        self.print_summary()

    def print_summary(self):
        """
        Prints a summary of the processed images.
        """
        print(f"\n{Fore.BLUE}Processing Summary Report:")
        table_data = [["ID", "Filename", "# Tags"]]
        for img in self.image_data["images"]:
            table_data.append([
                img["id"],
                img["filename"],
                len(img["metadata"]["tags"])
            ])

        print(tabulate(table_data, headers="firstrow", tablefmt="fancy_grid"))
        print(f"{Fore.GREEN}\nMetadata persisted to {self.json_file}")
        print(f"{Fore.BLUE}Pipeline execution complete")

def main():
    if RESET:
        # Purge past metadata if RESET is True
        if os.path.exists(JSON_FILE):
            try:
                os.remove(JSON_FILE)
                print(f"{Fore.YELLOW}Reset enabled: Existing metadata purged.")
            except Exception as e:
                print(f"{Fore.RED}Error purging metadata: {e}")
    processor = BashAutoTagger(IMAGE_FOLDER)
    processor.process_images()

if __name__ == "__main__":
    main()