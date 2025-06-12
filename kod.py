import cv2 as cv
import numpy as np
import time
import RPi.GPIO as GPIO
from picamera2 import Picamera2

# ========== MOTOR PINLERI ========== #
AIN1, AIN2 = 17, 27
BIN1, BIN2 = 23, 24
ENA = 18
STBY = 22

# ========== GPIO AYARI ========== #
GPIO.setmode(GPIO.BCM)
GPIO.setup([AIN1, AIN2, BIN1, BIN2, STBY, ENA], GPIO.OUT)

pwm_on = GPIO.PWM(ENA, 1000)
pwm_arka = GPIO.PWM(BIN1, 1000)
pwm_on.start(0)
pwm_arka.start(0)

GPIO.output(STBY, GPIO.HIGH)
GPIO.output(BIN2, GPIO.LOW)

# ========== MOTOR FONKSIYONLARI ========== #
def on_direksiyon_zamanli(yon, aci):
    if yon == "DUZ" or aci < 5:
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.LOW)
        return

    sure = min(aci * 0.02, 0.5)
    print(f"[DIREKSIYON] {yon} yï¿½nï¿½ne {aci}ï¿½ iï¿½in {sure:.2f} sn yï¿½n veriliyor.")

    if yon == "SOL":
        GPIO.output(AIN1, GPIO.HIGH)
        GPIO.output(AIN2, GPIO.LOW)
    elif yon == "SAG":
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.HIGH)

    time.sleep(sure)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

def arka_motor_ileri(hiz=40):
    pwm_arka.ChangeDutyCycle(hiz)

def motorlari_durdur():
    pwm_on.ChangeDutyCycle(0)
    pwm_arka.ChangeDutyCycle(0)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)
# ========== TRAFIK ISIGI TESPIT ========== #
def traffic_light_status(frame):
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 150, 150])
    upper_red1 = np.array([10, 255, 255])
    mask1 = cv.inRange(hsv, lower_red1, upper_red1)

    lower_red2 = np.array([160, 150, 150])
    upper_red2 = np.array([179, 255, 255])
    mask2 = cv.inRange(hsv, lower_red2, upper_red2)

    red_mask = mask1 + mask2

    lower_green = np.array([45, 100, 100])
    upper_green = np.array([75, 255, 255])
    green_mask = cv.inRange(hsv, lower_green, upper_green)

    red_pixels = cv.countNonZero(red_mask)
    green_pixels = cv.countNonZero(green_mask)

    print(f"[LED ANALIZ] RED: {red_pixels} | GREEN: {green_pixels}")

    if red_pixels > 2000:
        return "red"
    elif green_pixels > 500:
        return "green"
    else:
        return "unknown"

# ========== SERIT TAKIP FONKSIYONLARI ========== #
tek_serit_ofset = 65
piksel_derece = 4

