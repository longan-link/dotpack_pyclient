import time
import io
from PIL import Image
from websocket import create_connection
from tqdm import tqdm


class MicroblocksClient:
    def __init__(self, address=None, verbose=False):
        self._verbose = verbose # verbose: Print various debugging information
        self._startup_filename = 'startup.conf'
        self.address = address

    def __anext__(self):
        self.disconnect()
    
    def _color2val(self, rgb_color):
        r, g, b = rgb_color
        return (r << 16 | g << 8 | b)

    '''
    def _image2intarray(self, pilimage):
        pixels = pilimage.load()

        vals = []
        for i in range(pilimage.size[0]):
            for j in range(pilimage.size[1]):
                # if i == j:
                    r,g,b = pixels[i,j]
                    val = r << 16 | g << 8 | b
                    vals.append(str(val))
        return vals
    '''

    '''
    def _upload_image_text(self, pilimage):
        #save image to fs
        #Text Protocol
        #    4 fragment
        #    add,{1-4},intarray
        intarray = self._image2intarray(pilimage)
        
        for i in [0,1,2,3]:
            self.client.send(f'setImage,{i+1},' + ','.join(intarray[64*i:64*(i+1)]))
            rep = self.client.recv()
        return True
    '''
    
    def _send(self, cmd):
        '''
        verbose: Print various debugging information (linux cli style
        '''
        self.client.send(cmd)
        rep = self.client.recv()
        if self._verbose:
            print(rep)
        return rep
    
    def _send_binary(self, data):
        self.client.send_binary(data)
        rep = self.client.recv()
        if self._verbose:
            print(rep)
        return rep
    
    def _upload_text_file(self, filename, data):
        '''
        uploadTextFile,{filename},{data}
        '''
        cmd = f'uploadTextFile,{filename},{data}'
        return self._send(cmd)

    def _setFileMeta(self,filename):
        '''
        setFileMeta,{filename}
            setFileMeta image.bmp
        '''
        cmd = f'setFileMeta,{filename}'
        self._send(cmd)

    def connect(self, address=None):
        if address:
            self.address = address
        self.client = create_connection(f"ws://{self.address}:81")

    def disconnect(self):
        self.client.close()
    
    def clear(self):
        cmd = 'clear'
        return self._send(cmd)

    def draw_point(self, colorR, colorG, colorB, pointx, pointy):
        cmd = f'setPixel,{colorR},{colorG},{colorB},{pointx},{pointy}'
        return self._send(cmd)

    def set_brightness(self, num):
        cmd = f'setBrightness,{num}'
        return self._send(cmd)
    

    def set_background(self, color):
        cmd = f'setBackground,{self._color2val(color)}'
        return self._send(cmd)
    
    def display_char(self, char, color=(255, 0, 0)):
        char = str(char).strip()[0]
        cmd = f'displayChar,{char},{self._color2val(color)}'
        return self._send(cmd)

    def scroll_text(self, text, color, pausing=100):
        cmd = f'scrollText,{text},{self._color2val(color)},{pausing}'
        return self._send(cmd)
    

    def display_image(self, filename, startup):
        '''
        Text Protocol
            displayBMPImage,{filename},{startup}
        '''
        cmd = f'displayBMPImage,{filename},{startup}'
        return self._send(cmd)

    def _upload_image(self, pilimage, filename):

        self._setFileMeta(filename)
            
        output = io.BytesIO()
        pilimage.save(output, format='bmp')

        output.seek(0)
        img_bytearray = bytearray(output.read())
        
        return self._send_binary(img_bytearray)

    def upload_and_show_image(self, pilimage, filename="image.bmp", startup=True):
        self._upload_image(pilimage, filename)
        return self.display_image(filename,startup)

    def list_file_names(self, dirname="root"):
        '''
        return 
            file names list
        
        Text Protocol
            listFileNames,{dirname}
        '''
        cmd = f'listFileNames,{dirname}'
        file_names = self._send(cmd)
        return file_names.strip().split(',') 

    def delete_file(self, filename):
        ''' 
        deleteFile,{filename}
            deleteFile image.bmp
        '''
        cmd = f'deleteFile,{filename}'
        return self._send(cmd)

    def delete_all_images(self):
        files = self.list_file_names()
        for i in files:
            if  ".bmp" in i.lower():
                self.delete_file(i)
        return True

    def _clean_animation(self, name):
        cmd = f'cleanAnimation,{name}'
        return self._send(cmd)

    def upload_animation(self, name, frames, duration=0.1):
        '''
        实现
            不使用gif, 使用动态图片
    
        使用命名规则    animation-0.bmp,animation-1.bmp,animation-2.bmp
        '''

        # 要求服务端清理
        self._clean_animation(name)

        for index, img in enumerate(tqdm(frames)):
            # pack._microblocks_client.delete_file(filename=f"SnowCrash-{index}.bmp")
            self._upload_image(img, filename=f"{name}-{index}.bmp")

        return True
    
    def display_animation(self, name="animation", pausing=100, loop=False, startup=True):
        '''
        Text Protocol
            displayAnimation,{name},{pausing},{loop}
            播放到最后一张
        '''
        cmd = f'displayAnimation,{name},{pausing},{loop},{startup}'
        return self._send(cmd)

    def remove_startup(self):
        self.delete_file(self._startup_filename)
