import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Literal
from PIL import Image
from pydub import AudioSegment
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

def assemble_video() -> mpy.VideoFileClip:
    """
    Assemble the final video using the processed assets and timeline
    """
    # Load timeline
    with open(Path('output') / 'sync_log.txt', 'r') as f:
        timeline = json.load(f)
    
    # Create video clips from images
    clips = []
    for entry in timeline:
        img_clip = ImageClip(entry['image'])
        img_clip = img_clip.set_duration(entry['duration'])
        clips.append(img_clip)
    
    # Concatenate all image clips
    final_clip = concatenate_videoclips(clips, method="compose")
    
    # Add narration audio
    narration_path = next(Path('assets').glob('narration.*'))
    narration = AudioFileClip(str(narration_path))
    
    # Add background music
    music_path = next(Path('assets').glob('background_music.*'))
    background_music = AudioFileClip(str(music_path))
    
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
    
    if format_ratio == '16:9':
        # For landscape, maintain original aspect ratio
        final = clip.resize(width=target_width, height=target_height)
    else:
        if format_ratio == '9:16':
            # For portrait, crop sides and scale
            crop_width = clip.w * (9/16)
            x_center = (clip.w - crop_width) / 2
            final = (clip
                    .crop(x1=x_center, y1=0, x2=x_center + crop_width, y2=clip.h)
                    .resize(width=target_width, height=target_height))
        else:  # 1:1
            # For square, crop to center
            if clip.w > clip.h:
                # Landscape source: crop sides
                crop_size = clip.h
                x_center = (clip.w - crop_size) / 2
                final = (clip
                        .crop(x1=x_center, y1=0, x2=x_center + crop_size, y2=crop_size)
                        .resize(width=target_width, height=target_height))
            else:
                # Portrait source: crop top/bottom
                crop_size = clip.w
                y_center = (clip.h - crop_size) / 2
                final = (clip
                        .crop(x1=0, y1=y_center, x2=crop_size, y2=y_center + crop_size)
                        .resize(width=target_width, height=target_height))
    
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
    main()
