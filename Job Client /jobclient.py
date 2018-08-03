from flask import Flask
import json

app = Flask(__name__,template_folder='template')

import views


