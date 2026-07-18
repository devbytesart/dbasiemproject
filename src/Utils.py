"""
Copyright 2026 ttdantett DevBytesArt®

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

author: ttdantett
title: siem project
document: utilitaires
"""

import json, os, time, threading, traceback, re
from pathlib import Path
from datetime import datetime
import hashlib
import lz4.frame
import base64, html
import socket
import random
from concurrent.futures import ThreadPoolExecutor
import tarfile
import zipfile
import shutil
import tempfile
from typing import List, Dict, Any, Union
import UtilsEnum as ue
import copy


# Old format "%Y-%m-%d-%H" 
DEFAULT_DATE_FORMAT = "%Y-%m-%d"  # Format by default

def lock_file(file_path, locked=True):
    """Lock or unlock a file by creating or removing a .lock file (atomic)."""
    file_path = Path(file_path)
    lock_file_path = file_path.with_suffix(".lock")
    
    if locked:
        try:
            lock_file_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, 'w') as f:
                f.write(json.dumps({
                    "locked": True,
                    "pid": os.getpid(),
                    "time": time.time()
                }))
            return True
        except FileExistsError:
            return False  # Already locked
        except Exception as e:
            print(f"Error creating lock: {e}")
            return False
    else:
        try:
            if lock_file_path.exists():
                lock_file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error removing lock: {e}")
            return False

def is_locked(file_path):
    """Check if the file is locked by the presence of a .lock file."""
    file_path = Path(file_path)
    return file_path.with_suffix(".lock").exists()



# MERGE DICTS
def merge_dicts(dict1, dict2, op="or", max_thread=5):
    """
    Merges two dictionaries according to the specified logical operator, using threads
    to accelerate the process when the number of keys is large.
    """
    try:
        if not isinstance(dict1, dict) or not isinstance(dict2, dict):
            raise ValueError("Arguments dict1 and dict2 must be dictionaries.")
        
        merged_dict = {}
        keys = set(dict1.keys()).union(dict2.keys())
        threads = []
        thread_results = {}
        
        # Using a semaphor to limit the threads
        semaphore = threading.Semaphore(max_thread)
        
        def process_key(key):
            # Limit number of active threads
            with semaphore:
                val1 = dict1.get(key)
                val2 = dict2.get(key)
                if isinstance(val1, dict) and isinstance(val2, dict):
                    thread_results[key] = merge_dicts(val1, val2, op)
                elif isinstance(val1, list) and isinstance(val2, list):
                    if op == "or":
                        thread_results[key] = list(set(val1).union(val2))
                    elif op == "and":
                        thread_results[key] = list(set(val1).intersection(val2))
                    elif op == "not":
                        # Delete elements of val2 from val1
                        thread_results[key] = list(set(val1).difference(val2))
                elif val1 is not None and val2 is None:
                    # Keep val1 uf if op is "or" or "not"
                    if op in ["or", "not"]:
                        thread_results[key] = val1
                elif val2 is not None and val1 is None:
                    # Convert val2 only if op is "or"
                    if op == "or":
                        thread_results[key] = val2
                elif val1 is not None and val2 is not None:
                    # Convert val1 for "or" else None
                    thread_results[key] = val1 if op == "or" else None
                else:
                    pass  # Not compatible, do nothing

        # Launch thread for each key 
        for key in keys:
            thread = threading.Thread(target=process_key, args=(key,))
            threads.append(thread)
            thread.start()

        # Wait ends of all threads 
        for thread in threads:
            thread.join()

        # Fusion results collected in the final dictionary
        merged_dict.update(thread_results)
        
        return merged_dict
    except Exception as e:
        print("Error during the merging of dictionaries: ", e)
        return {}
    

