from core.file_utils import *
from openai import OpenAI
import shutil

client = OpenAI(api_key="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")

def confirm(filename, prompt="Are you sure? (yes/no): "):
    response = input(prompt + " " + filename).strip().lower()
    return response in ["yes", "y"]

def parse_instruction(text):
    system_prompt = """Extract user intent and convert to one of the following JSON formats:

    1. For file operations:
    {'action': move/copy/delete/create/redo, 'source_filename': optional, 'target_folder': optional}

    2. For search queries:
    {'action': 'search', 'query': <description of the file being searched for>}

    If user says 'redo', return only {'action': 'redo'}.
    """  

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
    )

    content = response.choices[0].message.content.strip()

    try:
        return ast.literal_eval(content)
    except Exception:
        print("Invalid instruction format:", content)
        return None

def execute_command(cmd):
    result = []
    destination_path = None
    action = cmd['action']

    if action == "search":
        query = cmd.get("query", "")
        result.append(f"Searching for file matching: \"{query}\"")

        candidates = []
        EXCLUDED_PATHS = ['site-packages', '__pycache__', 'venv', '.git', '.env', 'node_modules', 'test', 'tests']

        for folder in KNOWN_FOLDERS.values():
            if any(excl in folder for excl in EXCLUDED_PATHS):
                continue
            try:
                for f in os.listdir(folder):
                    full_path = os.path.join(folder, f)
                    if os.path.isfile(full_path) or os.path.isdir(full_path):
                        score = fuzz.token_set_ratio(f.lower(), query.lower())
                        candidates.append((score, full_path))
            except:
                continue

        if not candidates:
            result.append("No matching files found.")
            return "\n".join(result)

        candidates.sort(reverse=True)
        top_matches = [c for c in candidates if c[0] > 60][:5]
        if not top_matches:
            result.append("No strong matches found.")
            return "\n".join(result)

        result.append("Top matching files/folders:")
        for score, path in top_matches:
            result.append(f"[{score}] {path}")
        return "\n".join(result)

    if not isinstance(cmd, dict) or 'action' not in cmd:
        result.append("Invalid command format.")
        return "\n".join(result)

    if action == "redo":
        last = load_latest_log_action()
        if not last:
            result.append("No previous action to redo.")
            return "\n".join(result)
        if last.get("is_redo"):
            result.append("Redo has already been called for the last action.")
            return "\n".join(result)
        source_file = last["destination"]
        destination_path = os.path.dirname(last["source"])
        try:
            if last['action'] == "move":
                shutil.move(source_file, os.path.join(destination_path, os.path.basename(source_file)))
                log_action("move", source_file, os.path.join(destination_path, os.path.basename(source_file)), is_redo=True)
                result.append(f"Redone move: {source_file} -> {destination_path}")
        except Exception as e:
            result.append(f"Redo failed: {e}")
        return "\n".join(result)

    target_folder = None
    if action in ["move", "copy", "create"]:
        target_folder = match_folder_by_name(KNOWN_FOLDERS, cmd.get("target_folder"))
        if not target_folder:
            result.append("Target folder not found.")
            return "\n".join(result)

    if action == "create":
        folder_path = os.path.join(target_folder, cmd.get("source_filename", "").strip())
        if not folder_path:
            result.append("Folder name missing.")
            return "\n".join(result)
        try:
            os.makedirs(folder_path, exist_ok=True)
            log_action("create", None, folder_path)
            result.append(f"Created folder: {folder_path}")
        except Exception as e:
            result.append(f"Create failed: {e}")
        return "\n".join(result)

    # All others need to resolve source file
    if 'source_filename' not in cmd or cmd['source_filename'].lower() == 'latest download':
        source_file = None
        latest_time = 0
        for folder in KNOWN_FOLDERS.values():
            try:
                for f in os.listdir(folder):
                    full_path = os.path.join(folder, f)
                    if os.path.isfile(full_path) or os.path.isdir(full_path):
                        t = os.path.getctime(full_path)
                        if t > latest_time:
                            latest_time = t
                            source_file = full_path
            except:
                continue
    else:
        source_file = find_file_by_name_all_folders(KNOWN_FOLDERS, cmd['source_filename'])

    if not source_file or not os.path.exists(source_file):
        result.append("Source file not found.")
        return "\n".join(result)

    if target_folder:
        destination_path = os.path.join(target_folder, os.path.basename(source_file))

    try:
        if action == "move":
            shutil.move(source_file, destination_path)
        elif action == "copy":
            if os.path.isdir(source_file):
                shutil.copytree(source_file, destination_path)
            else:
                shutil.copy2(source_file, destination_path)
        elif action == "delete":
            result.append(f"Request to delete: {source_file}")
            if not confirm("Are you sure you want to delete this? (yes/no): ", source_file):
                result.append("Delete cancelled.")
                return "\n".join(result)
            if os.path.isdir(source_file):
                shutil.rmtree(source_file)
            else:
                os.remove(source_file)
        else:
            result.append("Unsupported action.")
            return "\n".join(result)

        if action == "delete":
            log_action("delete", source_file, None)
            result.append(f"Deleted {source_file}")
        else:
            log_action(action, source_file, destination_path)
            result.append(f"{action.capitalize()}d {source_file} to {destination_path}")

    except Exception as e:
        result.append(f"Operation failed: {e}")

    return "\n".join(result)