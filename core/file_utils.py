from datetime import datetime
import os
import json
from rapidfuzz import fuzz
from pathlib import Path
import ast

# Get all folders recursively under Desktop
desktop_dir = Path.home() / "Desktop"
KNOWN_FOLDERS = {
    folder.name.lower(): str(folder)
    for folder in desktop_dir.rglob("*")
    if folder.is_dir()
}

KNOWN_FOLDERS["desktop"] = str(desktop_dir)

LOG_FILE = "file_actions_log.json"

def log_action(action, source, destination, is_redo=False):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "source": source,
        "destination": destination,
        "is_redo": is_redo
    }

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_latest_log_action():
    if not os.path.exists(LOG_FILE):
        return None
    with open(LOG_FILE, "r") as f:
        data = json.load(f)
        return data[-1] if data else None

def get_latest_file(folder_path):
    try:
        entries = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) or os.path.isdir(os.path.join(folder_path, f))
        ]
        return max(entries, key=os.path.getctime) if entries else None
    except Exception as e:
        print(f"Error accessing folder {folder_path}: {e}")
        return None

def find_file_by_name_all_folders(folders, filename):
    candidates = []
    for folder in folders.values():
        try:
            entries = os.listdir(folder)
            for entry in entries:
                full_path = os.path.join(folder, entry)
                if os.path.isfile(full_path) or os.path.isdir(full_path):
                    score = fuzz.ratio(entry.lower(), filename.lower())
                    if score > 90:
                        print(f"Checking: {full_path}, Score: {score}")
                    candidates.append((score, full_path))
        except Exception as e:
            print(f"Skipping folder {folder} due to error: {e}")
            continue

    strong_matches = [c for c in candidates if c[0] > 80]
    if len(strong_matches) > 1:
        print("Multiple files/folders matched with high confidence:")
        return None

    if not candidates:
        return None

    best_match = max(candidates, key=lambda x: x[0])
    print(f"Best match score: {best_match[0]} for: {best_match[1]}")
    return best_match[1] if best_match[0] > 80 else None

def match_folder_by_name(folders, target_name):
    candidates = [
        (fuzz.ratio(name.lower(), target_name.lower()), path)
        for name, path in folders.items()
    ]

    strong_matches = [c for c in candidates if c[0] > 80]
    if len(strong_matches) > 1:
        print("Multiple target folders matched with high confidence:")
        for score, path in strong_matches:
            print(f"  {score}: {path}")
        return None

    if not candidates:
        return None

    best_match = max(candidates, key=lambda x: x[0])
    print(f"Matched target folder '{target_name}' with score {best_match[0]} -> {best_match[1]}")
    return best_match[1] if best_match[0] > 80 else None