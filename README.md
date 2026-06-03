# IoT26_project_TeamG

#  AIoT Smart Recycling System


## 📌 프로젝트 개요

라즈베리파이 5 + YOLOv8 + 멀티센서를 활용한 AI 기반 스마트 분리수거 시스템입니다.  
사용자가 쓰레기를 가져오면 초음파 센서가 감지하고, 카메라로 촬영 후 YOLO AI가 종류를 분류하여 LCD에 올바른 분리수거 방법을 안내합니다. 분류 결과는 Notion 클라우드에 실시간으로 기록됩니다.

---
## 재활용 분류 결과
![alt text](<재활용분류결과.png>)

## 
## 💡 주요 아이디어

### 기본 기능
| 기능 | 설명 |
|---|---|
| 스마트 분류 | 초음파 센서로 사용자 접근 감지 → 카메라 활성화 → YOLO 분류 → LCD 안내 |
| 환경 모니터링 | 대기 중 온도/습도 측정 → LCD에 실시간 표시 |
| 페일세이프 | 카메라/센서 오류 자동 감지 및 복구 |

### 보너스 기능 (추가 아이디어)
| 기능 | 설명 |
|---|---|
| Notion 클라우드 연동 | 분류 결과를 Notion API로 실시간 기록 |
| 자동 복구 | Remote I/O 에러 발생 시 rpicam 프로세스 자동 재시작 |
| 센서 이상 감지 | 초음파 센서 연속 오류 시 LCD에 경고 표시 |

---

## 🔧 시스템 동작 흐름

```
사용자 접근
    ↓
초음파 센서 감지 (50cm 이내)
    ↓
카메라 활성화 & 촬영 (rpicam-still)
    ↓
YOLOv8 AI 분류
    ↓
LCD 화면에 분리수거 안내
    ↓
Notion API로 기록 저장
    ↓
대기 모드 (온습도 모니터링)
```

---

## 🛠 하드웨어 구성

| 부품 | 역할 |
|---|---|
| Raspberry Pi 5 | 중앙 처리 (Edge AI) |
| Camera Module (OV5647) | 쓰레기 이미지 촬영 |
| HC-SR04 초음파 센서 | 사용자 접근 감지 |
| DHT11 온습도 센서 | 주변 환경 모니터링 |
| I2C LCD 16x2 (0x27) | 분류 결과 및 안내 출력 |
| 브레드보드 + 점퍼선 + 저항 | 회로 연결 |

### 핀 배치

| 부품 | 핀 |
|---|---|
| HC-SR04 VCC | 2번 (5V) |
| HC-SR04 GND | 6번 (GND) |
| HC-SR04 TRIG | 16번 (GPIO23) |
| HC-SR04 ECHO | 22번 (GPIO25) — 저항 연결 |
| DHT11 VCC | 1번 (3.3V) |
| DHT11 GND | 9번 (GND) |
| DHT11 DATA | 7번 (GPIO4) |
| LCD VCC | 4번 (5V) |
| LCD GND | 14번 (GND) |
| LCD SDA | 3번 (GPIO2) |
| LCD SCL | 5번 (GPIO3) |

---

## 💻 소프트웨어 구성

| 항목 | 내용 |
|---|---|
| OS | Raspberry Pi OS |
| AI 모델 | YOLOv8n (ultralytics) |
| 언어 | Python 3 |
| 클라우드 연동 | Notion API (REST API / Bearer Token) |

### 분류 카테고리

| 감지 객체 | 분류 | 배출 위치 |
|---|---|---|
| bottle, cup | Plastic | 플라스틱 통 |
| can, scissors | Can/Metal | 캔 통 |
| book, paper | Paper | 종이 통 |
| apple, banana | Food | 음식물 통 |
| 기타 | General | 일반쓰레기 통 |

---

## 📦 설치 방법

```bash
# 1. 패키지 업데이트
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-dev python3-smbus i2c-tools rpicam-apps

# 2. Python 라이브러리 설치
pip3 install adafruit-blinka adafruit-circuitpython-dht smbus2 --break-system-packages
pip3 install torch torchvision --break-system-packages --index-url https://download.pytorch.org/whl/cpu
pip3 install ultralytics --no-deps --break-system-packages
pip3 install matplotlib scipy ultralytics-thop opencv-python --break-system-packages
pip3 install requests --break-system-packages

# 3. I2C 활성화
sudo raspi-config
# Interface Options → I2C → Yes

# 4. 실행
cd ~/smart_recycling
python3 main.py
```

---

## ☁️ Notion 연동 설정

1. [notion.so/my-integrations](https://www.notion.so/my-integrations) 에서 통합 생성
2. 데이터베이스 페이지 생성 후 통합 연결
3. `main.py` 에서 토큰 및 DB ID 입력:

```python
NOTION_TOKEN = "your_token_here"
DATABASE_ID = "your_database_id_here"
```

### Notion 데이터베이스 컬럼 구성

| 컬럼명 | 타입 |
|---|---|
| Name | 제목 |
| Time | 날짜 |
| Category | 텍스트 |
| Confidence | 숫자 |
| Temperature | 숫자 |
| Humidity | 숫자 |

---

## 👥 팀원 역할

| 이름 | 역할 |
|---|---|
| 고근형 | 메인 코드 개발, 하드웨어 연결, Notion 연동 |
| 팀원 B | 페일세이프 기능 구현 |
| 팀원 C | PPT 발표 자료, Notion 보고서 작성 |

--
