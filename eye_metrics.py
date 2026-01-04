

#EAR, Blink ve PERCLOS
#temel olarak goz metriklerini cikaran dosya

import time #zaman islemleri icin kullanilan temel kutuphane
import numpy as np #sayısal islemler icin kullanilan temel kutuphane

#mediapipe facemesh landmark indeksleri
#her goz icin 6 farkli nokta secilir
LEFT_EAR_IDX  = [33, 159, 158, 133, 153, 144]
RIGHT_EAR_IDX = [362, 386, 387, 263, 374, 380]

#gozun cevresinden secilen noktalar, goz cevresine cerceve cizdirebilmek icin
LEFT_EYE_IDX  = [33, 133, 160, 159, 158, 157, 173]
RIGHT_EYE_IDX = [362, 263, 387, 386, 385, 384, 398]

#iki nokta arasi duz mesafeyi alir
def euclidean_dist(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

""" EAR HESAPLAMA """
#goz kapainca dikey mesafe kuculur EAR duser
def eye_aspect_ratio(eye):
    p1, p2, p3, p4, p5, p6 = eye
    A = euclidean_dist(p2, p6) #gozun dikey acikligi (ust)
    B = euclidean_dist(p3, p5) #gozun dikey acikligi (alt)
    C = euclidean_dist(p1, p4) #gozun yatay genisligi
    return (A + B) / (2.0 * C)

#__init__ bir siniftan nesne olusturuldugunda otomatik calisan kurucu fonksiyon 
#baslangic ayarlarini yapar
#treshold=0.21 0.21 alti goz kapali kabul edilir
class EyeMetrics:
    def __init__(self, ear_threshold=0.21, perclos_tau=25.0):

        self.ear_threshold = ear_threshold

        #blink
        self.blink_count = 0 #blink cout sifirdan baslar
        self.blink_flag = False #bu bayrak goz kapaliyi tutar goz acik duruma gecince kirpma sayar
        self.start_time = time.time() #dakikadaki kirpma hesabi icindir

        #perclos EMA
        #gozun birkaç saniyede kapali kalma egilimi 
        #smooth bir gecis saglar
        self.perclos_ema = 0.0
        self.prev_time = time.time()
        self.perclos_tau = perclos_tau

    #mediapipe landmarklar 0-1 arasi normalizedir
    #bu degerler piksele cevrildi
    def update(self, face_landmarks, w, h):
        #EAR sol
        left_eye_pts = []
        for idx in LEFT_EAR_IDX:
            lm = face_landmarks[idx]
            left_eye_pts.append((int(lm.x * w), int(lm.y * h)))
        left_ear = eye_aspect_ratio(left_eye_pts)

        #EAR sag
        right_eye_pts = []
        for idx in RIGHT_EAR_IDX:
            lm = face_landmarks[idx]
            right_eye_pts.append((int(lm.x * w), int(lm.y * h)))
        right_ear = eye_aspect_ratio(right_eye_pts)
        
        #EAR ortalama
        ear = (left_ear + right_ear) / 2.0

        """" BLINK HESAPLAMA """
        if ear < self.ear_threshold:
            self.blink_flag = True
        else:
            if self.blink_flag:
                self.blink_count += 1
                self.blink_flag = False
        
        #blink rate
        elapsed = time.time() - self.start_time
        blink_rate = self.blink_count / (elapsed / 60.0) if elapsed > 0 else 0.0

        """ PERCLOS HESAPLAMA """
        now = time.time()
        dt = max(1e-3, now - self.prev_time)
        self.prev_time = now

        is_closed = 1.0 if ear < self.ear_threshold else 0.0
        beta = np.exp(-dt / self.perclos_tau)
        self.perclos_ema = beta * self.perclos_ema + (1 - beta) * is_closed
        perclos = float(self.perclos_ema)

        #goz kutulari
        lx, ly = [], []
        for idx in LEFT_EYE_IDX:
            p = face_landmarks[idx]
            lx.append(int(p.x * w))
            ly.append(int(p.y * h))
        left_box = (min(lx)-5, min(ly)-5, max(lx)+5, max(ly)+5)

        rx, ry = [], []
        for idx in RIGHT_EYE_IDX:
            p = face_landmarks[idx]
            rx.append(int(p.x * w))
            ry.append(int(p.y * h))
        right_box = (min(rx)-5, min(ry)-5, max(rx)+5, max(ry)+5)

        """ CIKTI """
        return ear, self.blink_count, blink_rate, perclos, left_box, right_box