# MERGE DICTS IDS
def merge_dicts_ids(dict1, dict2, max_thread=5):
    """
    Fusion dict2 and dict1 using threads foreach key, with limit number of thread simultaneously
    """
    try:
        threads = []
        semaphore = threading.Semaphore(max_thread)

        def process_key(key, value):
            # Limit the number of active threads 
            with semaphore:
                if key in dict1:
                    if isinstance(dict1[key], dict) and isinstance(value, dict):
                        # Recursive fusion of subdictionaries
                        merge_dicts_ids(dict1[key], value, max_thread)
                    elif isinstance(dict1[key], list) and isinstance(value, list):
                        # Union lists for this key 
                        dict1[key] = list(set(dict1[key]).union(value))
                    else:
                        # For other type, replace by a copy
                        dict[key] = value
                else:
                    # Add a copy if key does not exists in dict1
                    dict1[key] = value

        # Creation of threads for each key in dict2
        for key, value in dict2.items():
            thread = threading.Thread(target=process_key, args=(key, value))
            threads.append(thread)
            thread.start()

        # Wait end of all threads
        for thread in threads:
            thread.join()

        return dict1
    except Exception as e:
        print("Error in merge_dicts_ids:", traceback.format_exc())
        return {}


def wait_for_unlock(file_path, timeout=30):
    """Wait until the file is unlocked."""
    start_time = time.time()
    while is_locked(file_path):
        time.sleep(0.1)
        if time.time() - start_time > timeout:
            raise TimeoutError(f"The file {file_path} is still locked after {timeout} seconds.")

def wait_for_lock(file_path, timeout=30):
    """Wait until the file is locked."""
    start_time = time.time()
    while not is_locked(file_path):
        try:
            lock_file(file_path)
        except:
            pass
        time.sleep(0.1)
        if time.time() - start_time > timeout:
            raise TimeoutError(f"The file {file_path} is still unlocked after {timeout} seconds.")


def add_file_modif_date(history_path, file_modified, remove=False):
    """Add or remove the modification time of a file in a JSON file."""
    try:
        history_path = Path(history_path)
        file_modified = str(file_modified)

        wait_for_unlock(history_path, timeout=60)

        if not lock_file(history_path, True):
            time.sleep(0.1)
            if not lock_file(history_path, True):
                raise RuntimeError(f"Failed to lock the file {history_path}")
        
        try:
            data = {}

            if history_path.exists():
                with open(history_path, 'r') as json_file:
                    content = json_file.read().strip()
                    if content:
                        try:
                            data = json.loads(content)
                        except json.JSONDecodeError:
                            print(f"Error decoding JSON in {history_path}, backing up...")
                            backup_path = history_path.with_suffix(".json.bak")
                            shutil.copy(history_path, backup_path)
                            data = {}
                    else:
                        data = {}

            if remove:
                data.pop(file_modified, None)
            else:
                data[file_modified] = {
                    "last_modification": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "checksum": calculate_checksum(file_modified)
                }

            with open(history_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
        
        finally:
            lock_file(history_path, False)

        return True

    except RuntimeError:
        print("Error: failed to lock the file")
        return False
    except Exception:
        print("Error in add_file_modif_date:", traceback.format_exc())
        lock_file(history_path, False)
        return False

# COMPARE DICTIONARIES AND SEND ADDED, REMOVED, MODIFIED KEYS
# TODO use this function in configurator insteed
def compare_dicts(old_data, new_data, parent_keys=[]):
    differences = {"added": [], "removed": [], "modified": {}}
    
    # If both are dictionaries
    if isinstance(old_data, dict) and isinstance(new_data, dict):
        all_keys = set(old_data.keys()).union(set(new_data.keys()))
        for key in all_keys:
            if key in old_data and key not in new_data:
                # Deleted key 
                differences["removed"].append(".".join(parent_keys + [key]))
            elif key in new_data and key not in old_data:
                # Added key
                differences["added"].append(".".join(parent_keys + [key]))
            else:
                # Present key in both, recursive comparison
                sub_diff = compare_dicts(old_data[key], new_data[key], parent_keys + [key])
                # Treat modifications with new format
                if sub_diff["added"] or sub_diff["removed"] or sub_diff["modified"]:
                    differences["modified"][key] = {
                        "added": sub_diff["added"],
                        "removed": sub_diff["removed"],
                        "modified": sub_diff["modified"]
                    }

    # If both are lists
    elif isinstance(old_data, list) and isinstance(new_data, list):
        # If lenght of list has changed
        if len(old_data) != len(new_data):
            differences["modified"].append({
                "key": ".".join(parent_keys),
                "old": old_data,
                "new": new_data,
            })
        else:
            for i, (old_item, new_item) in enumerate(zip(old_data, new_data)):
                sub_diff = compare_dicts(old_item, new_item, parent_keys + [str(i)])
                differences["added"].extend(sub_diff["added"])
                differences["removed"].extend(sub_diff["removed"])
                differences["modified"].extend(sub_diff["modified"])

    # If both are simple values (not dictionary or list)
    else:
        if old_data != new_data:
            differences["modified"] = {
                "old": old_data,
                "new": new_data
            }
    
    return differences


# CREATE FOLDERS
# TODO create a version of save file that use create folders in order to avoid error of folders and files does not exists
def create_folders(path):
    """ Create folders if not exist """
    # Split path of file if exists
    dir_path, file_name = os.path.split(path)
    
    # Create required folders
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Folder created : {dir_path}")
    
    # Create final file if specified
    if file_name:
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, 'w') as file:
            file.write("")  
            # Create empty file
        print(f"File created : {file_path}")

