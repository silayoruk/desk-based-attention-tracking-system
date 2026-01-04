#headpose, kafa yonu hesabi yapilir

import cv2 #opencv kutuphanesi
import numpy as np #sayisal islemler icin kullanilan temel kutuphane
import time #zaman islemleri icin kullanilan temel kutuphane
from collections import deque #son N degeri saklamak icin koleksiyon

#yuzun 3B basit kafatasi modeli
#solvePnP icin referans sablon
model_points = np.array([
    (0.0, 0.0, 0.0), #burun
    (0.0, -330.0, -65.0), #cene
    (-225.0, 170.0, -135.0), #sol goz kose
    (225.0, 170.0, -135.0), #sag goz kose
    (-150.0, -150.0, -125.0), #sol agiiz kose
    (150.0, -150.0, -125.0) #sag agiz kose
], dtype=np.float32)

#facemeshten alti adet nokta secilerek 3B modeldeki alti noktaya eslenir
#secilen noktalar facemeshin standart landmark noktalaridir
NOSE = 1
CHIN = 152
LEFT_EYE_CORNER = 33
RIGHT_EYE_CORNER = 263
LEFT_MOUTH = 61
RIGHT_MOUTH = 291

#histerizis 
YAW_OFF = 45.0
YAW_ON  = 35.0

PITCH_DOWN_OFF = 18.0
PITCH_DOWN_ON  = 12.0

#stabilizasyon ayarlari
EMA_ALPHA = 0.92 #yumusatma
CONFIRM_FRAMES = 10 #yeni duruma gecmeden once 10 kare ust uste dogrula
MIN_SWITCH_SEC = 0.60 #0.60 saniye gecmeden durum degistirme 
OFF_LOCK_SEC = 1.20 #off 1.2 saniye kilitle 

prev_state = "OnScr" #en son durum
candidate_state = "OnScr" #yeni aday durum
candidate_count = 0 #aday durum sayisi
last_switch_time = 0.0 #en son ne zaman durum degisti

#stabilizasyon
yaw_ema = 0.0
pitch_ema = 0.0
roll_ema = 0.0

yaw_buf = deque(maxlen=7)
pitch_buf = deque(maxlen=7)

#kalibrasyon 
#kamera acisi degisebilir, kameraya ve kisiye gore sifirlar
baseline_set = False
yaw0 = 0.0
pitch0 = 0.0
roll0 = 0.0

#klavyeden C tusu ile kalibrasyon yapilacak
#kullanici pozisyondayken o acilari sifir yapacak
def calibrate_baseline():
    global baseline_set, yaw0, pitch0, roll0, yaw_ema, pitch_ema, roll_ema
    yaw0, pitch0, roll0 = yaw_ema, pitch_ema, roll_ema
    baseline_set = True

#○wrap
#kafa acilarini -180 & +180 arasina sabitler
def _wrap_to_180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0

#normalizasyon 
#kafa acilarini -90 & +90 arasina sabitler
def _normalize_to_90(a: float) -> float:
    a = _wrap_to_180(a)
    if a < -90.0:
        a += 180.0
    elif a > 90.0:
        a -= 180.0
    return a

