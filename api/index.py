# api/index.py

from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Flask on Vercel!"

# Required for Vercel to detect the app
def handler(environ, start_response):
    return app(environ, start_response)
