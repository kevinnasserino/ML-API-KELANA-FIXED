from flask import Flask

app = Flask(__name__)

from . import main  # Import main routes
