from flask import Flask, session, Blueprint
from flask_redis import FlaskRedis
from celery import Celery
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)


bp = Blueprint('task_server',__name__)


app.config.from_pyfile('task_server.conf')
redis_store = FlaskRedis(app)

celery = Celery(app.name)
celery.conf.broker_url = app.config["REDIS_URL"]


import api

app.register_blueprint(bp, url_prefix='/api')

