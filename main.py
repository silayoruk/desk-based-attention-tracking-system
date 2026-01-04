#program dosyasi

import cv2 #opencv kutuphanesi
import time #zaman islemleri icin kullanilan temel kutuphane
import mediapipe as mp #landmark islemleri icin temel kutuphane

#proje modulleri entegrasyonu 
from eye_metrics import EyeMetrics
from headpose import compute_headpose, calibrate_baseline
#from focusdrop import compute_focusdrop
from attention import classify_attention, BeepAlert
from overlay import (
    draw_status_plain,
    draw_fps,
    draw_boxes,
    draw_alert
)

#sabitler
EAR_THRESHOLD = 0.21 #EAR esigi
CAM_W, CAM_H = 640, 480 #kamera cozunurlugu

""" PROGRAM """
def main():

    print("OpenCV:", cv2.__version__) #opsiyonel

    #kamera acma ve ayarlama
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Kamera acilamadi")

    #mediapipe facemesh
    mp_face = mp.solutions.face_mesh
    face_mesh = mp_face.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    #nesneleri baslatma
    eye = EyeMetrics(ear_threshold=EAR_THRESHOLD) #her karede goz metriklerini hesaplayack
    beeper = BeepAlert(enabled=True) #uyari gerektiginde beeper

    #FPS 
    prev_t = time.perf_counter()
    fps = 0.0
    alpha = 0.9

    try:
        #ana dongu
        while True:
            ret, frame = cap.read() #kare geldi mi?
            if not ret:
                break

            #openCV framei BGR tutar, mediapipe RGB ister
            #gerekli donusumler
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            #yuz arar
            result = face_mesh.process(rgb)
            face_found = result.multi_face_landmarks is not None

            #once varsayilanlar atanir
            #yuz bulunursa gercek degerlerle guncellenir
            #bulunamazsa program coker
            ear = blink = blink_rate = perclos = 0.0
            yaw = pitch = roll = 0.0
            offscreen_state = "OnScr"
            left_box = right_box = None

            #eger yuz bulunduysa
            if face_found:
                landmarks = result.multi_face_landmarks[0].landmark

                #eye metrics
                ear, blink, blink_rate, perclos, left_box, right_box = \
                    eye.update(landmarks, w, h)

                #headpose
                yaw, pitch, roll, offscreen_state = \
                    compute_headpose(landmarks, w, h)

            #focusdrop
            #focus_status = compute_focusdrop()
            focus_status = "OK"

            #siniflandirma
            label, color, msg, level = classify_attention(
                face_found,
                perclos,
                offscreen_state,
                focus_status
            )

            #sesli alarm
            if level > 0:
                beeper.trigger(label)

            #overlay 
            draw_status_plain(
                frame,
                ear, blink, blink_rate, perclos,
                focus_status, yaw, pitch,
                offscreen_state, label
            )

            if left_box and right_box:
                draw_boxes(frame, left_box, right_box)

            draw_alert(frame, w, h, label, msg, color)
            draw_fps(frame, fps, w, h)

            cv2.imshow("Attention Monitor", frame)

            #FPS hesaplanir ve ekranda gosterilir
            now = time.perf_counter()
            fps = alpha * fps + (1 - alpha) * (1.0 / max(1e-6, now - prev_t))
            prev_t = now

            #klavye ile cikis
            key = cv2.waitKeyEx(1)
            if key == 27:          # ESC
                break
            elif key == ord('c'): # Kalibrasyon
                calibrate_baseline()

    finally:
        #temiz kapanis
        cap.release()
        cv2.destroyAllWindows()


#programin baslangic kosulu
if __name__ == "__main__":
    main()
