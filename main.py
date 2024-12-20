import os
import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Literal
from PIL import Image
from pydub import AudioSegment
from moviepy.editor import (VideoFileClip, ImageClip, AudioFileClip, 
                          concatenate_videoclips, CompositeVideoClip)
import moviepy.editor as mpy

VALID_IMAGE_FORMATS = {'.jpg', '.png', '.jpeg'}
VALID_AUDIO_FORMATS = {'.mp3', '.wav'}
# Video format configurations
FORMAT_CONFIGS = {
    '16:9': {'width': 1920, 'height': 1080},  # Landscape HD
    '9:16': {'width': 1080, 'height': 1920},  # Portrait (Stories/Reels)
    '1:1': {'width': 1080, 'height': 1080},   # Square
}

TARGET_RESOLUTION = (1920, 1080)  # Default 16:9 HD resolution

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
            # Calculate scaling factors
            width_ratio = TARGET_RESOLUTION[0] / img.size[0]
            height_ratio = TARGET_RESOLUTION[1] / img.size[1]
            scale_factor = max(width_ratio, height_ratio)
            
            # Scale up to fill screen
            new_size = (
                int(img.size[0] * scale_factor),
                int(img.size[1] * scale_factor)
            )
            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Center crop if needed
            left = (new_size[0] - TARGET_RESOLUTION[0]) // 2
            top = (new_size[1] - TARGET_RESOLUTION[1]) // 2
            right = left + TARGET_RESOLUTION[0]
            bottom = top + TARGET_RESOLUTION[1]
            
            img_final = img_resized.crop((left, top, right, bottom))
            
            metadata = {
                'path': str(img_path),
                'size': TARGET_RESOLUTION,
                'crop_box': (left, top, right, bottom),
                'scale_factor': scale_factor
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
            'image': img_data['path'],
            'start_time': current_time,
            'end_time': current_time + time_per_image,
            'duration': time_per_image,
            'crop_box': img_data['crop_box'],
            'scale_factor': img_data['scale_factor']
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

def assemble_video() -> mpy.VideoFileClip:
    """
    Assemble the final video using the processed assets and timeline
    """
    # Load timeline
    with open(Path('output') / 'sync_log.txt', 'r') as f:
        timeline = json.load(f)
    
    # Create video clips from images using pre-calculated dimensions
    clips = []
    for entry in timeline:
        # Load and process image
        with Image.open(entry['image']) as img:
            # Scale image using pre-calculated factor
            new_size = (
                int(img.size[0] * entry['scale_factor']),
                int(img.size[1] * entry['scale_factor'])
            )
            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Crop using pre-calculated box
            img_final = img_resized.crop(entry['crop_box'])
            
        # Convert PIL image to MoviePy clip
        img_array = np.array(img_final)
        img_clip = mpy.ImageClip(img_array).set_duration(entry['duration'])
        clips.append(img_clip)
    
    # Concatenate all image clips
    final_clip = mpy.concatenate_videoclips(clips, method="compose")
    
    # Add narration audio
    narration_path = next(Path('assets').glob('narration.*'))
    narration = mpy.AudioFileClip(str(narration_path))
    
    # Add background music
    music_path = next(Path('assets').glob('background_music.*'))
    background_music = mpy.AudioFileClip(str(music_path))
    
    # Loop background music if shorter than video
    if background_music.duration < final_clip.duration:
        background_music = background_music.loop(duration=final_clip.duration)
    else:
        background_music = background_music.subclip(0, final_clip.duration)
    
    # Set background music volume to 20% of original
    background_music = background_music.volumex(0.2)
    
    # Combine audio tracks
    final_audio = narration.audio_fadeout(1)
    final_audio = final_audio.mix(background_music.audio_fadeout(2))
    
    # Set the audio to the video
    final_clip = final_clip.set_audio(final_audio)
    
    return final_clip

def export_video(clip: mpy.VideoFileClip, format_ratio: Literal['16:9', '9:16', '1:1'] = '16:9') -> None:
    """
    Export video in specified aspect ratio with appropriate padding/cropping
    """
    config = FORMAT_CONFIGS[format_ratio]
    target_width = config['width']
    target_height = config['height']
    
    # Calculate scaling factors
    width_ratio = target_width / clip.w
    height_ratio = target_height / clip.h
    
    # Calculate scaling factors to fill the target resolution
    width_ratio = target_width / clip.w
    height_ratio = target_height / clip.h
    scale_factor = max(width_ratio, height_ratio)
    
    # Scale up to fill screen
    scaled_width = int(clip.w * scale_factor)
    scaled_height = int(clip.h * scale_factor)
    
    # Resize while maintaining quality
    scaled_clip = clip.resize(width=scaled_width, height=scaled_height)
    
    # Center crop to target resolution
    x_center = (scaled_width - target_width) // 2
    y_center = (scaled_height - target_height) // 2
    
    final = scaled_clip.crop(
        x1=x_center,
        y1=y_center,
        x2=x_center + target_width,
        y2=y_center + target_height
    )
    
    # Export with format-specific filename
    output_path = Path('output') / f'video_{format_ratio.replace(":", "x")}.mp4'
    final.write_videofile(
        str(output_path),
        fps=30,
        codec='libx264',
        audio_codec='aac'
    )
    final.close()

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
        
        print("\nAssembling video...")
        final_clip = assemble_video()
        
        print("\nExporting videos in different formats...")
        # Export in all supported formats
        for format_ratio in FORMAT_CONFIGS.keys():
            print(f"Exporting {format_ratio} version...")
            export_video(final_clip, format_ratio)
        
        # Clean up
        final_clip.close()
        
        print("\nProcessing complete! Videos exported to output directory")
    except Exception as e:
        print(f"Error during processing: {str(e)}")

if __name__ == "__main__":
    from ui import VideoCreatorUI
    app = VideoCreatorUI()
    app.run()
