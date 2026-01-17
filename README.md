# Plutos - Poker Analysis Helper

A personal poker gameplay analysis and decision support tool for preflop strategy training.

## Features

- Real-time screen capture of poker table windows
- Card recognition via template matching and OCR
- Hero position and active players detection
- Preflop decision recommendations based on configurable charts
- Multi-table support (up to 4 windows)
- Transparent overlay per table with recommendations
- SQLite database for session logging and analysis

## Requirements

- Windows 10/11
- Python 3.11+
- Tesseract OCR installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`

## Installation

1. Clone the repository:

```bash
git clone <your-private-repo-url>
cd plutos
```

2. Create and activate virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Prepare template images:
   - Place suit templates in `templates/` folder (spades.png, hearts.png, diamonds.png, clubs.png)
   - Place number templates in `number_templates/` folder (2.png ... A.png)

## Usage

Run the main application:

```bash
python -m src.app.main
```

## Project Structure

```
plutos/
├── src/
│   ├── app/
│   │   ├── main.py           # Application entrypoint
│   │   └── config.py         # Configuration and thresholds
│   ├── capture/
│   │   ├── screen_capture.py # MSS screen capture
│   │   └── window_manager.py # Window detection and registry
│   ├── vision/
│   │   ├── card_recognition.py # Card detection and validation
│   │   └── ui_state.py       # Turn detection by pixel/UI state
│   ├── poker/
│   │   ├── preflop_engine.py # Preflop decision logic
│   │   ├── positions.py      # Seat and position mapping
│   │   └── models.py         # Data models (dataclasses)
│   ├── overlay/
│   │   └── overlay_window.py # Transparent overlay per window
│   ├── workers/
│   │   ├── poller.py         # State polling worker
│   │   └── persister.py      # Database persistence worker
│   └── storage/
│       ├── db.py             # SQLite connection helper
│       └── schema.sql        # Database schema
├── tests/
│   └── ...                   # Unit tests
├── templates/                # Suit template images
├── number_templates/         # Number template images
├── requirements.txt
├── README.md
└── .gitignore
```

## Git Workflow

- `main` - stable releases only
- `develop` - integration branch
- `feature/<name>` - feature branches

### Initial Setup Commands

Repository is already initialized. To connect to your private remote:

```bash
# Add your private remote (GitHub or GitLab)
git remote add origin git@github.com:YOUR_USERNAME/plutos.git

# Or with HTTPS:
# git remote add origin https://github.com/YOUR_USERNAME/plutos.git

# Push main branch (rename master to main if needed)
git branch -M main
git push -u origin main

# Push develop branch
git checkout develop
git push -u origin develop
```

### Current branches

- `master` / `main` - stable releases
- `develop` - integration branch (current)

### Creating feature branches

```bash
git checkout develop
git checkout -b feature/my-feature-name
# ... make changes ...
git add .
git commit -m "Description of changes"
git push -u origin feature/my-feature-name
```

## Development

Run tests:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## Configuration

Edit `src/app/config.py` to adjust:

- Tesseract path
- Polling frequency
- Template matching thresholds
- Window search patterns
- Debug logging level

## Notes

- This tool is for personal gameplay analysis only
- Does not automate any actions - only shows recommendations
- Keep your repository private