def kenar_tespit(goruntu):
    hsv = cv.cvtColor(goruntu, cv.COLOR_BGR2HSV)
    alt_mor = np.array([125, 50, 50])
    ust_mor = np.array([155, 255, 255])
    maske = cv.inRange(hsv, alt_mor, ust_mor)
    maske = cv.morphologyEx(maske, cv.MORPH_OPEN, np.ones((5, 5), np.uint8))
    maske = cv.morphologyEx(maske, cv.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    kenar = cv.Canny(maske, 50, 150)
    return kenar

def ilgili_bolge(goruntu):
    yukseklik, genislik = goruntu.shape[:2]
    bolge = np.array([[ 
        (0, int(0.98 * yukseklik)),
        (genislik, int(0.98 * yukseklik)),
        (int(0.9 * genislik), int(0.5 * yukseklik)),
        (int(0.1 * genislik), int(0.5 * yukseklik))
    ]])
    maske = np.zeros_like(goruntu)
    cv.fillPoly(maske, bolge, (255, 255, 255))
    return cv.bitwise_and(goruntu, maske)

def sol_sag_tespiti(cizgiler, yukseklik):
    sol, sag = [], []
    if cizgiler is None:
        return np.array([0,0,0,0]), np.array([0,0,0,0])
    for c in cizgiler:
        x1, y1, x2, y2 = c.reshape(4)
        m = (y2 - y1) / (x2 - x1) if x2 != x1 else 0
        b = y1 - m * x1
        (sol if m < 0 else sag if m > 0 else []).append((m, b))
    return serit_koordinatlari(sol, yukseklik), serit_koordinatlari(sag, yukseklik)

def serit_koordinatlari(dogrular, yukseklik):
    if not dogrular:
        return np.array([0, 0, 0, 0])
    egimler = [e for e, _ in dogrular]
    kesisimler = [k for _, k in dogrular]
    m, c = np.mean(egimler), np.mean(kesisimler)
    if m == 0:
        return np.array([0, 0, 0, 0])
    y1 = int(0.95 * yukseklik)
    y2 = int(0.6 * yukseklik)
    x1 = int((y1 - c) / m)
    x2 = int((y2 - c) / m)
    return np.array([x1, y1, x2, y2])

def orta_nokta_x(sol, sag, genislik):
    if sol[2] == 0 and sag[2] == 0:
        return genislik // 2
    elif sol[2] == 0:
        return int(sag[2] - tek_serit_ofset)
    elif sag[2] == 0:
        return int(sol[2] + tek_serit_ofset)
    else:
        return int((sol[2] + sag[2]) / 2)

def yon_ve_aci(orta_x, merkez_x):
    fark = merkez_x - orta_x
    aci = int(fark / piksel_derece)
    yon = "DUZ"
    if aci > 0:
        yon = "SOL"
    elif aci < 0:
        yon = "SAG"
    return yon, abs(aci)

def hiz_goster(goruntu, hiz):
    basx, basy = 420, 300
    cv.putText(goruntu, "HIZ:", (350, 300), cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    for i in range(hiz):
        x = basx + i * 12
        y2 = basy - (i + 1) * 7
        cv.line(goruntu, (x, basy), (x, y2), (0, 0, 255), 4)

def cizgileri_ciz(goruntu, cizgiler):
    yeni = np.zeros_like(goruntu)
    for c in cizgiler:
        if c[2] == 0:
            continue
        x1, y1, x2, y2 = c.reshape(4)
        yeni = cv.line(yeni, (x1, y1), (x2, y2), (255, 0, 0), 3)
    return cv.addWeighted(goruntu, 0.8, yeni, 1, 0)

# ========== ANA ISLEM FONKSIYONLARI ========== #
def serit_takip(frame):
    yukseklik, genislik = frame.shape[:2]
    merkez_x = genislik // 2

    kenarlar = kenar_tespit(frame)
    cv.imshow("Kenarlar", kenarlar)

    roi = ilgili_bolge(kenarlar)
    cv.imshow("ROI Bï¿½lgesi", roi)

    cizgiler = cv.HoughLinesP(roi, 1, np.pi / 180, 20, minLineLength=15, maxLineGap=10)
    sol, sag = sol_sag_tespiti(cizgiler, yukseklik)

    frame_cizgili = cizgileri_ciz(frame.copy(), (sol, sag))

    orta_x = orta_nokta_x(sol, sag, genislik)
    cv.line(frame_cizgili, (merkez_x, int(0.6 * yukseklik)), (orta_x, int(0.6 * yukseklik)), (0,0,255), 2)

    yon, aci = yon_ve_aci(orta_x, merkez_x)

    cv.putText(frame_cizgili, f"Aci: {aci}'", (350, 250), cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv.putText(frame_cizgili, yon, (420, 250), cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    hiz = max(1, 5 - min(aci // 5, 4))
    hiz_goster(frame_cizgili, hiz)

    cv.imshow("Serit Takip Sistemi", frame_cizgili)

    on_direksiyon_zamanli(yon, aci)
    arka_motor_ileri(hiz=60)

def main(frame):
    global red_seen

    status = traffic_light_status(frame)

    if status == "red":
        motorlari_durdur()
        red_seen = True
        print("[TRAFFIC] KIRMIZI -> DUR")
    elif status == "green":
        red_seen = False
        serit_takip(frame)
    elif status == "unknown":
        if red_seen:
            motorlari_durdur()
            print("[TRAFFIC] BILINMEYEN (ï¿½nce kï¿½rmï¿½zï¿½) -> BEKLE")
        else:
            serit_takip(frame)

# ========== PROGRAM BASLANGICI ========== #
if _name_ == "_main_":
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)}))
    picam2.start()

    red_seen = False

    try:
        while True:
            frame = picam2.capture_array()
            main(frame)
            if cv.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Program durduruldu.")

    finally:
        motorlari_durdur()
        pwm_on.stop()
        pwm_arka.stop()
        GPIO.cleanup()
        cv.destroyAllWindows()