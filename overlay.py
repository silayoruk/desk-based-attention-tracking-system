""" GORSELLESTIRME VE ARAYUZ """
""" bu dosya, hesaplama yapan dosyalardaki verileri kullaniciya veren gosrel bir panel olusturur"""

import cv2 #openCV 

def put_text(frame, text, org, font, fs, color, th):
    cv2.putText(frame, text, org, font, fs, color, th, lineType=cv2.LINE_AA)

#status metriklerini yazdirma
def draw_status_plain(frame, ear, blink_count, blink_rate, perclos,
                      focus_status, yaw, pitch, offscreen, label,
                      x1=10, y1=20):
    
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FS = 0.75
    TH = 2
    TXT = (255, 255, 255)

    # arka plan kutusu (okunurluk icin)
    panel_w = 320
    panel_h = 260
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1-8, y1-22), (x1+panel_w, y1+panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

    put_text(frame, "STATUS", (x1, y1), FONT, FS, TXT, TH)

    y = y1 + 35
    step = 28
    put_text(frame, f"EAR: {ear:.3f}", (x1, y), FONT, FS, TXT, TH); y += step
    put_text(frame, f"Blink: {blink_count}", (x1, y), FONT, FS, TXT, TH); y += step
    put_text(frame, f"BlinkRate: {blink_rate:.1f}/min", (x1, y), FONT, FS, TXT, TH); y += step
    put_text(frame, f"PERCLOS: {perclos:.2f}", (x1, y), FONT, FS, TXT, TH); y += step
    put_text(frame, f"Focus: {focus_status}", (x1, y), FONT, FS, TXT, TH); y += step
    put_text(frame, f"Yaw: {yaw:.1f}", (x1, y), FONT, FS, TXT, TH); y += step
    put_text(frame, f"Pitch: {pitch:.1f}", (x1, y), FONT, FS, TXT, TH); y += step
    put_text(frame, f"OffScreen: {offscreen}", (x1, y), FONT, FS, TXT, TH); y += step
    put_text(frame, f"Class: {label}", (x1, y), FONT, FS, TXT, TH)

#fps yazdirma
def draw_fps(frame, fps, w, h, pad=10):
    text = f"FPS: {fps:.1f}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    fs = 1.05          
    th = 2

    (tw, th_text), baseline = cv2.getTextSize(text, font, fs, th)
    x = max(pad, w - tw - pad)
    y = max(th_text + pad, 35)

    cv2.putText(frame, text, (x, y), font, fs, (0, 220, 0), th, lineType=cv2.LINE_AA)

#goz kutularini cizme
def draw_boxes(frame, left_box, right_box):
    lx1, ly1, lx2, ly2 = left_box
    rx1, ry1, rx2, ry2 = right_box
    cv2.rectangle(frame, (lx1, ly1), (lx2, ly2), (0, 255, 0), 2)
    cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (0, 255, 255), 2)

#uyari yazdirma
def draw_alert(frame, w, h, label, msg, color):
    cv2.rectangle(frame, (5, 5), (w - 5, h - 5), color, 4)
    cv2.putText(frame, f"Class: {label}", (10, h - 55),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
    cv2.putText(frame, msg, (10, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
