import os
import time

def wait_for_new_file(download_dir):
    """
    Monitors the specified download directory for a new file.
    Returns the name of the downloaded file.
    """
    existing_files = os.listdir(download_dir)
    while True:
        current_files = os.listdir(download_dir)
        new_files = set(current_files) - set(existing_files)

        if new_files:
            while True:
                new_file_name = list(new_files)[0]
                new_file_path = os.path.join(download_dir, new_file_name)
                if new_file_path.endswith(".crdownload"):
                    break
                else:
                    # print("file finish download")
                    return new_file_path

        # Wait for a short time before checking again
        time.sleep(1)