# CALCULATE CHECKSUM FILE
def calculate_checksum(file_path):
    """Calculate the checksum of a file."""
    try:
        # Verify if valid path
        if not file_path or not os.path.exists(file_path):
            print(f"Invalid or non-existent file path: {file_path}")
            return "INVALID_CHECKSUM"
        # Read file and compute checksum
        with open(file_path, 'rb') as f:
            file_data = f.read()
        if not file_data:
            print(f"File is empty: {file_path}")
            return "EMPTY_FILE"
        # Compute checksum
        return hashlib.md5(file_data).hexdigest()
    except Exception as e:
        # Enregistrer l'erreur et retourner un checksum invalide
        # Save error and return invalid checksum
        print(f"Error in calculate_checksum for file {file_path}:\n{traceback.format_exc()}")
        return "ERROR_CHECKSUM"
    

# COMPRESS AND DECOMPRESS DATA
COMPRESSION_EXTENSION = "lz4"

def compress_data(data, algorithm=COMPRESSION_EXTENSION):
    if algorithm == "lz4":
        return lz4.frame.compress(data)


def decompress_data(data, algorithm=COMPRESSION_EXTENSION):
    if algorithm == "lz4":
        return lz4.frame.decompress(data)

def is_compressed(file_path):
    """Check if the file is already a compressed archive."""
    compressed_extensions = ('.zip', '.gz', '.tar', '.tar.gz', '.tgz', '.bz2', '.xz')
    return file_path.lower().endswith(compressed_extensions)

def compress_file(file_path, history_path, algorithm="TAR"):
    """Compress a file using the specified algorithm if not already compressed."""
    try:
        if is_compressed(file_path):
            print(f"File '{file_path}' is already compressed. Skipping compression.")
            return
        if algorithm.upper() == "TAR":
            archive_path = file_path + ".tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(file_path, arcname=os.path.basename(file_path))
                # Update the history file
                add_file_modif_date(history_path, archive_path)
            if os.path.exists(file_path):
                os.remove(file_path)
                # Erase the file in the history
                add_file_modif_date(history_path, file_path, True)
        elif algorithm.upper() == "ZIP":
            archive_path = file_path + ".zip"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, arcname=os.path.basename(file_path))
                # Update the history file
                add_file_modif_date(history_path, archive_path)
            if os.path.exists(file_path):
                os.remove(file_path)
                # Erase the file in the history
                add_file_modif_date(history_path, file_path, True)
        else:
            return
            # raise ValueError(f"Unsupported algorithm: {algorithm}")
    except Exception:
        print(f"Error in compress_file for file {file_path}:\n{traceback.format_exc()}")


