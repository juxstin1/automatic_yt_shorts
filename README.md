# Video Creator

A Python application that creates videos from images with narration and background music.

## Features

- User-friendly GUI for asset selection
- Supports multiple image formats (JPG, PNG)
- Supports multiple audio formats (MP3, WAV)
- Automatic image scaling and transitions
- Background music mixing with narration
- Exports in multiple aspect ratios (16:9, 9:16, 1:1)
- Comprehensive logging system

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Project Structure

```
project/
│
├── assets/           # Place your input files here
│   ├── images/      # Your image files (.jpg, .png)
│   ├── narration    # Your narration audio (.mp3, .wav)
│   └── background   # Your background music (.mp3, .wav)
│
├── output/          # Generated videos and logs
│   └── logs/       # Processing logs
│
├── main.py          # Core processing logic
├── ui.py           # GUI implementation
├── utils.py        # Utility functions
└── requirements.txt # Project dependencies
```

## Usage

1. Start the application:
```bash
python ui.py
```

2. Using the GUI:
   - Click "Select Images Folder" to choose your images
   - Click "Select Narration Audio" to choose your narration
   - Click "Select Background Music" to choose background music
   - Click "Create Video" to generate the video

3. Find your videos:
   - Generated videos will be in the `output` directory
   - Processing logs will be in `output/logs`

## Supported Formats

- Images: .jpg, .jpeg, .png
- Audio: .mp3, .wav
- Output: .mp4 (H.264 codec)

## Troubleshooting

Check the log files in `output/logs` for detailed processing information and any error messages.

## License

[Your chosen license]

## Contributing

[Your contribution guidelines]
