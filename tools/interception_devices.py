"""Listet fuer Geraete 1-20 die Hardware-ID (= echte, angeschlossene Geraete).
So findet deckcore die echte Tastatur automatisch, ohne fixe Geraetenummer.

Aufruf:  python interception_devices.py "<interception.dll>"
"""
import sys, os, ctypes

if len(sys.argv) < 2 or not os.path.isfile(sys.argv[1]):
    print("Aufruf: python interception_devices.py <interception.dll>"); sys.exit(1)
dll = ctypes.WinDLL(sys.argv[1])

dll.interception_create_context.restype = ctypes.c_void_p
dll.interception_destroy_context.argtypes = [ctypes.c_void_p]
dll.interception_get_hardware_id.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
dll.interception_get_hardware_id.restype = ctypes.c_uint
dll.interception_is_keyboard.argtypes = [ctypes.c_int]
dll.interception_is_keyboard.restype = ctypes.c_int
dll.interception_is_mouse.argtypes = [ctypes.c_int]
dll.interception_is_mouse.restype = ctypes.c_int

ctx = dll.interception_create_context()
if not ctx:
    print("Kein Context -> Treiber nicht erreichbar."); sys.exit(2)

buf = ctypes.create_unicode_buffer(512)
print("Geraet | typ      | Hardware-ID")
print("-------+----------+------------")
for d in range(1, 21):
    n = dll.interception_get_hardware_id(ctx, d, buf, ctypes.sizeof(buf))
    typ = "Tastatur" if dll.interception_is_keyboard(d) else ("Maus" if dll.interception_is_mouse(d) else "?")
    hid = buf.value if n > 0 else ""
    if hid:
        print("  %2d   | %-8s | %s" % (d, typ, hid))
dll.interception_destroy_context(ctx)
print("\n(Nur Geraete mit Hardware-ID sind echt angeschlossen.)")
