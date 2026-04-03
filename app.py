from flask import Flask, send_from_directory
from dotenv import load_dotenv
import os

from auth import auth_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)

# App configuration
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["REQUIRE_OTP_ALWAYS"] = os.getenv("REQUIRE_OTP_ALWAYS") == "True"
app.config["OTP_THRESHOLD"] = int(os.getenv("OTP_THRESHOLD", 40))

# Register blueprint
app.register_blueprint(auth_bp)


# Serve images folder
@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory("images", filename)


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return "404 – Page not found", 404


@app.errorhandler(500)
def internal_error(e):
    return "500 – Internal server error", 500


if __name__ == "__main__":
    app.run(debug=True)
