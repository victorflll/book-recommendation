from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app,
     resources={r"/*": {
         "origins": ["*"],
         "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
         "allow_headers": ["Content-Type"],
         "supports_credentials": True,
         "send_wildcard": False
     }}
)

from src.app import postgres_controller, mongo_controller