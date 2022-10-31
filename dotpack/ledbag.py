import os
import re
import platform
import time
import uuid
import asyncio

# import logging
import loguru
import threading
from PIL import Image, ImageDraw, ImageFont, ImageSequence  # pillow
from IPython import display
from ipythonblocks import BlockGrid


from .utils import only_device

# ref imagiCharms https://imagilabs.com/app
RED = R = (255, 0, 0)
GREEN = G = (0, 255, 0)
BLUE = B = (0, 0, 255)
ORANGE = O = (255, 165, 0)
YELLOW = Y = (255, 255, 0)
AQUA = A = (0, 255, 255)
PURPLE = P = (148, 0, 211)
MAGENTA = M = (255, 0, 255)
BLACK = K = (0, 0, 0)
WHITE = W = (255, 255, 255)

base_path = os.path.dirname(os.path.realpath(__file__))

# todo 使用 proxy 模式 https://github.com/faif/python-patterns/blob/master/patterns/structural/proxy.py


class DotPack:
    """Class DotPack(16x16) encapsulates the DotPack communication.

    from dotpack import DotPack
    pack = DotPack()
    pack.conect(address)
    pack.set_pixel(0, 0, 'red')

    get device address:
        shell: bleak-lescan

    Coordinate:
        https://learn.adafruit.com/adafruit-gfx-graphics-library/coordinate-system-and-units
    """

    _COLOR = {
        "red": RED,
        "green": GREEN,
        "blue": BLUE,
        "orange": ORANGE,
        "yellow": YELLOW,
        "aqua": AQUA,
        "purple": PURPLE,
        "magenta": MAGENTA,
        "black": BLACK,
        "white": WHITE,
    }

    def __init__(
        self, address="local", logger=None, use_imagicharm_coordinate_system=True
    ):
        # async -> sync
        self.__event_loop = asyncio.new_event_loop()
        self.__lock = threading.Lock()
        self.__thread = threading.Thread(target=self.__event_loop.run_forever)
        self.__thread.start()

        self._ledpanel = None
        self._microblocks_client = None
        self.type = "DotPack"  # ...
        self.size = 16
        self.address = address.strip()
        self._img = Image.new(mode="RGB", size=(self.size, self.size))
        self._show_duration = 0.1
        self._show_scale = 20
        self._use_imagicharm_coordinate_system = use_imagicharm_coordinate_system

        if logger is None:
            self.logger = loguru.logger

    def __del__(self):
        # self.logger.debug('del')
        self.disconnect()

    def _execute(self, coroutine, timeout: float = None):
        """
        async -> sync
            ref: https://github.com/intelino-code/intelino-trainlib-py/blob/master/intelino/trainlib/train.py
        """
        with self.__lock:
            return asyncio.run_coroutine_threadsafe(
                coroutine, self.__event_loop
            ).result(timeout)

    def _is_local(self):
        if self.address == "local":
            return True
        else:
            return False

    def _get_client_type(self, address):
        # wifi
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", address):
            return "Microblocks_firmware"

        # Bluetooth
        if (
            re.match(r"(?:[0-9a-fA-F]:?){12}", address) or len(self.address) == 36
        ):  # MacOS
            return "C_firmware"

    def _generate_name(self):
        return "_" + uuid.uuid4().hex[:8]

    def _resize_to_save(self, img):
        return img.resize(
            (self._show_scale * img.width, self._show_scale * img.height), Image.NEAREST
        )

    def _imshow(self, img, PILimage=True):
        display.clear_output(wait=True)

        imdata = img.getdata()
        grid = BlockGrid(
            self.size, self.size, fill=(0, 0, 0), block_size=self._show_scale
        )
        for block, colors in zip(grid, imdata):
            block.rgb = colors
        display.display(grid)
        time.sleep(self._show_duration)

    def _show_image(self, image, PILimage=True):
        # todo GIF
        if self._ledpanel:
            self._execute(self._ledpanel.upload_and_show_image(image))

        if self._microblocks_client:
            self._microblocks_client.upload_and_show_image(image)

    def _show_here(self, img=None, PILimage=True):
        if img:
            self._imshow(img, PILimage=PILimage)
        else:
            self._imshow(self._img, PILimage=PILimage)

    def __getitem__(self, xy):
        """获取 xy 位置的颜色

        eg: pack[0, 1]"""
        x, y = xy
        return self.get_pixel(x, y)

    def __setitem__(self, xy, value):
        """设置 xy 位置的颜色

        eg: pack[0, 1] = (255, 0, 0)"""
        x, y = xy
        return self.set_pixel(x, y, value)  # set 会如何
        # return self.li[item]

    def connect(self, address=None):
        # 根据 address 蓝牙地址还是wifi地址自动连接
        if address:
            self.address = address.strip()
        if self._is_local():
            return

        if self._get_client_type(self.address) == "Microblocks_firmware":
            from .microblocks_client import MicroblocksClient
            self._microblocks_client = MicroblocksClient(self.address)
            self._microblocks_client.connect()
            print("connected!")
            return True

        if self._get_client_type(self.address) == "C_firmware":
            # fix win7 bleak bug
            from .ledpanel import DotPackClient
            self._ledpanel = DotPackClient(self.address)
            self._execute(self._ledpanel.connect())
            print("connected!")
            return True

    def disconnect(self):
        # print('disconnect')
        if self._ledpanel:
            time.sleep(0.05)
            self._execute(self._ledpanel.disconnect())
            time.sleep(0.05)

        if self._microblocks_client:
            self._microblocks_client.disconnect()

        with self.__lock:
            self.__event_loop.call_soon_threadsafe(self.__event_loop.stop)
            self.__thread.join()
        self.__event_loop.close()
        # print("disconnected!")

    def load(self, filename):
        """加载图像，像素比例自动缩放到 16x16"""
        img = Image.open(filename)
        self._img = img.convert("RGB").resize((16, 16), Image.NEAREST)
        return True

    def save(self, name=None, img=None, resize=True):
        """保存图像"""
        if not name:
            name = self._generate_name()
        if not img:
            img = self._img
        # path = str(codelab_adapter_dir / "notebooks" / name) + ".png"
        path = f"{name}.png"
        # print(path)
        if resize:
            img = self._resize_to_save(img)
        img.save(path, format="png")
        # print(path)
        return path
        # 保存在 notebook 里

    def set_pixel(self, x, y, color, show=True):
        """设置 x, y 位置的颜色

        eg: set_pixel(0, 1, 'red')

        coordinate: https://learn.adafruit.com/adafruit-gfx-graphics-library/coordinate-system-and-units
        """
        # https://microbit-micropython.readthedocs.io/en/v1.0.1/display.html#microbit.display.set_pixel
        if type(color) == str:
            color = self._COLOR[color]

        if self._use_imagicharm_coordinate_system:
            # 与 imagicharm 保持一致, x 行 y 列
            y, x = x, y  # x y 与笛卡尔坐标系相反

        self._img.putpixel((x, y), color)

        if self._is_local():
            if show:
                self.show_here(self._img)

        if self._microblocks_client:
            if show:
                r, g, b = color
                self._microblocks_client.draw_point(r, g, b, x, y)

        if self._ledpanel:
            # to pack
            if show:
                r, g, b = color
                self._execute(self._ledpanel.draw_point(r, g, b, x, y))
                # self._show_image(img, PILimage=PILimage)

    def get_pixel(self, x, y):
        """获取 x, y 位置的颜色

        eg: get_pixel(0, 1)"""
        if self._use_imagicharm_coordinate_system:
            y, x = x, y
        return self._img.getpixel((x, y))

    def set_color(self, color):
        """设置背景颜色"""
        if type(color) == str:
            color = self._COLOR[color]

        for i in range(self.size):
            for j in range(self.size):
                self._img.putpixel((i, j), color)

        if self._is_local():
            self.show_here(self._img)

        if self._ledpanel:
            # to pack
            r, g, b = color
            self._execute(self._ledpanel.set_background(r, g, b))
            # self._show_image(img, PILimage=PILimage)
        if self._microblocks_client:
            self._microblocks_client.set_background(color)

    def display_char_zh(self, character, color=RED, font="simhei", offset_y=0):
        """显示中文字符"""
        # macos PingFang
        assert len(character) == 1
        if type(color) == str:
            color = self._COLOR[color]
        self._img = Image.new(mode="RGB", size=(self.size, self.size))
        # im = Image.new(mode="RGB", size=(self.size, self.size))
        draw = ImageDraw.Draw(self._img)

        if platform.system() == "Darwin" and font == "simhei":
            font = "PingFang"

        if font == "PingFang":
            if not offset_y:
                offset_y = -3

        image_font = ImageFont.truetype(font, self.size)
        draw.text((0, offset_y), character, font=image_font, fill=color)

        self.show(self._img)

    def display_text_zh(self, text, duration=1, **kw):
        """显示中文字符串"""
        for char in text:
            self.display_char_zh(char, **kw)
            time.sleep(duration)
        self.display_char_zh(" ", **kw)

    # def displayText(self, text, color1=(230, 0, 0), color2=(0, 250, 250), icon=None):
    def display_text(
        self, text, color=RED, color1=(0, 0, 0), color2=(0, 0, 0), icon=None
    ):
        """滚动显示英文字符串
        BLE 速度很慢，暂时弃用这种特效
        todo 只传内容，不传图片
        """
        if type(color) == str:
            color = self._COLOR[color]

        if self._microblocks_client:
            return self._microblocks_client.scroll_text(text, color)

        delta = 0
        if icon:
            delta = 25
        xsize = ImageFont.load_default().getsize(text)[0] + 32 + delta
        im = Image.new(mode="RGB", size=(xsize, self.size))
        for i in range(16):
            current_color = (
                int(color1[0] + ((color2[0] - color1[0]) / 16 * i)),
                int(color1[1] + ((color2[1] - color1[1]) / 16 * i)),
                int(color1[2] + ((color2[2] - color1[2]) / 16 * i)),
            )
            shape = [(0, i), (xsize, i)]
            img1 = ImageDraw.Draw(im)
            img1.line(shape, fill=current_color, width=0)
        if icon:
            iconIm = Image.open(icon).convert("RGB")
            im.paste(iconIm, (16, 0))
        imDraw = ImageDraw.Draw(im)
        imDraw.text((16 + delta, 4), text, (30, 30, 30))  # fill=color
        imDraw.text((16 + delta, 3), text, (210, 200, 191))  # fill=color
        for i in range(xsize - 15):
            crop_rectangle = (i, 0, i + 16, 16)  # 16x16 视野
            cropped_im = im.crop(crop_rectangle)
            self.show(cropped_im, True)
            # for j in range(400000):
            #    a = 0

    # display_char

    def display_emoji(self, character, color=RED, font="emoji", offset_y=0):
        """显示 emoji 表情符"""
        # assert len(character) == 1

        if type(color) == str:
            color = self._COLOR[color]
        self._img = Image.new(mode="RGB", size=(self.size, self.size))
        # im = Image.new(mode="RGB", size=(self.size, self.size))
        draw = ImageDraw.Draw(self._img)

        if font.lower() == "emoji":
            if color == RED:
                color = "white"
            if not offset_y:
                offset_y = 2

            src_path = os.path.join(base_path, "src")
            font_path = os.path.join(src_path, "seguiemj.ttf")
            image_font = ImageFont.truetype(
                font_path, self.size, layout_engine=ImageFont.LAYOUT_RAQM
            )
            draw.text(
                (0, offset_y),
                character,
                font=image_font,
                fill=color,
                embedded_color=True,
            )
        if "symbola" in font.lower():
            # https://github.com/python-pillow/Pillow/pull/4955
            if not offset_y:
                offset_y = -2
            image_font = ImageFont.truetype(font, self.size)
            draw.text((0, offset_y), character, font=image_font, fill=color)

        self.show(self._img)

    def show_here(self, img=None, PILimage=True):
        """显示图像"""
        if not img:
            img = self._img
        if self._is_local():
            return self._show_here(img, PILimage=PILimage)

    def show(self, img=None, PILimage=True):
        """显示图像"""
        if not img:
            img = self._img
        if self._is_local():
            return self._show_here(img, PILimage=PILimage)
        else:
            # to pack
            self._show_image(img, PILimage=PILimage)

    def clear(self):
        self._img = Image.new(mode="RGB", size=(self.size, self.size))
        if self._is_local():
            return self.show()

        if self._microblocks_client:
            self._microblocks_client.clear()

        if self._ledpanel:
            self._execute(self._ledpanel.clear())

    # def set_brightness(self, brightness):
    #     self._execute(self._ledpanel.set_brightness(brightness))

    @only_device
    def set_mode(self, name):
        """设置模式/特效 (仅在硬件上运行, 不支持模拟器)
        eg: fire, rainbow, snow, matrix, fireflies, arrows, noise_ocean, balls...
        """
        self._execute(self._ledpanel.set_effect_mode(name))

    def screen_on(self):
        """打开屏幕 (仅在硬件上运行, 不支持模拟器)"""
        self._execute(self._ledpanel.on())

    def screen_off(self):
        """关闭屏幕 (仅在硬件上运行, 不支持模拟器)"""
        self._execute(self._ledpanel.off())

    def set_brightness(self, brightness):
        """设置屏幕亮度"""
        self._execute(self._ledpanel.set_brightness(brightness))

    def upload_and_show_image(self, pilimage):
        """上传并显示图像"""
        self._execute(self._ledpanel.upload_and_show_image(pilimage))

    def set_effect_mode(self, mode):
        """设置效果切换模式
        eg：nextMode:下一个特效、prevMode:上一个特效、auto：自动切换
        """
        self._execute(self._ledpanel.set_effect_change_mode(mode))

    def get_images_list(self):
        """获取储存在板子中的图像列表"""
        self._execute(self._ledpanel.list_images_names())

    def show_function_icon(self, icon):
        """显示功能图标
        eg：(范围：0-18)
        """
        self._execute(self._ledpanel.function_icon(icon))

    def save_image(self, name):
        """保存当前显示在点阵屏上的图像"""
        self._execute(self._ledpanel.save_current_images(name))

    def delete_image(self, name):
        """删除存在板子中的图像"""
        self._execute(self._ledpanel.delete_images(name))

    def display_image(self, name):
        """显示存在板子中的图像"""
        self._execute(self._ledpanel.display_images(name))

    def image_rename(self, oldname, newname):
        """修改存在板子中的图像名称"""
        self._execute(self._ledpanel.image_rename(oldname, newname))

    def delete_all_images(self):
        """删除所有保存在板子上的图像"""
        self._execute(self._ledpanel.delete_all_images())

    def implicitly_get_image_data(self, name):
        """隐式获取上传的图片数据"""
        self._execute(self._ledpanel.implicitly_get_image_data(name))

    def display_Implicitly_image(self):
        """显示隐式获取到的图片（在缓存中）"""
        self._execute(self._ledpanel.display_Implicitly_image())

    def firmware_ver(self):
        """获取当前的版本信息"""
        self._execute(self._ledpanel.firmware_ver())

    def get_led_image_data(self):
        """获取当前显示在点阵屏上的颜色数据"""
        self._execute(self._ledpanel.led_image_data())

    def run_text_on_effects(self, text):
        """将文本显示在特效模式上"""
        self._execute(self._ledpanel.run_text_on_effects(text))

    def scroll_text(self, text):
        """显示滚动文本"""
        self._execute(self._ledpanel.scroll_text(text))

    def text_colormode(self, mode):
        """设置颜色模式
        eg：0 white font    1 gradient font    2 multicolor font
        """
        self._execute(self._ledpanel.text_colormode(mode))

    def text_color(self, color):
        """设置字体颜色"""
        self._execute(self._ledpanel.text_color(color))

    def crawl_speed(self, speed):
        """设置文本滚动速度"""
        self._execute(self._ledpanel.crawl_speed(speed))

    def play_text_once(self, text):
        """显示滚动一次的文本"""
        self._execute(self._ledpanel.play_text_once(text))

    def game_mode(self, mode):
        """选择游戏模式
        eg：选择游戏 - (1:迷宫，2：贪吃蛇，3：俄罗斯方块，4：打砖块)
            游戏操作 - (10：向上移动，11:向右移动，12：向下移动，13：向左移动，14：OK键)
        """
        self._execute(self._ledpanel.game_mode(mode))

    def game_paused(self):
        """暂停游戏"""
        self._execute(self._ledpanel.game_paused())

    def continue_game(self):
        """开始/继续游戏"""
        self._execute(self._ledpanel.continue_game())

    def set_game_speed(self, speed):
        """设置游戏速度"""
        self._execute(self._ledpanel.set_speed(speed))

    def get_flash_size(self):
        """获取板子的内存情况
        eg：显示总内存容量和已使用的容量
        """
        self._execute(self._ledpanel.flash_size())

    def get_folder_directory(self, name):
        """获取文件夹下的所有文件名"""
        self._execute(self._ledpanel.folder_directory(name))

    def get_dirname(self, name):
        """获取文件夹中文件夹的名字"""
        self._execute(self._ledpanel.dirname(name))

    def delete_dir(self, name):
        """删除文件夹（文件夹必须为空才可删除）"""
        self._execute(self._ledpanel.delete_dir(name))

    def recovery_mode(self):
        """恢复断电前的上一次效果或动图或图片"""
        self._execute(self._ledpanel.recovery_mode())

    def set_boot_mode(self, mode, name):
        """
        设置开机模式
        1、图片模式 (例：$6 35|1 图像文件名)
        2、动图模式（例：$6 35|2 动图文件名）
        3、指定特效模式（此设置需要在选定好的特效下发送指令，即可设置当前显示的特效为开机画面 例：$6 35|3）
        4、随机特效模式（例：$6 35|4）
        """
        self._execute(self._ledpanel.set_boot_mode(mode, name))

    def recovery_mode(self):
        """恢复断电前的模式"""
        self._execute(self._ledpanel.recovery_mode())

    def get_blemtu(self):
        """获取当前蓝牙的MTU大小"""
        self._execute(self._ledpanel.get_mtu_value())

    def get_blemac(self):
        """获取书包的BLE地址"""
        self._execute(self._ledpanel.get_ble_mac())

    def _update_animation(self, name, frames):
        """上传并保存动图"""
        self._execute(self._ledpanel.upload_animation(name, frames))

    def _display_gif(self, speed, name):
        """播放存在板子中的动图"""
        self._execute(self._ledpanel.display_gif(speed, name))

    def _get_gif_list(self):
        """获取存储在板子中的动图列表"""
        self._execute(self._ledpanel.dirname("16p16GIF"))

    def _delete_gif(self, name):
        """删除存储在板子中的动图"""
        self._execute(self._ledpanel.delete_gif(name))

    def _rename_gif(self, oldname, newname):
        """重命名存储在板子中的动图名称"""
        self._execute(self._ledpanel.renameGIF(oldname, newname))

    def close(self):
        self.disconnect()


