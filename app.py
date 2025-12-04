from flask import Flask, render_template, request, jsonify
import random
import cv2
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
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    cv2.imshow("Uploaded Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # === 這裡原本放模型推論 ===
    # 目前先回傳假的預測結果
    label = random.choice(LABELS)
    confidence = round(random.uniform(0.5, 0.99), 2)  # 0.50 ~ 0.99 之間

    return jsonify({
        "label": label,
        "confidence": confidence
    })


if __name__ == "__main__":
    # 實際部署時請把 debug 關掉
    app.run(host="0.0.0.0", port=5000, debug=True)
