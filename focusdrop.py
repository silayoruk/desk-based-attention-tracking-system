#bilgisayarda fare/klavye dinlenir 
#en son ne zaman aktif kullanildigini tutar
#listener kullanarak surekli sorgu calistirmak yerine olay gelince haber alir

from pynput import mouse, keyboard #fare ve klavye olaylarini yakalamak icin kullanilan temel kutuphane
import time #zaman islemleri icin temel kutuphane
import math #mesafe hesabi icin temel kutuphane

#son etkinlik zamanlarini alir
last_mouse_time = time.time()
last_keyboard_time = time.time()

#mouse mikro hareket filtresi
_LAST_POS = None
MOVE_EPS_PX = 3 #3 piksel altini hareket sayma
MIN_MOVE_INTERVAL = 0.08 #0.08 saniyeden daha sik gelen move eventleri sayma
_last_move_update = 0.0 #son hareket

#listenerlar globalde tutulur
#python objeyi cop sanip kapatmasin
_mouse_listener = None
_keyboard_listener = None
_listeners_started = False

#mouse hareketi
def _update_mouse_activity(x, y):
    global last_mouse_time, _LAST_POS, _last_move_update

    #en son islemden beri 0.08 saniye gecmediyse yoksay
    now = time.time()
    if now - _last_move_update < MIN_MOVE_INTERVAL:
        return

    #daha once hic pozisyon kaydedilmediyse 
    if _LAST_POS is None:
        _LAST_POS = (x, y)
        last_mouse_time = now
        _last_move_update = now #ilk pozisyonu kaydet
        return

    #fareninin konum mesafesi hesaplanir
    dx = x - _LAST_POS[0]
    dy = y - _LAST_POS[1]
    dist = math.hypot(dx, dy)

    #mikro hareket filtresi
    if dist >= MOVE_EPS_PX:
        last_mouse_time = now
        _LAST_POS = (x, y)
        _last_move_update = now

""" FOCU DROP mouse/keyboard"""

#ahreket olunca _update_mouse_activity calistirilir mikro hareket filtresinden gecer
def _on_move(x, y):
    _update_mouse_activity(x, y)

#tiklama olunca zaman guncellenir 
#aktife gecilir
#net bir harekettir filtreye gerek yoktur
def _on_click(x, y, button, pressed):
    global last_mouse_time
    last_mouse_time = time.time()

#scroll olunca zaman guncellenir 
#aktife gecilir
#net bir harekettir filtreye gerek yoktur
def _on_scroll(x, y, dx, dy):
    global last_mouse_time
    last_mouse_time = time.time()

#klavyeden herhangibir tusa basilinca zaman guncellenir
#aktife gecilir
def _on_press(key):
    global last_keyboard_time
    last_keyboard_time = time.time()

#dinleyici bagimsiz bir sekilde calismaya baslar ve surekli olarak mouse ve klavye olaylarini izler
#bu olaylar tetiklendiginde fonksiyonlari calistirir
def start_listeners():
    global _listeners_started, _mouse_listener, _keyboard_listener
    if _listeners_started:
        return

    #listenerlar olusturulur
    _mouse_listener = mouse.Listener(on_move=_on_move, on_click=_on_click, on_scroll=_on_scroll)
    _keyboard_listener = keyboard.Listener(on_press=_on_press)

    #listenerlar baslatilir
    _mouse_listener.start()
    _keyboard_listener.start()

    _listeners_started = True

""" FOCUSDROP HESABI """
def compute_focusdrop(mouse_threshold=120, keyboard_threshold=120):

    now = time.time()
    mouse_idle = now - last_mouse_time
    keyboard_idle = now - last_keyboard_time

    if mouse_idle > mouse_threshold and keyboard_idle > keyboard_threshold:
        return "FocDrop"
    elif mouse_idle > mouse_threshold:
        return "MouseInactive"
    elif keyboard_idle > keyboard_threshold:
        return "KeyboardInactive"
    else:
        return "Active"


#import edilince otomatik baslat
start_listeners()
