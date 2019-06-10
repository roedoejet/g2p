from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_talisman import Talisman
from g2p.cors import Correspondence
from g2p.cors.langs import LANGS
from g2p.transducer import Transducer


VERSION = '0.0.1'

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'test!'
socketio = SocketIO(app)
DEFAULT_N = 10


def returnEmptyCors(n=DEFAULT_N):
    y = 0
    cors = []
    while y < n:
        cors.append({
            "from": '',
            "to": '',
            "before": '',
            "after": ''
        })
        y += 1
    return cors

def hotToCors(hotData):
    return [{"before": x[2], "from": x[0], "after": x[3], "to": x[1]} for x in hotData if x[0] and x[1]]


@app.route('/')
def home():
    return render_template('index.html', langs=LANGS)


@socketio.on('conversion event', namespace='/test')
def convert(message):
    print(message)
    cors = Correspondence(hotToCors(message['data']['cors']))
    transducer = Transducer(cors)
    output_string = transducer(message['data']['input_string'])
    emit('conversion response', {'output_string': output_string})


@socketio.on('table event', namespace='/test')
def change_table(message):
    print(message)
    if message['lang'] == 'custom':
        cors = Correspondence(returnEmptyCors())
    else:
        cors = Correspondence(language={'lang': message['lang'], 'table': message['table']})
    emit('table response', {'cors': cors()})


@socketio.on('connect', namespace='/test')
def test_connect():
    emit('connection response', {'data': 'Connected'})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')
