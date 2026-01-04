#siniflandirma yapar
#verilen karar gore sesli uyari verir

import time #zaman islemleri icin temel kutuphane 
import subprocess #beepalert macOS icin gerekli kutuphaneler
import sys #beepalert macOS icin gerekli kutuphaneler

PERCLOS_DROWSY = 0.30 #uykululuk esigi (0-1)

#RGB
GREEN  = (0, 255, 0)
YELLOW = (0, 255, 255)
RED    = (0, 0, 255)

""" SINIFLANDIRMA """
def classify_attention(face_found: bool, #yuz bulundu mu
                       perclos: float, #goz kapalilik orani
                       offscreen_state: str, #headpose durumu
                       focus_status: str #mouse/ keyboard durumu
                       ):

    #karar sirasi onemlidir
    #yuz yok > uykulu > offscreen > input pasif > normal
    if not face_found:
        return "Distracted", YELLOW, "Yuz algilanamadi", 1

    if perclos >= PERCLOS_DROWSY:
        return "Drowsy", RED, f"PERCLOS yuksek: {perclos:.2f}", 2

    if offscreen_state != "OnScr":
        return "Distracted", YELLOW, f"OffScreen: {offscreen_state}", 1

    if focus_status in ("FocDrop", "MouseInactive", "KeyboardInactive"):
        return "Distracted", YELLOW, f"Input: {focus_status}", 1

    return "Normal", GREEN, "Odak normal", 0

#siniflandirma sonucuna gore sesli uyari verir
class BeepAlert:
    def __init__(self, enabled=True, cooldown_sec=1.5):
        self.enabled = enabled
        self.cooldown_sec = cooldown_sec
        self._last = 0.0
        self._winsound = None
        
        #platform bilgisi macOs icin
        self._is_mac = (sys.platform == "darwin")
        self._is_win = (sys.platform.startswith("win"))
        
        try:
            import winsound
            self._winsound = winsound
        except Exception:
            self._winsound = None
            
    def _beep_mac(self, times=1):
        # macOS sistem bip sesi (beep)
        # times kadar tekrar
        try:
            script = "beep\n" * times
            subprocess.run(["osascript", "-e", script], check=False)
        except Exception:
            pass

    def trigger(self, label: str):
        if not self.enabled:
            return

        now = time.time()
        if now - self._last < self.cooldown_sec:
            return
        self._last = now

        try:
            # Drowsy: 2 kez, Distracted: 1 kez
            if label.startswith("Drowsy"):
                if self._winsound is not None:
                    self._winsound.Beep(1200, 180)
                    self._winsound.Beep(1200, 180)
                elif self._is_mac:
                    self._beep_mac(times=2)

            elif label.startswith("Distracted"):
                if self._winsound is not None:
                    self._winsound.Beep(900, 180)
                elif self._is_mac:
                    self._beep_mac(times=1)

        except Exception:
            pass