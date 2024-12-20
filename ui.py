import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from pathlib import Path
import main
import os
import shutil

class VideoCreatorUI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Video Creator")
        self.window.geometry("800x600")
        
        # Paths for asset folders
        self.image_path = None
        self.narration_path = None
        self.music_path = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title = ctk.CTkLabel(self.window, text="Video Creator", font=("Arial", 24))
        title.pack(pady=20)
        
        # Asset Selection Frame
        asset_frame = ctk.CTkFrame(self.window)
        asset_frame.pack(pady=20, padx=20, fill="x")
        
        # Images Folder Selection
        img_btn = ctk.CTkButton(
            asset_frame, 
            text="Select Images Folder", 
            command=self.select_images_folder
        )
        img_btn.pack(pady=10)
        
        self.img_label = ctk.CTkLabel(asset_frame, text="No folder selected")
        self.img_label.pack()
        
        # Narration File Selection
        narr_btn = ctk.CTkButton(
            asset_frame, 
            text="Select Narration Audio", 
            command=self.select_narration
        )
        narr_btn.pack(pady=10)
        
        self.narr_label = ctk.CTkLabel(asset_frame, text="No file selected")
        self.narr_label.pack()
        
        # Background Music Selection
        music_btn = ctk.CTkButton(
            asset_frame, 
            text="Select Background Music", 
            command=self.select_music
        )
        music_btn.pack(pady=10)
        
        self.music_label = ctk.CTkLabel(asset_frame, text="No file selected")
        self.music_label.pack()
        
        # Create Video Button
        create_btn = ctk.CTkButton(
            self.window,
            text="Create Video",
            command=self.create_video,
            width=200,
            height=50,
            font=("Arial", 18)
        )
        create_btn.pack(pady=30)
        
        # Status Label
        self.status_label = ctk.CTkLabel(
            self.window,
            text="Ready",
            font=("Arial", 16)
        )
        self.status_label.pack(pady=10)
        
    def select_images_folder(self):
        folder = filedialog.askdirectory(title="Select Images Folder")
        if folder:
            self.image_path = folder
            self.img_label.configure(text=f"Selected: {folder}")
            
    def select_narration(self):
        file = filedialog.askopenfilename(
            title="Select Narration Audio",
            filetypes=[("Audio Files", "*.mp3 *.wav")]
        )
        if file:
            self.narration_path = file
            self.narr_label.configure(text=f"Selected: {file}")
            
    def select_music(self):
        file = filedialog.askopenfilename(
            title="Select Background Music",
            filetypes=[("Audio Files", "*.mp3 *.wav")]
        )
        if file:
            self.music_path = file
            self.music_label.configure(text=f"Selected: {file}")
            
    def create_video(self):
        if not all([self.image_path, self.narration_path, self.music_path]):
            self.status_label.configure(text="Please select all required assets!")
            return
            
        # Ensure assets directory exists
        assets_dir = Path("assets")
        assets_dir.mkdir(exist_ok=True)
        
        # Clear existing assets
        for file in assets_dir.glob("*"):
            if file.is_file():
                file.unlink()
            
        # Copy new assets
        try:
            # Copy images
            for img in Path(self.image_path).glob("*"):
                if img.suffix.lower() in main.VALID_IMAGE_FORMATS:
                    shutil.copy2(img, assets_dir)
            
            # Copy audio files
            narr_ext = Path(self.narration_path).suffix
            shutil.copy2(self.narration_path, assets_dir / f"narration{narr_ext}")
            
            music_ext = Path(self.music_path).suffix
            shutil.copy2(self.music_path, assets_dir / f"background_music{music_ext}")
            
            # Create output directory
            Path("output").mkdir(exist_ok=True)
            
            # Update status
            self.status_label.configure(text="Processing video...")
            self.window.update()
            
            # Run main processing
            main.main()
            
            self.status_label.configure(text="Video created successfully!")
            
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = VideoCreatorUI()
    app.run()
