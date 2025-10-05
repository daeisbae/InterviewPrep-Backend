#!/usr/bin/env python3
"""
Simple test script to send interview.webm to the analyze-interview endpoint.

Usage:
    python tests/send_video_test.py
"""

import requests

# Configuration
VIDEO_FILE = "tests/interview.webm"
API_URL = "http://localhost:8000/api/v1/analyze-interview"

print(f"📹 Sending {VIDEO_FILE} to {API_URL}")

# Open and send the file
with open(VIDEO_FILE, 'rb') as f:
    files = {'file': ('interview.webm', f, 'video/webm')}
    response = requests.post(API_URL, files=files)

# Print response
print(f"Status: {response.status_code}")
print(response.json())
