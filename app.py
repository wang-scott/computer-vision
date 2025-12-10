from flask import Flask, render_template, request, jsonify, send_file
import random
import json
import os
import cv2
import numpy as np
from ultralytics import YOLO
import base64
from io import BytesIO

app = Flask(__name__)

# 假的分類標籤（你之後可以改成自己的模型類別）
LABELS = ["cleaner", "cutter", "gasoven", "gastorch", "medicinejar","scissors","screwdriver","socket"]

def detect_objects(image):
    """執行物件偵測，回傳類別計數和偵測圖片"""
    current_path = os.getcwd()
    MODEL_PATH = os.path.join(current_path,'best.pt')

    # --- 1. 載入訓練好的模型 ---
    try:
        model = YOLO(MODEL_PATH)
        print(f"--- 成功載入模型權重: {MODEL_PATH} ---")
    except Exception as e:
        print(f"錯誤：無法載入模型。請檢查路徑是否正確。錯誤訊息: {e}")
        return None, None

    # --- 2. 執行推論 (檢測) ---
    print(f"正在執行物件偵測...")

    results = model.predict(
        source=image,
        imgsz=(960,720),
        save=False,
        show=False,
        save_txt=False,
        save_conf=False,
        save_crop=False,
        project=None,
        name=None
    )

    print("\n--- 推論完成 ---")

    # --- 初始化類別計數字典 ---
    class_counts = {}
    detected_image = None

    # --- 3. 處理結果圖片與統計類別 ---
    for idx, result in enumerate(results):
        # 提取帶有邊界框的圖片 (np.ndarray)
        im_bgr = result.plot()
        detected_image = im_bgr
        
        # --- 統計每個類別的數量 ---
        if result.boxes is not None and len(result.boxes) > 0:
            class_ids = result.boxes.cls.cpu().numpy()
            class_names = result.names
            
            for class_id in class_ids:
                class_id = int(class_id)
                class_name = class_names[class_id]
                
                if class_name not in class_counts:
                    class_counts[class_name] = 0
                
                class_counts[class_name] += 1
                
    print("\n--- 每個類別的偵測數量 ---")
    print(class_counts)

    return class_counts, detected_image

@app.route("/")
def index():
    return render_template("index.html", labels=LABELS)

@app.route("/predict", methods=["POST"])
def predict_endpoint():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    
    try:
        file_bytes = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        # Resize 圖片為 960x720
        image = cv2.resize(image, (960, 720))
        
        # 儲存上傳的圖片為 test_image
        image_path = 'test_image.png'
        
        # 執行物件偵測
        class_counts, detected_image = detect_objects(image)
        
        if class_counts is None or detected_image is None:
            return jsonify({"error": "Detection failed"}), 500
        
        # 將偵測圖片轉換為 Base64 以便傳送給前端
        _, buffer = cv2.imencode('.png', detected_image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # 計算主要類別（最多偵測到的）
        if class_counts:
            main_label = max(class_counts, key=class_counts.get)
        else:
            main_label = "Unknown"

        return jsonify({
            "label": main_label,
            "class_counts": class_counts,
            "detected_image": f"data:image/png;base64,{image_base64}"
        })
    
    except Exception as e:
        print(f"錯誤: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)