def uncompress_file(file_path, history_path):
    """Uncompress a file based on its extension. Return path to extracted directory or original file if not compressed."""
    try:
        # Identify compression type
        lower_file = file_path.lower()
        is_tar = lower_file.endswith((".tar.gz", ".tgz"))
        is_zip = lower_file.endswith(".zip")
        if not (is_tar or is_zip):
            # File is not compressed
            return file_path
        base_dir = os.path.dirname(file_path)
        extracted_files = []
        if is_tar:
            with tarfile.open(file_path, "r:gz") as tar:
                tar.extractall(path=base_dir)
                extracted_files = tar.getnames()
        elif is_zip:
            with zipfile.ZipFile(file_path, "r") as zipf:
                zipf.extractall(path=base_dir)
                extracted_files = zipf.namelist()
        # Delete the compressed file
        if os.path.exists(file_path):
            os.remove(file_path)
            add_file_modif_date(history_path, file_path, True)  # Mark as deleted
        # Mark extracted files as created
        for name in extracted_files:
            extracted_path = os.path.join(base_dir, name)
            add_file_modif_date(history_path, extracted_path)
        return base_dir
    except Exception:
        print(f"Error in uncompress_file for file {file_path}:\n{traceback.format_exc()}")
        return None

def uncompress_file_with_copy(file_path):
    """Make a copy of the file, uncompress it, and return the path of the extracted file or folder
    and False if not compressed or True if compressed."""
    try:
        # Identify compression type
        lower_file = file_path.lower()
        is_tar = lower_file.endswith((".tar.gz", ".tgz"))
        is_zip = lower_file.endswith(".zip")
        if not (is_tar or is_zip):
            return file_path, False
        base_dir = os.path.dirname(file_path)
        # Create a temporary copy
        temp_copy_path = os.path.join(base_dir, f"copy_{os.path.basename(file_path)}")
        shutil.copy2(file_path, temp_copy_path)
        extracted_dir = tempfile.mkdtemp(dir=base_dir)  # Create a temp directory for extraction
        extracted_files = []
        if is_tar:
            with tarfile.open(temp_copy_path, "r:gz") as tar:
                tar.extractall(path=extracted_dir)
                extracted_files = tar.getnames()
        elif is_zip:
            with zipfile.ZipFile(temp_copy_path, "r") as zipf:
                zipf.extractall(path=extracted_dir)
                extracted_files = zipf.namelist()
        # Cleanup temp copy
        if os.path.exists(temp_copy_path):
            os.remove(temp_copy_path)
        # Return path to extracted content
        if len(extracted_files) == 1:
            return os.path.join(extracted_dir, extracted_files[0]), True
        return extracted_dir, True
    except Exception:
        print(f"Error in uncompress_file_with_copy for file {file_path}:\n{traceback.format_exc()}")
        return None, False

def encrypt_file(file_path, history_path, key, algorithm="AES256"):
    """ Encrypt a file using the specified algorithm."""
    try:
        # TODO
        pass
    except:
        print(f"Error in encrypt_file for file {file_path}:\n{traceback.format_exc()}")


def decrypt_file(file_path, history_path, key=None, algorithm="AES256"):
        """ Decrypt a file using the specified algorithm."""
        try:
            # TODO
            # Create a copy of the file
            base_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            copied_file_path = os.path.join(base_dir, f"copy_{file_name}")
            shutil.copy2(file_path, copied_file_path)
            return copied_file_path
        except:
            print(f"Error in decrypt_file for file {file_path}:\n{traceback.format_exc()}")


def standardize_file_format(file_path, compression=None, encryption=None, standardization=None):
    """Standardize the file format to a common format."""
    try:
        if not compression and not encryption:
            # The must be uncompressed and unencrypted if case
            extension = os.path.splitext(file_path)[1]

    except:
        print(f"Error in standardize_file_format for file {file_path}:\n{traceback.format_exc()}")

