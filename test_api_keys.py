#!/usr/bin/env python
"""
Script to test if API keys for different models are valid
"""

import os
import sys
import logging
from dotenv import load_dotenv
import requests
import json

load_dotenv()  # Load environment variables from .env file

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_openai_key(api_key, base_url="https://api.openai.com/v1"):
    """Test if the OpenAI API key is valid"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(f"{base_url}/models", headers=headers)
        if response.status_code == 200:
            logger.info("✅ OpenAI API key is valid")
            return True
        else:
            logger.error(f"❌ OpenAI API key is invalid. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing OpenAI API key: {str(e)}")
        return False

def test_anthropic_key(api_key, base_url="https://api.gptsapi.net/v1"):
    """Test if the Anthropic API key is valid"""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/messages",
            headers=headers,
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hello, API test."}]
            }
        )
        
        if response.status_code == 200:
            logger.info("✅ Anthropic API key is valid")
            return True
        else:
            logger.error(f"❌ Anthropic API key is invalid. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing Anthropic API key: {str(e)}")
        return False

def test_deepseek_key(api_key, base_url="https://api.deepseek.com/v1"):
    """Test if the Deepseek API key is valid"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Hello, API test."}],
                "max_tokens": 10
            }
        )
        
        if response.status_code == 200:
            logger.info("✅ Deepseek API key is valid")
            return True
        else:
            logger.error(f"❌ Deepseek API key is invalid. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing Deepseek API key: {str(e)}")
        return False

def main():
    """Main function to test all API keys"""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") 
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    
    # Check if keys exist in environment
    if not openai_key:
        logger.warning("⚠️ OPENAI_API_KEY environment variable not set")
    if not anthropic_key: 
        logger.warning("⚠️ ANTHROPIC_API_KEY environment variable not set")
    if not deepseek_key:
        logger.warning("⚠️ DEEPSEEK_API_KEY environment variable not set")
    
    # Test each key if it exists
    success = True
    
    if openai_key:
        if not test_openai_key(openai_key):
            success = False
    
    if anthropic_key:
        # Check if there's a specific base_url in config for Anthropic
        # Directly trying the gptsapi URL if it's the one in the config 
        if not test_anthropic_key(anthropic_key, "https://api.anthropic.com"):
            # Try with alternative URL
            logger.info("Trying alternate URL for Anthropic (gptsapi.net)...")
            if not test_anthropic_key(anthropic_key, "https://api.gptsapi.net"):
                success = False
    
    if deepseek_key:
        if not test_deepseek_key(deepseek_key):
            success = False
    
    if success:
        logger.info("✅ All available API keys are valid")
        return 0
    else:
        logger.error("❌ One or more API keys failed validation")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 