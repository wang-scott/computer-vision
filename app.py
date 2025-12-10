from flask import Flask, render_template, request, jsonify, send_file
import random
import json
import os
# import cv2
import numpy as np

app = Flask(__name__)

# 假的分類標籤（你之後可以改成自己的模型類別）
LABELS = ["Paper", "Plastic", "Metal", "Glass", "Other"]


@app.route("/")
def index():
    # 把 LABELS 傳到前端，讓前端畫統計圖用
    return render_template("index.html", labels=LABELS)


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    
    file_bytes = np.frombuffer(file.read(), np.uint8)
    # image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    # cv2.imshow("Uploaded Image", image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    
    # === 這裡原本放模型推論 ===
    # 目前先回傳假的預測結果
    label = random.choice(LABELS)
    confidence = round(random.uniform(0.5, 0.99), 2)  # 0.50 ~ 0.99 之間

    return jsonify({
        "label": label,
        "confidence": confidence
    })


@app.route("/get_detection_image", methods=["GET"])
def get_detection_image():
    """返回檢測結果圖片"""
    # 在 detection_results 目錄中尋找圖片檔案
    detection_dir = "detection_results"
    if not os.path.exists(detection_dir):
        return jsonify({"error": "Detection results directory not found"}), 404
    
    # 尋找圖片檔案 (jpg, jpeg, png)
    image_files = [f for f in os.listdir(detection_dir) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        return jsonify({"error": "No detection image found"}), 404
    
    # 返回第一個找到的圖片
    image_path = os.path.join(detection_dir, image_files[0])
    return send_file(image_path, mimetype='image/jpeg')


@app.route("/get_class_counts", methods=["GET"])
def get_class_counts():
    """返回物件檢測統計數據"""
    json_path = "detection_results/class_counts.json"
    
    if not os.path.exists(json_path):
        return jsonify({"error": "Class counts file not found"}), 404
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            class_counts = json.load(f)
        return jsonify(class_counts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # 實際部署時請把 debug 關掉
    app.run(host="0.0.0.0", port=5000, debug=True)
