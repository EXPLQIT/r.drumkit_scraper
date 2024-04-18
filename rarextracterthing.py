import os
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def extract_file(file_path, destination_folder):
    # Create a unique directory for each archive to prevent file scattering
    archive_name = os.path.splitext(os.path.basename(file_path))[0]
    extraction_target_folder = os.path.join(destination_folder, archive_name)
    os.makedirs(extraction_target_folder, exist_ok=True)

    try:
        # Execute 7-Zip command to extract into the created subfolder
        result = subprocess.run(['C:\\Program Files\\7-Zip\\7z', 'x', file_path, f'-o{extraction_target_folder}'], check=True, text=True, capture_output=True)
        return (file_path, True, result.stdout)
    except subprocess.CalledProcessError as e:
        # Attempt to delete the archive if extraction fails
        try:
            os.remove(file_path)
            deletion_status = "Deleted"
        except Exception as deletion_error:
            deletion_status = f"Failed to delete: {deletion_error}"
        return (file_path, False, f"{e.stderr} | {deletion_status}")

def clean_folder_name(folder_name):
    clean_name = folder_name.replace('%20', ' ')
    clean_name = re.sub(r'[^a-zA-Z0-9 .]', '', clean_name)
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
    return clean_name

def rename_extracted_folders(destination_folder):
    for folder_name in os.listdir(destination_folder):
        folder_path = os.path.join(destination_folder, folder_name)
        if os.path.isdir(folder_path):
            new_folder_name = clean_folder_name(folder_name)
            new_folder_path = os.path.join(destination_folder, new_folder_name)
            if new_folder_name != folder_name:  # Only rename if the name is different
                os.rename(folder_path, new_folder_path)
                print(f"Renamed '{folder_name}' to '{new_folder_name}'")

def extract_files(source_folder, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        print(f"Created destination folder: {destination_folder}")

    files = [f for f in os.listdir(source_folder) if f.endswith(('.rar', '.zip'))]
    if not files:
        print("No RAR or ZIP files found in the source folder. Cleaning existing folder names.")
        rename_extracted_folders(destination_folder)  # Call here if no files are found
        return

    print(f"Found {len(files)} files in source folder.")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(extract_file, os.path.join(source_folder, file), destination_folder): file for file in files}
        for future in tqdm(as_completed(futures), total=len(files), desc="Extracting files", unit="file"):
            file, success, message = future.result()
            if success:
                print(f"Extracted into folder: {os.path.join(destination_folder, os.path.splitext(os.path.basename(file))[0])}")
            else:
                print(f"Failed to extract {os.path.basename(file)}: {message}")
    
    rename_extracted_folders(destination_folder)  # Call here after extraction and cleanup

source_folder = r'C:\TESTICLES'
destination_folder = r'G:\EXPLOIT\TEST KITS'

extract_files(source_folder, destination_folder)