def process_base64_to_html_safe(encoded_data):
    try:
        # Decode Base64
        decoded_bytes = base64.b64decode(encoded_data)
        decoded_str = decoded_bytes.decode('utf-8')
        # Verify if valid JSON
        try:
            parsed_json = json.loads(decoded_str)
            # If JSON, retransform in secured JSON chain
            safe_json_str = json.dumps(parsed_json)
            return html.escape(safe_json_str)  # Encode for HTML
        except json.JSONDecodeError:
            # If not JSON, encode special caracters 
            return html.escape(decoded_str)
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        # In case of decode error, return error
        return "Error during decoding data:" + encoded_data
    

def check_port_in_use(port):
    """Check if the specified port is already in use using a socket connection."""
    try:
        if port is not None and not isinstance(port, int):
            port = int(port)
        
        for t in range(5):  # Retry 5 times
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)  # Set timeout to avoid long waits
                result = sock.connect_ex(("127.0.0.1", port))  # Try to connect
                
                if result == 0:
                    print(f"Port {port} is in use. Retrying...")
                    time.sleep(t)
                else:
                    print(f"Port {port} is available.")
                    return False  # Port is free
        
        print(f"Port {port} is still in use after multiple attempts.")
        return True  # Port is still in use after retries
    except Exception as e:
        print(f"Error checking port {port}: {traceback.format_exc()}")
        return True  # Consider the port as occupied in case of error

def create_unique_id():
    """ Create unique id for logs """
    return (str(time.time()) + str(random.random())).replace(".","")


def sanitize_json(data):
    """
    Recursively traverses a dictionary or a list and escapes string values
    to prevent XSS attacks.
    """
    if isinstance(data, dict):
        return {key: sanitize_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_json(item) for item in data]
    elif isinstance(data, str):
        return html.escape(data)
    else:
        return data  # Return as is if it's not a string, list, or dictionary
    
def sort_records(records, sort_field, reverse=False):
    if not records:
        return []
    sample_value = records[0][sort_field]
    # Détect type
    def detect_type(val):
        try:
            datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
            return "date"
        except:
            try:
                float(val)
                return "number"
            except:
                return "text"
    value_type = detect_type(sample_value)
    # Choice function of conversion according to type
    if value_type == "date":
        parse_fn = lambda x: datetime.strptime(x[sort_field], "%Y-%m-%d %H:%M:%S.%f")
    elif value_type == "number":
        parse_fn = lambda x: float(x[sort_field])
    else:
        parse_fn = lambda x: x[sort_field]
    # Creation tuples (index, sorted key)
    indexed_keys = [(i, parse_fn(row)) for i, row in enumerate(records)]
    # Sort the key
    sorted_indices = sorted(indexed_keys, key=lambda x: x[1], reverse=reverse)
    # Apply order sorted
    return [records[i] for i, _ in sorted_indices]


def merge_sorted_results(existing, new_records, sort_field):
    """ Fusion two lists already sorted by sort_field """
    merged = []
    i, j = 0, 0
    # Function to parse sort key
    def parse_date(rec):
        return datetime.strptime(rec[sort_field], "%Y-%m-%d %H:%M:%S.%f")
    while i < len(existing) and j < len(new_records):
        if parse_date(existing[i]) <= parse_date(new_records[j]):
            merged.append(existing[i])
            i += 1
        else:
            merged.append(new_records[j])
            j += 1
    # Add remaining
    if i < len(existing):
        merged.extend(existing[i:])
    if j < len(new_records):
        merged.extend(new_records[j:])
    return merged


