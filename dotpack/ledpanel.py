import sys
import asyncio
from bleak import BleakClient
from PIL import Image
import uuid
from tqdm import tqdm

MODEL_NBR_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_RX = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_TX = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


class DotPackClient:
    def __init__(self, address):
        self.client = BleakClient(address)
        self._q = asyncio.Queue()
        self._err = False
        self._read_end = False
        self._printlog = True

    async def __anext__(self):
        await self.client.stop_notify(CHARACTERISTIC_UUID_TX)
        await self.client.disconnect()

    async def handle_rx(self, _: int, data: bytearray):
        rep = data
        OrderID = rep[-8:]
        OrderID = str(OrderID).split("bytearray(b'")[1].split("')")[0]
        if OrderID == self.get_timestamp_uuid:
            self._read_end = True
            self.previous_data = self.previous_data + rep
        else:
            self._read_end = False
            self.previous_data = self.previous_data + rep

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
        await self.client.stop_notify(CHARACTERISTIC_UUID_TX)
        await self.client.disconnect()

    def _UUID_Check(self, data):
        rep = bytearray(data)
        rep = rep.decode("utf-8")
        Orderlist = str(rep)
        Orderlist = Orderlist.split(",")
        OrderID = Orderlist[-1]
        if Orderlist[1:2] == ["ERR"]:
            self._err = True
        if OrderID == self.get_timestamp_uuid:
            rep = Orderlist[2:-1]
            self.rep_data = rep
            if rep != [] and self._printlog == True:
                rep = ",".join(rep)
                print(rep)
            self._printlog = True
        else:
            print("OrderID-ERROR")
            self._printlog = True

    async def _write_and_read(self, data):
        self._err = False
        self._read_end = False
        self.previous_data = bytearray()
        self.get_timestamp_uuid = str(uuid.uuid4().hex[:8])
        self.get_timestamp_uuid = self.get_timestamp_uuid.replace("-", "")
        data = bytearray(self.get_timestamp_uuid, "utf-8") + data
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_RX, data, response=True)
        while self._read_end == False:
            await asyncio.sleep(0.01)
        return self._UUID_Check(self.previous_data)

    async def on(self):  # 打开点阵屏
        data = bytearray("$1 1;", "utf-8")
        await self._write_and_read(data)

    async def off(self):  # 关闭点阵屏
        data = bytearray("$1 0;", "utf-8")
        await self._write_and_read(data)

    async def clear_eeprom(self):  # 清除eeprom中的内容（包括图片、动图、配置信息、配网信息等）
        data = bytearray("$1 3;", "utf-8")
        await self._write_and_read(data)

    async def get_mtu_value(self):  # 获取当前蓝牙的MTU大小
        data = bytearray("$1 4;", "utf-8")
        await self._write_and_read(data)

    async def get_ble_mac(self):  # 获取蓝牙MAC地址
        data = bytearray("$1 5;", "utf-8")
        await self._write_and_read(data)

    async def set_brightness(self, brightness):  # 设置背光亮度（0-255）
        # brightness >=0 <=255
        if brightness >= 0 and brightness <= 255:
            data = bytearray("$4 0 %d;" % (brightness), "utf-8")
        else:
            return
        await self._write_and_read(data)

    async def upload_and_show_image(self, pilimage):  # 上传图片并显示
        if pilimage is None:
            sys.exit("Could not read the image.")
        dim = (16, 16)
        out = pilimage.resize(dim)
        bufferall = {}
        bufferline = None

        for y in range(16):
            bufferline = "$6 11|%d " % (y)
            for x in range(16):
                r, g, b = out.getpixel((x, y))
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

        for i in range(16):
            data = bytearray(bufferall[i], "utf-8")
            await self._write_and_read(data)
            await asyncio.sleep(0.08)

    async def _upload_image(self, pilimage):  # 上传动图解析出来的图片
        if pilimage is None:
            sys.exit("Could not read the image.")
        dim = (16, 16)
        out = pilimage.resize(dim)
        bufferall = {}
        bufferline = None

        for y in range(16):
            bufferline = "$6 21|%d " % (y)
            for x in range(16):
                r, g, b = out.getpixel((x, y))
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

        for i in range(16):
            self._printlog = False
            data = bytearray(bufferall[i], "utf-8")
            await self._write_and_read(data)

    async def set_effect_mode(self, mode):  # 播放自带的动态效果
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
        await self._write_and_read(data)

    async def set_effect_change_mode(self, changeMode):  # 效果切换设置
        if changeMode == "manual":
            data = bytearray("$16 0;", "utf-8")
        elif changeMode == "auto":
            data = bytearray("$16 1;", "utf-8")
        elif changeMode == "prevMode":
            data = bytearray("$16 2;", "utf-8")
        elif changeMode == "nextMode":
            data = bytearray("$16 3;", "utf-8")
        elif changeMode == "on/offRandomSelectNext":
            data = bytearray("$16 5;", "utf-8")
        else:
            return
        await self._write_and_read(data)

    async def list_images_names(self):  # 获取图片名称列表
        data = bytearray("$5 5 0;", "utf-8")
        await self._write_and_read(data)

    async def function_icon(self, ico: int):  # 显示功能图标
        data = bytearray("$5 6 %d;" % (ico), "utf-8")
        await self._write_and_read(data)

    async def save_current_images(self, filename: str):  # 保存图片命令
        data = bytearray("$6 16|FS %s" % (filename), "utf-8")
        await self._write_and_read(data)

    async def delete_images(self, filename: str):  # 删除图片命令
        data = bytearray("$6 17|FS %s" % (filename), "utf-8")
        await self._write_and_read(data)

    async def display_images(self, filename: str):  # 播放图片
        data = bytearray("$6 15|FS %s" % (filename), "utf-8")
        await self._write_and_read(data)

    async def image_rename(self, olefilename: str, newfilename: str):  # 图片重命名
        data = bytearray("$6 18|FS %s|%s" % (olefilename, newfilename), "utf-8")
        await self._write_and_read(data)

    async def implicitly_get_image_data(self, filename: str):  # 隐式获取图像数据（不显示在点阵屏上）
        data = bytearray("$6 19|FS %s" % (filename), "utf-8")
        await self._write_and_read(data)
        if self._err == False:
            for i in range(15):
                data = bytearray("$18 0;", "utf-8")
                await self._write_and_read(data)
                await asyncio.sleep(0.05)

    async def delete_all_images(self):  # 删除所有的图片
        data = bytearray("$6 20|FS", "utf-8")
        await self._write_and_read(data)

    async def display_Implicitly_image(
        self,
    ):  # 显示隐式上传的图片（buffer中的数据）前提是使用过Implicitly_get_image_data命令，缓冲区有数据
        data = bytearray("$5 7;", "utf-8")
        await self._write_and_read(data)

    async def wifi_ssid(self, ssid: str):  # 设置要连接的WiFi名字
        data = bytearray("$6 2|%s" % (ssid), "utf-8")
        await self._write_and_read(data)

    async def wifi_password(self, password: str):  # 设置要连接的WiFi密码
        data = bytearray("$6 3|%s" % (password), "utf-8")
        await self._write_and_read(data)

    async def firmware_ver(self):  # 获取本版信息
        data = bytearray("$21 3;", "utf-8")
        await self._write_and_read(data)

    async def wifi_client(self):  # WiFi连接
        data = bytearray("$21 2;", "utf-8")
        await self._write_and_read(data)

    async def wifiip(self, wifiip: str):  # 显示WiFi IP
        data = bytearray("$21 1 %s;" % (wifiip), "utf-8")
        await self._write_and_read(data)

    async def apon(self):  # 打开ap功能
        data = bytearray("$21 0 1 %s;", "utf-8")
        await self._write_and_read(data)

    async def clear(self):  # 清除屏幕上的内容
        data = bytearray("$5 1;", "utf-8")
        await self._write_and_read(data)

    async def led_image_data(self):  # 获取点阵屏上的颜色数据
        data = bytearray("$5 4;", "utf-8")
        await self._write_and_read(data)

        for i in range(15):
            data = bytearray("$18 0;", "utf-8")
            await self._write_and_read(data)
            await asyncio.sleep(0.02)

    async def set_background(self, colorR: int, colorG: int, colorB: int):  # 设置背光颜色
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
            await self._write_and_read(data)
            data = bytearray("$5 2;", "utf-8")
            await self._write_and_read(data)
        else:
            return

    # color in hexmode :RRGGBB pointx and point y >0 <16
    async def draw_point(
        self, colorR: int, colorG: int, colorB: int, pointx: int, pointy: int
    ):  # 绘制点
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
            await self._write_and_read(data)
            # sleep 10 ms to let mcu's ble stack recover
            data = bytearray("$5 3 %d %d;" % (pointx, pointy), "utf-8")
            await self._write_and_read(data)
        else:
            return

    async def run_text_on_effects(self, text: str):  # 显示文字在效果上
        data = bytearray("$6 14|%s" % (text), "utf-8")
        await self._write_and_read(data)

    async def scroll_text(self, text: str):  # 显示滚动文字
        data = bytearray("$6 28|%s" % (text), "utf-8")
        await self._write_and_read(data)

    async def text_colormode(self, mode: int):  # 设置文字颜色模式
        data = bytearray(
            "$13 11 %d" % (mode), "utf-8"
        )  # 0 white font    1 gradient font    2 multicolor font
        await self._write_and_read(data)

    async def text_color(self, color: str):  # 设置文字颜色
        data = bytearray("$13 15 %s" % (color), "utf-8")  # COLOR:000000-FFFFFF
        await self._write_and_read(data)

    async def crawl_speed(self, speed: int):  # 设置文字滚动速度
        data = bytearray("$13 13 %d" % (speed), "utf-8")  # SPEED:0-225
        await self._write_and_read(data)

    async def play_text_once(self, text: str):  # 播放文字滚动一次（不循环）
        data = bytearray("$6 29|%s" % (text), "utf-8")
        await self._write_and_read(data)

    async def game_mode(self, game: int):  # 游戏模式选项
        # 选择游戏 - (1:迷宫，2：贪吃蛇，3：俄罗斯方块，4：打砖块)
        # 游戏操作 - (10：向上移动，11:向右移动，12：向下移动，13：向左移动，14：OK键)
        data = bytearray("$3 %d;" % (game), "utf-8")
        await self._write_and_read(data)

    async def move_to_the_left(self):
        data = bytearray("$3 13;", "utf-8")
        await self._write_and_read(data)

    async def game_paused(self):  # 暂停游戏
        data = bytearray("$3 15;", "utf-8")
        await self._write_and_read(data)

    async def continue_game(self):  # 继续游戏
        data = bytearray("$3 16;", "utf-8")
        await self._write_and_read(data)

    async def set_speed(self, speed: int):  # 设置游戏速度
        data = bytearray("$15 %d;" % (speed), "utf-8")
        await self._write_and_read(data)

    async def _save_gif(self, gifname: str, picname: str):  # 保存GIF（保存指令，非上传指令） *
        data = bytearray("$6 23|FS %s|%s" % (gifname, picname), "utf-8")
        await self._write_and_read(data)

    # async def display_gif(self,s:int,p:int,filename:str):  #播放GIF *
    #     data = bytearray("$6 24|FS %d %d|%s"%(s,p,filename),'utf-8')
    #     await self._write_and_read(data)

    #############################

    async def display_gif(self, s: int, filename: str):  # 播放GIF *
        data = bytearray("$6 24|FS %d|%s" % (s, filename), "utf-8")
        await self._write_and_read(data)

    #############################

    async def _display_sys_animation(self, p: int):  # 播放系统中的编程进去的动图，并非上传到flash上的GIF *
        data = bytearray("$5 9 %d" % p, "utf-8")
        await self._write_and_read(data)

    async def get_gif_quantity(
        self, p: int, gifname: str
    ):  # 获取保存到flash中的GIF帧数（用于上传完成后帧数的校对）*
        data = bytearray("$6 26|FS %d|%s" % (p, gifname), "utf-8")
        await self._write_and_read(data)

    async def delete_gif(self, filename: str):  # 删除保存在flash上的GIF动图 *
        data = bytearray("$6 25|FS %s" % (filename), "utf-8")
        await self._write_and_read(data)

    async def renameGIF(self, olefilename: str, newfilename: str):  # 重命名GIF动图 *
        data = bytearray("$6 27|FS %s|%s" % (olefilename, newfilename), "utf-8")
        await self._write_and_read(data)

    async def flash_size(self):  # 获取剩余的空间内存 （总内存和可用内存）
        data = bytearray("$6 34|FS", "utf-8")
        await self._write_and_read(data)

    async def folder_directory(self, directory: str):  # 获取指定文件夹中的文件名 （文件名非文件夹名）
        data = bytearray("$6 30|FS %s" % (directory), "utf-8")
        await self._write_and_read(data)

    async def dirname(self, directory: str):  # 文件夹中的文件夹名 （文件夹名非文件名）
        data = bytearray("$6 32|FS %s" % (directory), "utf-8")
        await self._write_and_read(data)

    async def delete_dir(self, directory: str):  # 删除文件夹（用于删除GIF后删除用来存储GIF动图的文件夹）
        data = bytearray("$6 33|FS %s" % (directory), "utf-8")
        await self._write_and_read(data)

    async def recovery_mode(self):  # 恢复断电前的上一次效果或动图或图片
        data = bytearray("$5 12", "utf-8")
        await self._write_and_read(data)

    async def set_boot_mode(self, mode: int, name: str):  # 设置开机模式
        # $6 35|M Filename 即可设置开机画面，其中M的取值范围为（1-4）指的是所需要设置的模式分别有 ：
        # 1、图片模式 (例：$6 35|1 图像文件名)
        # 2、动图模式（例：$6 35|2 动图文件名）
        # 3、指定特效模式（此设置需要在选定好的特效下发送指令，即可设置当前显示的特效为开机画面 例：$6 35|3）
        # 4、随机特效模式（例：$6 35|4）
        data = bytearray("$6 35|%d %s" % (mode, name), "utf-8")
        await self._write_and_read(data)

    async def upload_animation(self, name, frames):

        # 要求服务端清理
        self._printlog = False
        await self.delete_gif(name)
        self._printlog = False
        await self._display_sys_animation(1)
        i = -1
        for index, frame in tqdm(frames):
            i += 1
            await self._upload_image(frame)
            gifp = name
            picn = str(i)
            await self._save_gif(gifp, picn)
