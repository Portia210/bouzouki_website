from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import time
import os

class Automation:
    def __init__(self):
        self.driver = None  # Initialize the driver here
        self.download_dir = os.getcwd()  # Always use current working directory

    def start_chrome_driver(self) -> webdriver.Chrome:
        """ Uses the current working directory as the download directory """
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument('--kiosk-printing')
            # chrome_options.add_argument("--headless")
            chrome_options.add_experimental_option('prefs', {
                "download.default_directory": self.download_dir,
                "plugins.always_open_pdf_externally": True,
                "savefile.default_directory": self.download_dir,
                "printing.print_preview_sticky_settings.appState": '{"recentDestinations":[{"id":"Save as PDF","origin":"local"}],"selectedDestinationId":"Save as PDF","version":2}',
                "profile.default_content_settings.popups": 0
            })
            self.driver = webdriver.Chrome(options=chrome_options)  # Assign the driver here
            return self.driver
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def safe_find(self, by, value, timeout=5):
        try:
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return None

    def move_downloaded_file(self, initial_files, output_folder_path, new_filename):
        time.sleep(0.5)
        current_files = os.listdir(self.download_dir)
        new_files = [f for f in current_files if f not in initial_files]
        
        if new_files:
            newest_file = max(new_files, key=lambda f: os.path.getmtime(os.path.join(self.download_dir, f)))
            source_path = os.path.join(self.download_dir, newest_file)
            target_path = os.path.join(output_folder_path, new_filename)
            
            os.makedirs(output_folder_path, exist_ok=True)
            if os.path.exists(source_path):
                # Handle existing target file
                if os.path.exists(target_path):
                    os.remove(target_path)  # Remove existing file to avoid errors
                os.rename(source_path, target_path)
                print(f"הקובץ הועבר ושונה שמו: {target_path}")
                return target_path
            else:
                print(f"קובץ המקור לא נמצא: {source_path}")
                return None
        else:
            print("לא נמצאו קבצים חדשים בתיקיית ההורדות")
            return None
            
    def close_popup_windows(self, original_window):
        new_handles = [handle for handle in self.driver.window_handles if handle != original_window]
        for handle in new_handles:
            self.driver.switch_to.window(handle)
            self.driver.close()
        self.driver.switch_to.window(original_window)