def safe_parse_to_json(input_str):
    """
    Transform pseudo chain of dictionary (key/value without quotes) in valid JSON, then python dictionary
    """
    def quote_keys_and_string_values(s):
        # Step 1 : Add quotes around non quoted keys
        s = re.sub(r'(?<={|,)\s*([a-zA-Z_]\w*)\s*:', r'"\1":', s)
        # Step 2 : Add quotes around values of type string non-quoted
        # Avoid number, lists, objects, bools and null
        def replace(match):
            value = match.group(1)
            if re.fullmatch(r'-?\d+(\.\d+)?', value):  # number int or float
                return f':{value}'
            elif value in ['true', 'false', 'null']:   # bool JSON and null
                return f':{value}'
            else:
                return f':"{value}"'
        s = re.sub(r':\s*([a-zA-Z_]\w*)\s*(?=,|})', replace, s)
        return s
    try:
        print("safe_parse_to_json Input string:", input_str, str(type(input_str)))
        # if input is dict
        if isinstance(input_str, dict):
            return json.loads(json.dumps(input_str))
        # Cleaning
        cleaned = quote_keys_and_string_values(input_str)
        # Convert in dict Python
        return json.loads(cleaned)
    except Exception as e:
        raise ValueError(f"Error of transformation or parsing JSON: {e}")
    

def replace_var(text: str, history: List[Dict[str, Any]], variables: Dict[str, Any]) -> str:
    # print("replace_var", str(history), str(text))
    if not history:
        return text
    # Construire un dictionnaire id -> answer
    history_dict = {
        str(item["id"]): item["answer"] for item in history
    }
    # --- Remplacement des variables ${var_name} ---
    def var_repl(match):
        var_name = match.group(1)
        value = variables.get(var_name, f"${{{var_name} NOT FOUND}}")
        # Si c'est un dict ou une liste, sérialisation JSON
        return json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)

    text = re.sub(r"\$\{(\w+)\}", var_repl, text)
    # Replacement of references #{id}, #{id.first}, #{id.2}, etc.
    def id_repl(match):
        id_ = match.group(1)
        accessor = match.group(2)
        answer = history_dict.get(id_)
        if answer is None:
            return f"#{{ID NOT FOUND:{id_}}}"
        # If list
        if isinstance(answer, list):
            if accessor is None or accessor == 'last':
                value = answer[-1] if answer else ""
            elif accessor == 'first':
                value = answer[0] if answer else ""
            elif accessor == 'all':
                return json.dumps(answer, ensure_ascii=False)
            else:
                try:
                    index = int(accessor)
                    value = answer[index]
                except (ValueError, IndexError):
                    return f"#{{INVALID INDEX:{id_}.{accessor}}}"
        else:
            # It is not a list, get the value
            value = answer
        # Si la valeur sélectionnée est dict ou list, JSON
        # If value selected is dict or list, JSON
        return json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    text = re.sub(r"#\{(\d+)(?:\.(first|last|all|\d+))?\}", id_repl, text)
    print("Text replaced: ", text)
    return text

def convert_param_type(value, expected_type):
    # TODO add this function in utils
    try:
        print(f"Converting value '{value}' to type '{expected_type}'")

        if expected_type == int:
            return int(value)
        elif expected_type == float:
            return float(value)
        elif expected_type == bool:
            return str(value).lower() in ("true", "1", "yes")
        elif expected_type == str:
            return str(value)
        elif expected_type == list:
            if isinstance(value, list):
                return value
            return [v.strip() for v in value.strip("[]").split(",")]
        elif expected_type == dict:
            if value is None:
                return {}
            elif type(value) == dict:
                return value
            return safe_parse_to_json(value)
        else:
            return value  # fallback
    except Exception as e:
        print(f"Failed to convert '{value}' to {expected_type}: {str(e)}")
        raise ValueError(f"Failed to convert '{value}' to {expected_type}: {str(e)}")


def create_current_id(username, page_id):
    """ Return the current id formed of username and page id 
    To use the same current id form
    """
    return username + "--" + page_id

def parse_current_id(current_id):
    """ Parse the current id and return the username and the page id """
    splitted = current_id.split("--",1)
    return splitted[0], splitted[1]


###########################
# MODIFICATION ENUM SIEM_SEARCH_FORMAT

def update_siem_search_result(data):
    """ Get the SIEM_SEARCH_FORMAT and update it without error"""
    cop = copy.deepcopy(ue.SIEM_SEARCH_FORMAT.result.value)
    cop.update(data)
    return cop
    