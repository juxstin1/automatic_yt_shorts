import os
import json
from pathlib import Path
from typing import List, Tuple, Dict
from PIL import Image
from pydub import AudioSegment

VALID_IMAGE_FORMATS = {'.jpg', '.png', '.jpeg'}
VALID_AUDIO_FORMATS = {'.mp3', '.wav'}
TARGET_RESOLUTION = (1920, 1080)  # 16:9 HD resolution

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

def process_inputs() -> Tuple[float, List[Dict]]:
    """
    Process input audio and images, returning audio duration and image metadata
    Returns: Tuple of (audio_duration: float, image_metadata: List[Dict])
    """
    assets_dir = Path('assets')
    
    # Process narration audio
    narration_files = list(assets_dir.glob('narration.*'))
    narration_path = narration_files[0]
    audio = AudioSegment.from_file(str(narration_path))
    audio_duration = len(audio) / 1000.0  # Convert to seconds
    
    # Process images
    image_files = [f for f in assets_dir.glob('*') if f.suffix.lower() in VALID_IMAGE_FORMATS]
    image_files.sort()  # Ensure consistent ordering
    
    image_metadata = []
    for img_path in image_files:
        with Image.open(img_path) as img:
            # Resize image maintaining aspect ratio
            img.thumbnail(TARGET_RESOLUTION, Image.Resampling.LANCZOS)
            # Save processed image
            output_path = Path('output') / f"processed_{img_path.name}"
            img.save(output_path)
            
            metadata = {
                'original_path': str(img_path),
                'processed_path': str(output_path),
                'size': img.size,
                'aspect_ratio': f"{img.size[0]}/{img.size[1]}"
            }
            image_metadata.append(metadata)
    
    return audio_duration, image_metadata

def sync_assets(audio_duration: float, image_metadata: List[Dict]) -> None:
    """
    Create a timeline syncing images with audio duration
    """
    num_images = len(image_metadata)
    time_per_image = audio_duration / num_images
    
    timeline = []
    current_time = 0.0
    
    for idx, img_data in enumerate(image_metadata):
        entry = {
            'image': img_data['processed_path'],
            'start_time': current_time,
            'end_time': current_time + time_per_image,
            'duration': time_per_image
        }
        timeline.append(entry)
        current_time += time_per_image
    
    # Save timeline to output/sync_log.txt
    output_path = Path('output') / 'sync_log.txt'
    with open(output_path, 'w') as f:
        json.dump(timeline, f, indent=2)
        
    print(f"Timeline created with {num_images} images")
    print(f"Each image will display for {time_per_image:.2f} seconds")
    print(f"Total duration: {audio_duration:.2f} seconds")

def main():
    is_valid, errors = validate_assets()
    if not is_valid:
        print("Asset validation failed:")
        for error in errors:
            print(f"- {error}")
        return
    
    print("All assets validated successfully!")
    
    try:
        print("\nProcessing inputs...")
        audio_duration, image_metadata = process_inputs()
        
        print("\nCreating timeline...")
        sync_assets(audio_duration, image_metadata)
        
        print("\nProcessing complete! Check output/sync_log.txt for timeline details")
    except Exception as e:
        print(f"Error during processing: {str(e)}")

if __name__ == "__main__":
    main()
