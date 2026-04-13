from flask import Flask, send_from_directory, render_template, request, abort, Response
from dotenv import load_dotenv
from db import get_db_connection
import os, csv, io


from auth import auth_bp


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


ADMIN_PASSWORD = "diss2026"  

@app.route("/admin")
def admin():
    if request.args.get("key") != ADMIN_PASSWORD:
        abort(403)
    conn = get_db_connection()
    metrics = conn.execute("SELECT * FROM auth_metrics ORDER BY id DESC").fetchall()
    users = conn.execute("SELECT id, username, last_ip, last_browser, failed_attempts, created_at FROM users ORDER BY id DESC").fetchall()
    conn.close()

@app.route("/admin/download")
def admin_download():
    if request.args.get("key") != ADMIN_PASSWORD:
        abort(403)
    table = request.args.get("table", "auth_metrics")
    conn = get_db_connection()
    if table == "users":
        rows = conn.execute("SELECT id, username, last_ip, last_browser, failed_attempts, created_at FROM users").fetchall()
    else:
        rows = conn.execute("SELECT * FROM auth_metrics").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    if rows:
        writer.writerow(rows[0].keys())
        writer.writerows(rows)
    output.seek(0)
    return Response(output, mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={table}.csv"})


if __name__ == "__main__":
    app.run(debug=True)
