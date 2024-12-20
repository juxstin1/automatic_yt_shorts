import os
from pathlib import Path
from typing import List, Tuple

VALID_IMAGE_FORMATS = {'.jpg', '.png', '.jpeg'}
VALID_AUDIO_FORMATS = {'.mp3', '.wav'}

def validate_assets() -> Tuple[bool, List[str]]:
    """
    Validates the presence and format of required assets.
    Returns: Tuple of (is_valid: bool, error_messages: List[str])
    """
    errors = []
    assets_dir = Path('assets')
    
    # Check if assets directory exists
    if not assets_dir.exists():
        return False, ["Assets directory not found. Please create 'assets' directory."]
    
    # Check for narration audio
    narration_files = list(assets_dir.glob('narration.*'))
    if not narration_files:
        errors.append("No narration audio file found in assets directory.")
    else:
        if not any(f.suffix.lower() in VALID_AUDIO_FORMATS for f in narration_files):
            errors.append(f"Narration audio must be in one of these formats: {VALID_AUDIO_FORMATS}")
    
    # Check for background music
    music_files = list(assets_dir.glob('background_music.*'))
    if not music_files:
        errors.append("No background music file found in assets directory.")
    else:
        if not any(f.suffix.lower() in VALID_AUDIO_FORMATS for f in music_files):
            errors.append(f"Background music must be in one of these formats: {VALID_AUDIO_FORMATS}")
    
    # Check for images
    image_files = list(assets_dir.glob('*'))
    image_files = [f for f in image_files if f.suffix.lower() in VALID_IMAGE_FORMATS]
    if not image_files:
        errors.append(f"No image files found. Please add images in formats: {VALID_IMAGE_FORMATS}")
    
    # Check output directory
    output_dir = Path('output')
    if not output_dir.exists():
        return False, ["Output directory not found. Please create 'output' directory."]
    
    return len(errors) == 0, errors

def main():
    is_valid, errors = validate_assets()
    if not is_valid:
        print("Asset validation failed:")
        for error in errors:
            print(f"- {error}")
        return
    
    print("All assets validated successfully!")

if __name__ == "__main__":
    main()
