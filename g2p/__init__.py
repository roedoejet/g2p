from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from g2p.cors import Correspondence
from g2p.transducer import Transducer

VERSION = '0.0.1'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test!'
socketio = SocketIO(app)

def hotToCors(hotData):
    return [{"before": x[0], "from": x[1], "after": x[2], "to": x[3]} for x in hotData]

@app.route('/')
def home():    
    return render_template('index.html')

@socketio.on('conversion event', namespace='/test')
def test_message(message):
    print(message)
    cors = Correspondence(hotToCors(message['data']['cors']))
    transducer = Transducer(cors)
    output_string = transducer(message['data']['input_string'])
    emit('conversion response', {'output_string': output_string})

@socketio.on('connect', namespace='/test')
def test_connect():
    emit('connection response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')