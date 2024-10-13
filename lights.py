import DMXEnttecPro

def set_color(dmx, dim, r, g, b, w):
    dmx.set_channel(4, dim)
    dmx.set_channel(5, r)
    dmx.set_channel(6, g)
    dmx.set_channel(7, b)
    dmx.set_channel(8, w)
    dmx.submit()

def mainloop():
    dmx = DMXEnttecPro.Controller('/dev/ttyUSB0')
    set_color(dmx, 160, 0, 180, 180, 0)

    while True:
        # ... existing code ...
        # Example of activating lights
        set_color(dmx, 255, 255, 0, 0, 0)
        # Example of turning off lights
        set_color(dmx, 160, 0, 180, 180, 0)
        # ... existing code ...

if __name__ == "__main__":
    mainloop()