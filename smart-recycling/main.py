import lgpio
import os
import time
import subprocess
import board
import adafruit_dht
import smbus2
import yolov5
import torch
import cv2
import requests
from datetime import datetime

# === PyTorch 2.6+ 보안 규칙 통과 ===
_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "your_token_here")
DATABASE_ID = "372d0cc3fc948057a931f35f1fb73adc"
TRIG = 23
ECHO = 25
DHT_PIN = board.D4
LCD_ADDR = 0x27
DISTANCE_THRESHOLD = 50
FAIL_TIMEOUT = 1.0

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, TRIG)
lgpio.gpio_claim_input(h, ECHO)

dht = adafruit_dht.DHT11(DHT_PIN)
bus = smbus2.SMBus(1)

def lcd_send(data, mode):
    high = mode | (data & 0xF0) | 0x08
    low = mode | ((data << 4) & 0xF0) | 0x08
    for bits in [high | 0x04, high, low | 0x04, low]:
        bus.write_byte(LCD_ADDR, bits)
        time.sleep(0.0005)

def lcd_init():
    for cmd in [0x33, 0x32, 0x06, 0x0C, 0x28, 0x01]:
        lcd_send(cmd, 0)
        time.sleep(0.05)

def lcd_print(line1, line2=""):
    lcd_send(0x01, 0)
    time.sleep(0.05)
    lcd_send(0x80, 0)
    for c in line1[:16]:
        lcd_send(ord(c), 1)
    lcd_send(0xC0, 0)
    for c in line2[:16]:
        lcd_send(ord(c), 1)

def get_distance():
    lgpio.gpio_write(h, TRIG, 0)
    time.sleep(0.05)
    lgpio.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)
    lgpio.gpio_write(h, TRIG, 0)
    timeout_start = time.time()
    while lgpio.gpio_read(h, ECHO) == 0:
        if time.time() - timeout_start > 0.03:
            return 999
    start = time.time()
    timeout_start = time.time()
    while lgpio.gpio_read(h, ECHO) == 1:
        if time.time() - timeout_start > 0.03:
            return 999
    end = time.time()
    return (end - start) * 17150

def capture_image():
    subprocess.run(['rpicam-still', '-o', '/tmp/frame.jpg', '--nopreview', '-t', '500'], capture_output=True)
    frame = cv2.imread('/tmp/frame.jpg')
    return frame is not None, frame

def log_to_notion(label, confidence, temp, humidity):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": label}}]},
            "Time": {"date": {"start": datetime.now().isoformat()}},
            "Category": {"rich_text": [{"text": {"content": label}}]},
            "Confidence": {"number": round(confidence * 100, 2)},
            "Temperature": {"number": float(temp) if temp else 0},
            "Humidity": {"number": float(humidity) if humidity else 0}
        }
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"Notion 응답: {response.status_code}")
    if response.status_code != 200:
        print(f"오류: {response.text}")

LABELS = {
    "plastic":       ("Plastic", "플라스틱통에"),
    "metal":         ("Can/Metal", "캔통에"),
    "paper":         ("Paper", "종이통에"),
    "cardboard":     ("Paper", "종이통에"),
    "glass":         ("Glass", "유리통에"),
    "biodegradable": ("Food", "음식물통에"),
}

model = yolov5.load("garbage.pt")
model.conf = 0.25

lcd_init()
lcd_print("Smart Recycling", "Ready...")
print("시스템 시작!")
fail_start = None

try:
    while True:
        dist = get_distance()

        if dist == 999:
            if fail_start is None:
                fail_start = time.time()
            elif time.time() - fail_start >= FAIL_TIMEOUT:
                lcd_print("Sensor Error", "Check wiring")
                print("초음파 센서 이상 - 배선 확인")
            time.sleep(0.2)
            continue
        else:
            fail_start = None

        print(f"거리: {dist:.1f}cm")

        if dist < DISTANCE_THRESHOLD:
            print("물체 감지! 카메라 실행...")
            lcd_print("Detecting...", "Please wait")

            try:
                ret, frame = capture_image()

                if ret:
                    results = model(frame, size=640)
                    preds = results.pred[0]

                    if len(preds) > 0:
                        best = preds[preds[:, 4].argmax()]
                        confidence = float(best[4])
                        label_id = int(best[5])
                        label_name = model.names[label_id]

                        category, location = LABELS.get(label_name, (label_name, "일반쓰레기통에"))
                        print(f"분류: {category} ({confidence*100:.1f}%)")
                        lcd_print(f"{category}", f"{location} 버리세요")

                        try:
                            temp = dht.temperature
                            humidity = dht.humidity
                        except:
                            temp = 0
                            humidity = 0

                        log_to_notion(category, confidence, temp, humidity)
                        print(f"Notion 기록 완료! 온도:{temp} 습도:{humidity}")
                        time.sleep(3)
                    else:
                        lcd_print("No object", "detected")
                        print("물체 없음")
                        time.sleep(1)
                else:
                    raise IOError("카메라 프레임 캡처 실패")

            except Exception as e:
                print(f"카메라 에러 감지: {e}")
                print("카메라 프로세스 강제 종료 및 자동 복구 시작...")
                lcd_print("Camera Error", "Recovering...")
                os.system('pkill -f rpicam')
                time.sleep(3)
                print("복구 완료! 다시 스캔 대기")
                continue

        else:
            try:
                temp = dht.temperature
                humidity = dht.humidity
                lcd_print(f"Temp: {temp}C", f"Humidity: {humidity}%")
            except:
                lcd_print("Smart Recycling", "Ready...")
            time.sleep(2)

except KeyboardInterrupt:
    print("종료")
    lgpio.gpiochip_close(h)
    lcd_print("Goodbye!", "")
