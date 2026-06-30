"""Beweis-Test: schickt Strg+Shift+1 ueber den Interception-Treiber = wie ECHTE Hardware.
Wenn TTLS jetzt zur Szene 'Allgemein' schaltet, funktioniert der Weg -> dann baue ich ihn in RigzDeck ein.

Aufruf:  python interception_test.py  [optional: pfad zu interception.dll]
Die DLL liegt im Interception-Download unter:  library\\x64\\interception.dll  (x64 fuer 64-bit-Python!)
"""
import sys, os, glob, ctypes, time

def find_dll():
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        return sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    for c in [os.path.join(here, "interception.dll")] + \
             glob.glob(os.path.join(os.path.expanduser("~"), "Down*", "**", "x64", "interception.dll"), recursive=True):
        if os.path.isfile(c):
            return c
    return None

path = find_dll()
if not path:
    print("interception.dll nicht gefunden.")
    print("Aufruf:  python interception_test.py \"C:\\Pfad\\zu\\library\\x64\\interception.dll\"")
    sys.exit(1)
print("Lade DLL:", path)
try:
    dll = ctypes.WinDLL(path)
except OSError as e:
    print("DLL laedt nicht (32/64-bit-Mismatch? nimm die x64-DLL):", e)
    sys.exit(1)

class Stroke(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("state", ctypes.c_ushort), ("information", ctypes.c_uint)]

dll.interception_create_context.restype = ctypes.c_void_p
dll.interception_destroy_context.argtypes = [ctypes.c_void_p]
dll.interception_send.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
dll.interception_send.restype = ctypes.c_int

ctx = dll.interception_create_context()
if not ctx:
    print("Kein Context -> Treiber nicht aktiv. install-interception.exe /install ausgefuehrt + NEU GESTARTET?")
    sys.exit(2)

KEY_DOWN, KEY_UP = 0x00, 0x01
def send(dev, code, state):
    s = Stroke(code, state, 0)
    dll.interception_send(ctx, dev, ctypes.byref(s), 1)

combo = [0x1D, 0x2A, 0x02]    # Scancodes: LCtrl, LShift, '1'
print("\nIn 4s sende ich Strg+Shift+1 als ECHTE Hardware -> TTLS sollte zur Szene 'Allgemein' schalten.")
print("(TTLS muss laufen + Hotkey Strg+Shift+1 gebunden; Vordergrund egal.)")
for i in (4, 3, 2, 1):
    print(" ", i); time.sleep(1)

# Geraet 1 = erstes Keyboard. Falls nichts passiert, probiere ich der Reihe nach 1..10 durch.
for dev in range(1, 11):
    for c in combo: send(dev, c, KEY_DOWN)
    time.sleep(0.02)
    for c in reversed(combo): send(dev, c, KEY_UP)
    time.sleep(0.05)

print("\nGesendet (Geraete 1-10 durchprobiert). Hat TTLS auf 'Allgemein' geschaltet?")
dll.interception_destroy_context(ctx)
