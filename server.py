from flask import Flask, send_from_directory, jsonify
import subprocess
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
BAT_FILE = BASE_DIR / "run_ga4_update.bat"


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(BASE_DIR, path)


@app.route("/refresh-data", methods=["POST"])
def refresh_data():
    try:
        result = subprocess.run(
            [str(BAT_FILE)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            shell=True,
            timeout=300
        )

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "message": "Dashboard update failed.",
                "error": result.stderr
            }), 500

        return jsonify({
            "success": True,
            "message": "Dashboard updated successfully.",
            "output": result.stdout
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Could not execute update.",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5501)