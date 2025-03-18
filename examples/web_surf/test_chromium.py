#!/usr/bin/env python3
"""
Simple script to test if Chromium can be launched manually.
"""

import logging
import os
import subprocess
import time

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def test_chromium_with_open():
    """
    Test launching Chromium using macOS 'open' command with a custom profile.
    """
    try:
        # Define the Chromium app path
        chromium_app = os.path.expanduser("~/Library/Caches/ms-playwright/chromium-1155/chrome-mac/Chromium.app")
        
        if not os.path.exists(chromium_app):
            logger.error(f"Chromium app not found at: {chromium_app}")
            return False
            
        logger.info(f"Using Chromium app at: {chromium_app}")
        
        # Create a dedicated user data directory
        user_data_dir = os.path.expanduser("~/.chromium-profile")
        os.makedirs(user_data_dir, exist_ok=True)
        logger.info(f"Using user data directory: {user_data_dir}")
        
        # Prepare a simple HTML file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        test_html_path = os.path.join(script_dir, "test.html")
        
        with open(test_html_path, "w") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Chromium Test Page</title>
                <meta http-equiv="refresh" content="5;url=https://example.com" />
            </head>
            <body>
                <h1>Chromium is working!</h1>
                <p>This is a test page.</p>
                <p>Redirecting to example.com in 5 seconds...</p>
            </body>
            </html>
            """)
        
        logger.info(f"Created test HTML file at: {test_html_path}")
        
        # Construct the open command to launch Chromium with arguments
        # The syntax for passing arguments to an application with 'open' is:
        # open -a Application.app --args arg1 arg2 ...
        cmd = [
            "open",
            "-a",
            chromium_app,
            "--args",
            f"--user-data-dir={user_data_dir}",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            f"file://{test_html_path}"
        ]
        
        logger.info(f"Launching Chromium with command: {' '.join(cmd)}")
        
        # Launch Chromium and capture output
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info(f"Command executed with PID: {process.pid}")
        logger.info("Waiting for Chromium to launch...")
        
        # Wait for a few seconds to see if process completes (open command should complete quickly)
        time.sleep(3)
        
        returncode = process.poll()
        if returncode is not None and returncode != 0:
            stdout, stderr = process.communicate()
            logger.error(f"Open command failed with code: {returncode}")
            logger.error(f"STDOUT: {stdout.decode('utf-8', errors='replace')}")
            logger.error(f"STDERR: {stderr.decode('utf-8', errors='replace')}")
            return False
        
        logger.info("Chromium appears to have launched successfully.")
        logger.info("Waiting for the page to load and auto-redirect to example.com...")
        
        # Wait longer for the page load and redirect
        time.sleep(7)
        
        # Now manually open a new URL in the same browser instance
        second_url = "https://github.com"
        logger.info(f"Opening a second URL: {second_url}")
        
        # Construct another open command to open a new tab with a different URL
        new_tab_cmd = [
            "open",
            "-a",
            chromium_app,
            second_url
        ]
        
        # Execute the command to open a new tab
        subprocess.run(new_tab_cmd, check=True)
        
        logger.info("Waiting for the second page to load...")
        time.sleep(5)
        
        logger.info("Test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing Chromium: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chromium_with_open()
    print(f"Chromium test {'succeeded' if success else 'failed'}") 