LedBag = DotPack
DotPack.set_background = DotPack.set_color


class Animation:
    """
    a = Animation()
    make_unicorn(pack)
    a.add_frame(pack)
    make_heart(pack)
    a.add_frame(pack)
    a.show()  # a.show(to_pack=pack)
    """

    def __init__(self) -> None:
        self.frames = []  # 每个都是 PIL 图片
        self._pack = DotPack()

    def add_frame(self, pack_instance, frame_name=None):
        if not frame_name:
            frame_name = self._pack._generate_name()
        self.frames.append((frame_name, pack_instance._img.copy()))  # 不然引用同个对象

    def show(
        self,
        to_pack=None,
        filename="animation",
        optimize=False,
        duration=0.1,
        loop=0,
        **kwargs,
    ):
        # duration
        if to_pack:
            _frames = [frame for _, frame in self.frames]
            # todo show gif
            gif_filename = f"{filename}.gif"
            _frames[0].save(
                gif_filename,
                save_all=True,
                append_images=_frames[1:],
                optimize=optimize,
                duration=duration * 1000,
                loop=loop,
            )

            if to_pack._ledpanel:
                to_pack._update_animation(filename, self.frames)
                to_pack._display_gif(1, filename)

            if to_pack._microblocks_client:
                if loop == 0:
                    loop = True
                else:
                    loop = False

                to_pack._microblocks_client.upload_animation(filename, _frames)
                to_pack._microblocks_client.display_animation(
                    filename, pausing=duration, loop=loop
                )
        else:
            for name, frame in self.frames:
                self._pack.show(frame, PILimage=True)
                time.sleep(duration)

    def show_frame(self, frame_name, to_pack=None):
        for name, frame in self.frames:
            print(name)
            if frame_name == name:
                if to_pack:
                    to_pack.show(frame, PILimage=True)
                    # raise NotImplementedError
                else:
                    self._pack.show(frame, PILimage=True)
                return

    def remove_frame(self, frame_name):
        for name, frame in self.frames.copy():
            if frame_name == name:
                self.frames.remove((name, frame))
                return

    def save(
        self, name=None, resize=True, optimize=False, duration=1, loop=0, **kwargs
    ):
        if not name:
            name = self._pack._generate_name()
        if resize:
            _frames = [self._pack._resize_to_save(frame) for _, frame in self.frames]
        else:
            _frames = [frame for _, frame in self.frames]
        _frames[0].save(
            f"{name}.gif",
            save_all=True,
            append_images=_frames[1:],
            optimize=optimize,
            duration=duration * 1000,
            loop=loop,
        )

    def load(self, gif_image):
        """load gif"""
        im = Image.open(gif_image)
        self.frames = self._resize_gif(im)

    def _resize_gif(self, im):
        frames = [
            (
                self._pack._generate_name(),
                frame.copy()
                .resize((self._pack.size, self._pack.size), Image.NEAREST)
                .convert("RGB"),
            )
            for frame in ImageSequence.Iterator(im)
        ]
        return frames

    def clear(self):
        self.frames = []

    def show_animation(self, speed, name, to_pack=None):
        to_pack._display_gif(speed, name)

    def get_animation_list(self, to_pack=None):
        to_pack._get_gif_list()

    def delete_animation(self, file_name=None, to_pack=None):
        to_pack._delete_gif(file_name)

    def rename_animation(self, oldname, newname, to_pack=None):
        to_pack._rename_gif(oldname, newname)


pack = DotPack()
connect = pack.connect
set_pixel = pack.set_pixel
show = pack.show
set_background = set_color = pack.set_background
clear = pack.clear
close = pack.close
save = pack.save
load = pack.load
display_emoji = pack.display_emoji

__all__ = [
    "DotPack",
    "LedBag",
    "Animation",
    "pack",
    "connect",
    "set_pixel",
    "show",
    "set_color",
    "set_background",
    "clear",
    "close",
    "save",
    "load",
    "display_emoji",
]
