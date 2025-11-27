from flask import Flask, request, jsonify, send_file
import boto3
import os
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)

###############################
# Cloudflare R2 CONFIG
###############################
R2_BUCKET = os.environ.get("R2_BUCKET")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")

# 반드시 R2 전용 키 사용해야 함
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")

# 엔드포인트 (자동 생성됨)
R2_ENDPOINT = f"https://{CF_ACCOUNT_ID}.r2.cloudflarestorage.com"

# boto3 S3 client
s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
)

###############################
# TEST ENDPOINT
###############################
@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "Central Data Engine running"})

###############################
# UPLOAD IMAGE
###############################
@app.route("/upload-image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file received"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename)

    try:
        s3.upload_fileobj(
            file,
            R2_BUCKET,
            f"images/{filename}",
            ExtraArgs={"ContentType": file.content_type},
        )
        return jsonify({"status": "ok", "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

###############################
# DOWNLOAD IMAGE
###############################
@app.route("/get-image/<filename>", methods=["GET"])
def get_image(filename):
    try:
        obj = s3.get_object(Bucket=R2_BUCKET, Key=f"images/{filename}")
        return send_file(BytesIO(obj["Body"].read()), mimetype=obj["ContentType"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

###############################
# SAVE JSON
###############################
@app.route("/save-json", methods=["POST"])
def save_json():
    data = request.json
    key = data.get("key")
    content = data.get("content")

    if not key:
        return jsonify({"error": "Key required"}), 400

    try:
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=f"json/{key}.json",
            Body=str(content).encode("utf-8"),
            ContentType="application/json",
        )
        return jsonify({"status": "ok", "saved_key": key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

###############################
# LOAD JSON
###############################
@app.route("/get-json/<key>", methods=["GET"])
def get_json(key):
    try:
        obj = s3.get_object(Bucket=R2_BUCKET, Key=f"json/{key}.json")
        data = obj["Body"].read().decode("utf-8")
        return jsonify({"key": key, "content": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

###############################
# UPLOAD TEST PAGE
###############################
@app.route('/upload-test', methods=['GET'])
def upload_test_page():
    return """
    <html>
      <body>
        <h2>Image Upload Test</h2>
        <form action="/upload-image" method="post" enctype="multipart/form-data">
            <input type="file" name="file" />
            <button type="submit">Upload</button>
        </form>
      </body>
    </html>
    """

@app.route("/")
def home():
    return jsonify({"message": "Ai Trading Lab Central Data Engine v1.0"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