""" HEAD POSE """
def compute_headpose(face_landmarks, w, h):
    global prev_state, candidate_state, candidate_count, last_switch_time
    global yaw_ema, pitch_ema, roll_ema
    global baseline_set, yaw0, pitch0, roll0
    global yaw_buf, pitch_buf

    #facemeshten gelen 6 adet landmark noktasini piksel koordinatlarina cevirir
    #opencv solvePnP ye uygun sorunsuz format olan np.float32ye cevirir
    image_points = np.array([
        (face_landmarks[NOSE].x * w, face_landmarks[NOSE].y * h),
        (face_landmarks[CHIN].x * w, face_landmarks[CHIN].y * h),
        (face_landmarks[LEFT_EYE_CORNER].x * w, face_landmarks[LEFT_EYE_CORNER].y * h),
        (face_landmarks[RIGHT_EYE_CORNER].x * w, face_landmarks[RIGHT_EYE_CORNER].y * h),
        (face_landmarks[LEFT_MOUTH].x * w, face_landmarks[LEFT_MOUTH].y * h),
        (face_landmarks[RIGHT_MOUTH].x * w, face_landmarks[RIGHT_MOUTH].y * h)
    ], dtype=np.float32)

    #kamera matrisi
    #kameranin yaklasik ic parametreleri
    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float32)

    dist_coeffs = np.zeros((4, 1), dtype=np.float32)

    """ solvePnP ILE KAFA POZU BULMA"""
    #3B yuuz modeli noktalari ile 2B goruntu karsiliklarini esleyerek kafanin kameraya gore donusunu ve konumunu bulur
    #success --> hesap basarili mi?
    #rvec --> rotation vector (kafanin nasil dondugu)
    #tvec --> translation vector (kafanin kameraya gore nerede oldugu)
    success, rvec, tvec = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE #iteratif yontemle coz
    )

    #hesap basarisizsa
    if not success:
        yaw_rel = yaw_ema - yaw0 if baseline_set else yaw_ema
        pitch_rel = pitch_ema - pitch0 if baseline_set else pitch_ema
        roll_rel = roll_ema - roll0 if baseline_set else roll_ema
        return yaw_rel, pitch_rel, roll_rel, prev_state
        #son bilinen durumdan devam et

    #EULER acilari
    rmat, _ = cv2.Rodrigues(rvec)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

    pitch = _normalize_to_90(float(angles[0]))
    yaw   = _normalize_to_90(float(-angles[1]))
    roll  = _wrap_to_180(float(angles[2]))

    #stabilizasyon
    yaw_buf.append(yaw)
    pitch_buf.append(pitch)
    yaw = float(np.median(np.array(yaw_buf)))
    pitch = float(np.median(np.array(pitch_buf)))

    #stabilizasyon
    yaw_ema   = EMA_ALPHA * yaw_ema   + (1 - EMA_ALPHA) * yaw
    pitch_ema = EMA_ALPHA * pitch_ema + (1 - EMA_ALPHA) * pitch
    roll_ema  = EMA_ALPHA * roll_ema  + (1 - EMA_ALPHA) * roll

    #baseline
    yaw_rel = yaw_ema - yaw0 if baseline_set else yaw_ema
    pitch_rel = pitch_ema - pitch0 if baseline_set else pitch_ema
    roll_rel = roll_ema - roll0 if baseline_set else roll_ema

    now = time.time()
    desired = prev_state

    #off kilidi (1.2 saniye)
    if prev_state != "OnScr" and (now - last_switch_time) < OFF_LOCK_SEC:
        desired = prev_state
    
    #onscr --> offscr
    else:
        if prev_state == "OnScr":
            if abs(yaw_rel) > YAW_OFF: #saga sola kafa donusu
                desired = "Yaw-OffScr"
            elif pitch_rel > PITCH_DOWN_OFF: #asagi yukari kafa donusu
                desired = "PitchDown-OffScr"
            else:
                desired = "OnScr"
        else:
            yaw_ok = abs(yaw_rel) < YAW_ON
            down_ok = pitch_rel < PITCH_DOWN_ON
            if yaw_ok and down_ok:
                desired = "OnScr"
            else:
                desired = prev_state

    # debounce
    #desired hemen kabul edilmesin ust uste dogrulansin
    if desired == prev_state: #ayni durumda
        candidate_state = desired
        candidate_count = 0 #sayac sifirlanir 
        
    #yeni durumun ust uste gelmesi beklenir 
    else:
        if desired == candidate_state:
            candidate_count += 1
        else:
            candidate_state = desired
            candidate_count = 1

        #yeni duruma gecmek icin 10 kare ust uste gelmis olmali ve en son degisimmden en az 0.60 saniye gecmis olmali
        if candidate_count >= CONFIRM_FRAMES and (now - last_switch_time) >= MIN_SWITCH_SEC:
            prev_state = candidate_state #prev_state gercekten degisir
            last_switch_time = now #last_switch_time guuncellenir
            candidate_count = 0

    #stabil state dondurulur
    return yaw_rel, pitch_rel, roll_rel, prev_state

