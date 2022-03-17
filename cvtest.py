import numpy as np
import cv2 as cv
import sys
img = cv.imread('/home/zhou/build/zhou/ledpanel/OIP.jpeg')
if img is None:
    sys.exit("Could not read the image.")
#cv.imshow("Display window", img)
dim=(16,16)
out=cv.resize(img,dim,interpolation = cv.INTER_CUBIC)
print(out.shape)
#cv.imshow("Resized image",out)

#cv.waitKey(0)
#cv.destroyAllWindows()
bufferall={}
bufferline=None

for y in range(16):
    buffer=("$6 11|%d " %(y))
    for x in range(16):
        print("B: %x G: %x R: %x" %(out[y,x,0],out[y,x,1],out[y,x,2])) # B G R format
        if  out[y,x,2]<16:
            bufferline=bufferline+"0"+("%x"%(out[y,x,2]))
        else:
            bufferline=bufferline+("%x"%(out[y,x,2]))
        if  out[y,x,1]<0x10:
            bufferline=bufferline+"0"+("%x"%(out[y,x,1]))
        else:
            bufferline=bufferline+("%x"%(out[y,x,1]))
        if  out[y,x,0]<0x10:
            bufferline=bufferline+"0"+("%x"%(out[y,x,0]))
        else:
            bufferline=bufferline+("%x"%(out[y,x,0]))
        if x==15:
            bufferline=bufferline+(" %d|;" %(x))
        else:
            bufferline=bufferline+(" %d|" %(x))
    bufferall[y]=bufferline
    print(buffer)
    print("\n")
    print(bufferall[y])