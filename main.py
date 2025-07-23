import cv2
import requests
import winsound
from ultralytics import YOLO
import os
from datetime import datetime
import time

# --- CONFIGURATION ---
BOT_TOKEN = '8037950501:AAFZGTIhG6WKafogoblSvMOUYSFn0zACBJU'
CHAT_ID = '1282149880'
CONFIDENCE_THRESHOLD = 0.3
TELEGRAM_INTERVAL = 30  # seconds between alerts
MODEL_PATH = 'yolov8n.pt'  # Change to your trained model if needed

# Threat classes to detect (excluding normal person)
THREAT_CLASSES = ['cell phone', 'knife', 'gun', 'masked', 'crawling']

# --- INITIAL SETUP ---
model = YOLO(MODEL_PATH)
last_alert_time = 0

# Telegram image sending function
def send_telegram_image(image_path, detected_class):
    print("[INFO] Sending image via Telegram...")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    caption = f"🚨 ALERT: {detected_class.upper()} Detected!\n🕒 {timestamp}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    with open(image_path, 'rb') as photo:
        response = requests.post(
            url,
            data={'chat_id': CHAT_ID, 'caption': caption},
            files={'photo': photo}
        )

    if response.status_code == 200:
        print("[✅] Telegram alert sent successfully!")
    else:
        print("[❌] Telegram error:", response.text)

# --- SIREN SOUND FUNCTION ---
def play_siren():
    for _ in range(3):  # Play siren pattern 3 times
        winsound.Beep(1000, 200)
        winsound.Beep(1500, 200)
        winsound.Beep(2000, 300)

# --- START CCTV CAMERA ---
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Could not read from camera.")
        break

    results = model.predict(source=frame, conf=CONFIDENCE_THRESHOLD, save=False, verbose=False)
    detected = False
    detected_class = ""

    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]
            conf = float(box.conf[0])

            if class_name in THREAT_CLASSES:
                detected = True
                detected_class = class_name
                print(f"[⚠️ DETECTED] {class_name} ({conf:.2f})")

                # Draw bounding box
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                x1, y1, x2, y2 = xyxy
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, f"{class_name} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # Send alert if threat detected
    current_time = time.time()
    if detected and (current_time - last_alert_time) > TELEGRAM_INTERVAL:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"threat_{detected_class}_{timestamp}.jpg"
        cv2.imwrite(filename, frame)

        # 🔊 Play siren sound
        play_siren()

        # 📤 Send image via Telegram
        send_telegram_image(filename, detected_class)

        os.remove(filename)  # Cleanup
        last_alert_time = current_time

    # Display feed
    cv2.imshow("📹 AI CCTV Detector", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
