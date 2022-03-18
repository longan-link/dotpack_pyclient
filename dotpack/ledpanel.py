import sys
# import string
import asyncio
from bleak import BleakClient
# from PIL import Image

MODEL_NBR_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_RX = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_TX = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


class ledpanel:
    macaddr = None
    status = None
    client = None

    def __init__(self, address):
        self.client = BleakClient(address)

    async def __anext__(self):
        await self.disconnect()

    def handle_rx(self, _: int, data: bytearray):
        # print("received:", data)
        pass

    async def connect(self):
        try:
            await self.client.connect()  # windows/ubuntu will automatically change MTU to maximum so we do not need to set manually here
        except Exception as e:
            print(e)
        try:
            await self.client.start_notify(CHARACTERISTIC_UUID_TX, self.handle_rx)
        except Exception as e:
            print(e)

    async def disconnect(self):
        await asyncio.sleep(0.1)
        try:
            await self.client.stop_notify(CHARACTERISTIC_UUID_TX)
        except Exception as e:
            print(e)

        try:
            await self.client.disconnect()
        except Exception as e:
            print(e)

    async def on(self):
        # data="$1 1;"
        data = bytearray("$1 1;", "utf-8")
        try:
            await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
        except Exception as e:
            print(e)

    async def off(self):
        data = bytearray("$1 0;", "utf-8")
        # data=
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def cleareeprom(self):
        data = bytearray("$1 3;", "utf-8")
        # data=
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    # brightness >=0 <=255
    async def set_brightness(self, brightness):
        if brightness >= 0 and brightness <= 255:
            data = bytearray("$4 0 %d;" % (brightness), "utf-8")
        else:
            return
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def upload_image(self, pilimage):
        if pilimage is None:
            sys.exit("Could not read the image.")
        # cv.imshow("Display window", img)
        dim = (16, 16)
        out = pilimage.resize(dim)
        bufferall = {}
        bufferline = None

        for y in range(16):
            bufferline = "$6 11|%d " % (y)
            for x in range(16):
                r, g, b = out.getpixel((x, y))
                # print("B: %x G: %x R: %x" %(out[y,x,0],out[y,x,1],out[y,x,2])) # B G R format
                if r < 16:
                    bufferline = bufferline + "0" + ("%x" % (r))
                else:
                    bufferline = bufferline + ("%x" % (r))
                if g < 0x10:
                    bufferline = bufferline + "0" + ("%x" % (g))
                else:
                    bufferline = bufferline + ("%x" % (g))
                if b < 0x10:
                    bufferline = bufferline + "0" + ("%x" % (b))
                else:
                    bufferline = bufferline + ("%x" % (b))
                if x == 15:
                    bufferline = bufferline + (" %d;" % (x))
                else:
                    bufferline = bufferline + (" %d|" % (x))
            bufferall[y] = bufferline
            # print(bufferall[y])
            pass

        for i in range(16):
            data = bytearray(bufferall[i], "utf-8")
            await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
            await asyncio.sleep(0.08)

    async def set_mode(self, mode):
        if mode == "black":
            data = bytearray("$14 0;", "utf-8")
        elif mode == "white":
            data = bytearray("$14 1;", "utf-8")
        elif mode == "color":
            data = bytearray("$14 2;", "utf-8")
        elif mode == "fire":
            data = bytearray("$14 3;", "utf-8")
        elif mode == "confetti":
            data = bytearray("$14 4;", "utf-8")
        elif mode == "rainbow":
            data = bytearray("$14 5;", "utf-8")
        elif mode == "matrix":
            data = bytearray("$14 6;", "utf-8")
        elif mode == "fireflies":
            data = bytearray("$14 7;", "utf-8")
        elif mode == "arrows":
            data = bytearray("$14 8;", "utf-8")
        elif mode == "noise_ocean":
            data = bytearray("$14 9;", "utf-8")
        elif mode == "snow":
            data = bytearray("$14 10;", "utf-8")
        elif mode == "ball":
            data = bytearray("$14 11;", "utf-8")
        elif mode == "balls":
            data = bytearray("$14 12;", "utf-8")
        elif mode == "starfall":
            data = bytearray("$14 13;", "utf-8")
        elif mode == "sparkles":
            data = bytearray("$14 14;", "utf-8")
        elif mode == "noise_madness":
            data = bytearray("$14 15;", "utf-8")
        elif mode == "noise_cloud":
            data = bytearray("$14 16;", "utf-8")
        elif mode == "noise_lava":
            data = bytearray("$14 17;", "utf-8")
        elif mode == "noise_plasma":
            data = bytearray("$14 18;", "utf-8")
        elif mode == "noise_rainbow":
            data = bytearray("$14 19;", "utf-8")
        elif mode == "noise_rrainbow_strip":
            data = bytearray("$14 20;", "utf-8")
        elif mode == "noise_zebra":
            data = bytearray("$14 21;", "utf-8")
        elif mode == "noise_forest":
            data = bytearray("$14 22;", "utf-8")
        elif mode == "colors":
            data = bytearray("$14 23;", "utf-8")
        elif mode == "swirl":
            data = bytearray("$14 24;", "utf-8")
        elif mode == "cyclon":
            data = bytearray("$14 25;", "utf-8")
        elif mode == "flicker":
            data = bytearray("$14 26;", "utf-8")
        elif mode == "pacifica":
            data = bytearray("$14 27;", "utf-8")
        elif mode == "shadows":
            data = bytearray("$14 28;", "utf-8")
        elif mode == "maze":
            data = bytearray("$14 29;", "utf-8")
        elif mode == "snake":
            data = bytearray("$14 30;", "utf-8")
        elif mode == "tetris":
            data = bytearray("$14 31;", "utf-8")
        elif mode == "arkanoid":
            data = bytearray("$14 32;", "utf-8")
        elif mode == "palette":
            data = bytearray("$14 33;", "utf-8")
        elif mode == "analyzer":
            data = bytearray("$14 34;", "utf-8")
        elif mode == "fire2":
            data = bytearray("$14 37;", "utf-8")
        elif mode == "s8":
            data = bytearray("$8 2 41 1;", "utf-8")
        elif mode == "clock":
            data = bytearray("$14 40;", "utf-8")
        elif mode == "nightclock":
            data = bytearray("$14 38;", "utf-8")
        elif mode == "offclock":
            data = bytearray("$8 5 1 0;", "utf-8")
        else:
            return
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def set_effect_change_mode(self, changeMode):
        if changeMode == "manual":
            data = bytearray("$16 0;", "utf-8")
        if changeMode == "auto":
            data = bytearray("$16 1;", "utf-8")
        if changeMode == "prevMode":
            data = bytearray("$16 2;", "utf-8")
        if changeMode == "nextMode":
            data = bytearray("$16 3;", "utf-8")
        if changeMode == "on/offRandomSelectNext":
            data = bytearray("$16 5;", "utf-8")
        else:
            return
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def request_fs_files(self):
        data = bytearray("$5 5 0;", "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
        # await asyncio.sleep(0.01) #really needed?
        # files=await self.client.read_gatt_char(CHARACTERISTIC_UUID_TX)
        # return files

    async def save_current_picture(self, fs: str, filename: str):
        if fs == "FS":
            data = bytearray("$6 16|FS %s" % (filename), "utf-8")
        elif fs == "SD":
            data = bytearray("$6 16|SD %s" % (filename), "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def delete_picture(self, fs: str, filename: str):
        if fs == "FS":
            data = bytearray("$6 17|FS %s" % (filename), "utf-8")
        elif fs == "SD":
            data = bytearray("$6 17|SD %s" % (filename), "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def display_fs_picture(self, fs: str, filename: str):
        if fs == "FS":
            data = bytearray("$6 15|FS %s" % (filename), "utf-8")
        elif fs == "SD":
            data = bytearray("$6 15|SD %s" % (filename), "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def filerename(self, fs: str, olefilename: str, newfilename: str):
        if fs == "FS":
            data = bytearray("$6 18|FS %s|%s" % (olefilename, newfilename), "utf-8")
        elif fs == "SD":
            data = bytearray("$6 18|SD %s|%s" % (olefilename, newfilename), "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def getfile(self, fs: str, filename: str):
        if fs == "FS":
            data = bytearray("$6 19|FS %s" % (filename), "utf-8")
        elif fs == "SD":
            data = bytearray("$6 19|SD %s" % (filename), "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
        for i in range(15):
            data = bytearray("$18 0;", "utf-8")
            await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
            await asyncio.sleep(0.05)

    async def delete_allpicture(self, fs: str):
        if fs == "FS":
            data = bytearray("$6 20|FS", "utf-8")
        elif fs == "SD":
            data = bytearray("$6 20|SD", "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def ssidd(self, ssid: str):
        data = bytearray("$6 2|%s" % (ssid), "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def wifipassword(self, password: str):
        data = bytearray("$6 3|%s" % (password), "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def firmware_ver(self):
        data = bytearray("$21 3;", "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def wificlient(self):
        data = bytearray("$21 2;", "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def wifiip(self, wifiip: str):
        data = bytearray("$21 1 %s;" % (wifiip), "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def apon(self):
        data = bytearray("$21 0 1 %s;", "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def clear(self):
        data = bytearray("$5 1;", "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def ledimage(self):
        data = bytearray("$5 4;", "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

        for i in range(15):
            data = bytearray("$18 0;", "utf-8")
            await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
            await asyncio.sleep(0.02)

    async def fill_color(self, colorR: int, colorG: int, colorB: int):
        if (
            colorR <= 0xFF
            and colorR >= 0
            and colorG <= 0xFF
            and colorG >= 0
            and colorB <= 0xFF
            and colorB >= 0
        ):
            if colorR < 0x10:
                hexR = "0%x" % colorR
            else:
                hexR = "%x" % colorR
            if colorG < 0x10:
                hexG = "0%x" % colorG
            else:
                hexG = "%x" % colorG
            if colorB < 0x10:
                hexB = "0%x" % colorB
            else:
                hexB = "%x" % colorB
            data = bytearray("$5 0 %s%s%s;" % (hexR, hexG, hexB), "utf-8")
            # print(data)
            await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
            data = bytearray("$5 2;", "utf-8")
            await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
        else:
            return

    # color in hexmode :RRGGBB pointx and point y >0 <16
    async def draw_point(
        self, colorR: int, colorG: int, colorB: int, pointx: int, pointy: int
    ):
        # check first
        if (
            colorR <= 0xFF
            and colorR >= 0
            and colorG <= 0xFF
            and colorG >= 0
            and colorB <= 0xFF
            and colorB >= 0
            and pointx >= 0
            and pointx < 16
            and pointy >= 0
            and pointy < 16
        ):
            if colorR < 0x10:
                hexR = "0%x" % colorR
            else:
                hexR = "%x" % colorR
            if colorG < 0x10:
                hexG = "0%x" % colorG
            else:
                hexG = "%x" % colorG
            if colorB < 0x10:
                hexB = "0%x" % colorB
            else:
                hexB = "%x" % colorB
            data = bytearray("$5 0 %s%s%s;" % (hexR, hexG, hexB), "utf-8")
            # print(data)
            await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
            # sleep 10 ms to let mcu's ble stack recover
            await asyncio.sleep(0.01)
            data = bytearray("$5 3 %d %d;" % (pointx, pointy), "utf-8")
            # print(data)
            await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
        else:
            return

    async def tetris(self):
        data = bytearray("$3 2;", "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def left(self):
        data = bytearray("$3 13;", "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def stop(self):
        data = bytearray("$3 15;", "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def speed(self, speed: int):
        data = bytearray("$13 13 %d;" % (speed), "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)

    async def test(self, st: str):
        data = bytearray("%s" % (st), "utf-8")
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data)
