import os

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from . import db
from .config import Config


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    app.config["MAX_CONTENT_LENGTH"] = app.config["MAX_UPLOAD_MB"] * 1024 * 1024
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    db.init_app(app)

    from .routes import api

    app.register_blueprint(api, url_prefix="/api")

    @app.errorhandler(HTTPException)
    def http_error(e):
        message = e.description
        if e.code == 413:
            message = "That file is too large."
        return jsonify({"error": message}), e.code

    @app.errorhandler(Exception)
    def server_error(e):
        app.logger.exception("Unhandled error")
        return jsonify({"error": "Something went wrong on the server."}), 500

    @app.after_request
    def headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    return app
