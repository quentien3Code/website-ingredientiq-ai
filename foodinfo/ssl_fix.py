"""
SSL Certificate Fix for Edamam API
This module provides SSL context configuration to handle certificate verification issues
"""

import ssl
import aiohttp

# Create SSL context to handle certificate verification issues
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def get_ssl_connector():
    """
    Get SSL connector for aiohttp sessions
    """
    return aiohttp.TCPConnector(ssl=ssl_context)

def create_ssl_session():
    """
    Create aiohttp session with SSL context
    """
    connector = get_ssl_connector()
    return aiohttp.ClientSession(connector=connector)
