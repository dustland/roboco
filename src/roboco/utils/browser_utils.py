import os
import platform
import subprocess
from pathlib import Path


def get_platform():
    """Get the current platform name in a standardized format."""
    system = platform.system().lower()
    
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    else:
        return system


def get_chrome_path():
    """
    Get the path to Google Chrome executable based on the current platform.
    Returns None if Chrome isn't found.
    """
    system = get_platform()
    
    if system == "macos":
        # Default Chrome path on macOS
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
        
        for path in paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                return expanded_path
                
    elif system == "windows":
        # Common Chrome paths on Windows
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
                
    elif system == "linux":
        # Try to find Chrome using the 'which' command on Linux
        try:
            result = subprocess.run(["which", "google-chrome"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True, 
                                   check=False)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
            
        # Alternative locations
        paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
    
    # Chrome wasn't found
    return None


def is_chrome_installed():
    """Check if Google Chrome is installed on the system."""
    return get_chrome_path() is not None


if __name__ == "__main__":
    # Test the functions when run directly
    print(f"Platform: {get_platform()}")
    
    chrome_path = get_chrome_path()
    if chrome_path:
        print(f"Chrome found at: {chrome_path}")
    else:
        print("Chrome not found") 