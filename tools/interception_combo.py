"""Schickt eine Tastenkombo per Interception auf GERAET <dev> (default 3 = echte Tastatur).
Kein Drücken noetig - nur TTLS beobachten.

Aufruf:  python interception_combo.py "<interception.dll>" [device] [scancodes-hex-komma]
   Beispiele:  ... 3 1D,2A,02   (Strg+Shift+1)   |   ... 3 42   (F8)
"""
import sys, os, ctypes, time

if len(sys.argv) < 2 or not os.path.isfile(sys.argv[1]):
    print("Aufruf: python interception_combo.py <interception.dll> [device] [scancodes-hex-komma]"); sys.exit(1)
dll = ctypes.WinDLL(sys.argv[1])
device = int(sys.argv[2]) if len(sys.argv) > 2 else 3
combo = [int(x, 16) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [0x1D, 0x2A, 0x02]

class Stroke(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("state", ctypes.c_ushort), ("information", ctypes.c_uint)]

dll.interception_create_context.restype = ctypes.c_void_p
dll.interception_destroy_context.argtypes = [ctypes.c_void_p]
dll.interception_send.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
dll.interception_send.restype = ctypes.c_int

ctx = dll.interception_create_context()
if not ctx:
    print("Kein Context -> Treiber nicht erreichbar."); sys.exit(2)

KEY_DOWN, KEY_UP = 0x00, 0x01
def send(code, state):
    st = Stroke(code, state, 0)
    return dll.interception_send(ctx, device, ctypes.byref(st), 1)

print("Sende Scancodes %s auf Geraet %d in 6s -> TTLS auf andere Szene stellen + zuschauen!" % (["0x%02X" % c for c in combo], device))
for i in (6,5,4,3,2,1):
    print(" ", i); time.sleep(1)

r = 0
for c in combo: r += send(c, KEY_DOWN)
time.sleep(0.04)
for c in reversed(combo): r += send(c, KEY_UP)
print("\nGesendet. send()-Summe: %d. Hat TTLS auf 'Allgemein' geschaltet?" % r)
dll.interception_destroy_context(ctx)
