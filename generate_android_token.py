#!/usr/bin/env python
"""
Generate Android-format FCM tokens for testing
This creates tokens that look like real Android FCM tokens
"""

import random
import string
import base64
import hashlib
import time

def generate_android_fcm_token():
    """Generate a realistic Android FCM token for testing"""
    
    # Android FCM tokens typically start with specific patterns
    prefixes = [
        "fu_",  # Most common
        "fMEP", 
        "fLQ",
        "fKX"
    ]
    
    # Generate random base64-like string
    def random_base64_string(length=140):
        chars = string.ascii_letters + string.digits + "-_"
        return ''.join(random.choice(chars) for _ in range(length))
    
    # Create token
    prefix = random.choice(prefixes)
    token_body = random_base64_string(140)
    
    # Add some realistic patterns
    token = f"{prefix}{token_body}"
    
    return token

def generate_multiple_tokens(count=5):
    """Generate multiple Android FCM tokens"""
    tokens = []
    for i in range(count):
        token = generate_android_fcm_token()
        tokens.append(token)
        print(f"Token {i+1}: {token}")
    return tokens

def test_token_format():
    """Test if generated tokens look realistic"""
    print("🔧 Generating Android FCM Tokens for Testing")
    print("=" * 50)
    
    tokens = generate_multiple_tokens(5)
    
    print("\n📱 Token Analysis:")
    for i, token in enumerate(tokens, 1):
        print(f"Token {i}:")
        print(f"  Length: {len(token)} characters")
        print(f"  Prefix: {token[:3]}")
        print(f"  Format: {'✅ Valid' if token.startswith('fu_') else '⚠️ Alternative'}")
        print()

if __name__ == "__main__":
    test_token_format() 