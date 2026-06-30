"""Gegenprobe: Tippt per Interception-Treiber einen Text auf GERAET <dev> (default 3 = echte Tastatur).
Beweist, ob Treiber-Injection in normalen Apps (Notepad) ankommt.

Aufruf:  python interception_notepad.py "<pfad zu interception.dll>" [device] [text]
"""
import sys, os, ctypes, time

if len(sys.argv) < 2 or not os.path.isfile(sys.argv[1]):
    print("Aufruf: python interception_notepad.py <interception.dll> [device] [text]")
    sys.exit(1)
dll = ctypes.WinDLL(sys.argv[1])
device = int(sys.argv[2]) if len(sys.argv) > 2 else 3
text = sys.argv[3] if len(sys.argv) > 3 else "test123"

class Stroke(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("state", ctypes.c_ushort), ("information", ctypes.c_uint)]

dll.interception_create_context.restype = ctypes.c_void_p
dll.interception_destroy_context.argtypes = [ctypes.c_void_p]
dll.interception_send.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
dll.interception_send.restype = ctypes.c_int

# Set-1 Scancodes (make codes)
SC = {
 'q':0x10,'w':0x11,'e':0x12,'r':0x13,'t':0x14,'y':0x15,'u':0x16,'i':0x17,'o':0x18,'p':0x19,
 'a':0x1E,'s':0x1F,'d':0x20,'f':0x21,'g':0x22,'h':0x23,'j':0x24,'k':0x25,'l':0x26,
 'z':0x2C,'x':0x2D,'c':0x2E,'v':0x2F,'b':0x30,'n':0x31,'m':0x32,
 '1':0x02,'2':0x03,'3':0x04,'4':0x05,'5':0x06,'6':0x07,'7':0x08,'8':0x09,'9':0x0A,'0':0x0B,
 ' ':0x39,
}

ctx = dll.interception_create_context()
if not ctx:
    print("Kein Context -> Treiber nicht erreichbar."); sys.exit(2)

KEY_DOWN, KEY_UP = 0x00, 0x01
def tap(code):
    d = Stroke(code, KEY_DOWN, 0); u = Stroke(code, KEY_UP, 0)
    r = dll.interception_send(ctx, device, ctypes.byref(d), 1)
    time.sleep(0.01)
    r += dll.interception_send(ctx, device, ctypes.byref(u), 1)
    time.sleep(0.03)
    return r

print("Tippe '%s' auf Geraet %d in 6 Sekunden -> JETZT Notepad oeffnen + reinklicken!" % (text, device))
for i in (6,5,4,3,2,1):
    print(" ", i); time.sleep(1)

total = 0
for ch in text.lower():
    if ch in SC:
        total += tap(SC[ch])
print("\nGesendet. send()-Summe: %d (erwartet %d). Steht '%s' in Notepad?" % (total, 2*len([c for c in text.lower() if c in SC]), text))
dll.interception_destroy_context(ctx)
