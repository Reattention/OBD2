#!/usr/bin/env python3
"""
Quick web interface test to identify issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
import logging

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)

def test_basic_flask():
    """Test basic Flask functionality"""
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return '''
        <html>
        <head><title>BMW OBD2 Test Interface</title></head>
        <body>
            <h1>🚗 BMW OBD2 Advanced Monitoring</h1>
            <p>Web interface is working!</p>
            <p>✅ READ-ONLY Operation Confirmed</p>
            <p>✅ All features are safe for vehicle ECU</p>
        </body>
        </html>
        '''
    
    @app.route('/test')
    def test():
        return {'status': 'working', 'message': 'Web interface test successful'}
    
    print("Starting basic Flask test server...")
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == "__main__":
    test_basic_flask()