"""Interception-Diagnose: Ist der Treiber wirklich aktiv + welches Geraet ist die echte Tastatur?

1) Setzt einen Filter und wartet auf einen ECHTEN Tastendruck (lernt so das Geraet
   UND beweist, dass der Treiber wirklich Eingaben abfaengt = aktiv).
2) Schickt Strg+Shift+1 auf GENAU dieses Geraet = wie echte Hardware.

Aufruf:  python interception_probe.py "C:\\...\\library\\x64\\interception.dll"
"""
import sys, os, ctypes, time

if len(sys.argv) < 2 or not os.path.isfile(sys.argv[1]):
    print("Aufruf: python interception_probe.py <pfad zu interception.dll (x64)>")
    sys.exit(1)

dll = ctypes.WinDLL(sys.argv[1])

class Stroke(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("state", ctypes.c_ushort), ("information", ctypes.c_uint)]

dll.interception_create_context.restype = ctypes.c_void_p
dll.interception_destroy_context.argtypes = [ctypes.c_void_p]
PREDICATE = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
dll.interception_set_filter.argtypes = [ctypes.c_void_p, PREDICATE, ctypes.c_ushort]
dll.interception_wait_with_timeout.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
dll.interception_wait_with_timeout.restype = ctypes.c_int
dll.interception_receive.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
dll.interception_receive.restype = ctypes.c_int
dll.interception_send.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
dll.interception_send.restype = ctypes.c_int

ctx = dll.interception_create_context()
print("context:", ctx)
if not ctx:
    print("Kein Context -> Treiber gar nicht erreichbar.")
    sys.exit(2)

FILTER_ALL = 0xFFFF
FILTER_NONE = 0x0000

def is_kbd(device):
    return 1 if 1 <= device <= 10 else 0
pred = PREDICATE(is_kbd)

dll.interception_set_filter(ctx, pred, FILTER_ALL)
print("\n>>> Druecke JETZT eine beliebige Taste auf der ECHTEN Tastatur (zum Lernen)... (10s Zeit)")
device = dll.interception_wait_with_timeout(ctx, 15000)
if not device:
    print("\nTIMEOUT - kein echter Tastendruck abgefangen.")
    print("=> Der Treiber faengt NICHTS ab => NICHT aktiv (Install/Reboot unvollstaendig).")
    dll.interception_set_filter(ctx, pred, FILTER_NONE)
    dll.interception_destroy_context(ctx)
    sys.exit(3)

s = Stroke()
dll.interception_receive(ctx, device, ctypes.byref(s), 1)
print("\nECHTE Tastatur = Geraet %d  (erste Taste: code=%d state=%d)" % (device, s.code, s.state))
print("=> Treiber ist AKTIV und faengt echte Tasten ab. Gut.")

# Filter aus -> Tastatur wieder normal
dll.interception_set_filter(ctx, pred, FILTER_NONE)

print("\n>>> In 4s schicke ich Strg+Shift+1 auf Geraet %d (echte Tastatur). TTLS -> 'Allgemein'?" % device)
for i in (4, 3, 2, 1):
    print(" ", i); time.sleep(1)

KEY_DOWN, KEY_UP = 0x00, 0x01
def send(code, state):
    st = Stroke(code, state, 0)
    return dll.interception_send(ctx, device, ctypes.byref(st), 1)

combo = [0x1D, 0x2A, 0x02]   # LCtrl, LShift, '1'
r = 0
for c in combo:
    r += send(c, KEY_DOWN)
time.sleep(0.03)
for c in reversed(combo):
    r += send(c, KEY_UP)
print("\nsend()-Rueckgaben summiert: %d  (>0 = Strokes wurden geschrieben)" % r)

dll.interception_destroy_context(ctx)
print("\nFertig. Hat TTLS auf 'Allgemein' geschaltet?")
