from flask import Flask, render_template
from flask_socketio import SocketIO, emit
VERSION = '0.0.1'

app = Flask(__name__)

@app.route('/')
def home():    
    return render_template('index.html')