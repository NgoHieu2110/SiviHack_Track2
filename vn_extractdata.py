from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route("/")
def index():
    # Hiển thị giao diện HTML
    return render_template("index.html")

@app.route("/run-export", methods=["POST"])
def run_export():
    data = request.json
    location = data.get("location", "DEU").upper()  # Mặc định là Đức (DEU) nếu không chọn
    max_notices = data.get("max", 10)

    # Xây dựng câu truy vấn dựa trên địa điểm Frontend gửi lên
    query_str = f"place-of-performance IN ({location})"
    outdir = "ted_export"

    # Gọi câu lệnh Python trong CMD thông qua subprocess
    cmd = [
        "python", "ted_to_markdown.py",
        "--query", query_str,
        "--max", str(max_notices),
        "--outdir", outdir
    ]

    try:
        # Chạy lệnh và đợi kết quả
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return jsonify({
            "status": "success",
            "message": f"Đã tải thành công các gói thầu tại {location}!",
            "output": result.stdout
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "message": "Lỗi khi chạy lệnh tải dữ liệu.",
            "error": e.stderr
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)