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

def test_anthropic_key(api_key, base_url="https://api.gptsapi.net"):
    """Test if the Anthropic API key is valid via gptsapi.net"""
    
    # Using the OpenAI-compatible endpoint
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        # Using the OpenAI-compatible chat completions endpoint
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": "wild-3-5-sonnet-20241022",
                "messages": [{"role": "user", "content": "Hello, API test."}],
                "max_tokens": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Claude API key is valid with OpenAI-compatible format")
            return True
        else:
            logger.error(f"❌ Claude test failed with gptsapi.net. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except requests.Timeout:
        logger.error("❌ Claude API request timed out after 10 seconds")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing Claude API key: {str(e)}")
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
            },
            timeout=10  # Add 10 second timeout
        )
        
        if response.status_code == 200:
            logger.info("✅ Deepseek API key is valid")
            return True
        else:
            logger.error(f"❌ Deepseek API key is invalid. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except requests.Timeout:
        logger.error("❌ Deepseek API request timed out after 10 seconds")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing Deepseek API key: {str(e)}")
        return False

def test_claude_openai_mode(api_key, base_url="https://api.gptsapi.net"):
    """Test if Claude can be accessed via OpenAI-compatible mode on gptsapi.net"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": "claude-3-5-sonnet-20241022",
                "messages": [{"role": "user", "content": "Hello, API test."}],
                "max_tokens": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Claude via OpenAI-compatible mode is working")
            return True
        else:
            logger.error(f"❌ Claude via OpenAI-compatible mode failed. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except requests.Timeout:
        logger.error("❌ Claude OpenAI-compatible mode request timed out after 10 seconds")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing Claude via OpenAI-compatible mode: {str(e)}")
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
        # Test in native Anthropic mode
        if not test_anthropic_key(anthropic_key, "https://api.gptsapi.net/v1"):
            success = False
            
        # Also test in OpenAI-compatible mode
        logger.info("Testing Claude with OpenAI-compatible mode...")
        if not test_claude_openai_mode(anthropic_key, "https://api.gptsapi.net/v1"):
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