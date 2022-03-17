from PIL import Image
file = "/home/zhou/build/zhou/ledpanel/yellow.jpeg"
img = Image.open(file)
out = img.resize((16,16))
bufferall={}
bufferline=None
#print(out.getpixel((0,1))[2])
#img.show()
for y in range(16):
    bufferline=("$6 11|%d " %(y))
    for x in range(16):
        r,g,b=img.getpixel((x,y))
        #print("B: %x G: %x R: %x" %(out[y,x,0],out[y,x,1],out[y,x,2])) # B G R format
        if  b<16:
            bufferline=bufferline+"0"+("%x"%(b))
        else:
            bufferline=bufferline+("%x"%(b))
        if  g<0x10:
            bufferline=bufferline+"0"+("%x"%(g))
        else:
            bufferline=bufferline+("%x"%(g))
        if  r<0x10:
            bufferline=bufferline+"0"+("%x"%(r))
        else:
            bufferline=bufferline+("%x"%(r))
        if x==15:
            bufferline=bufferline+(" %d;" %(x))
        else:
            bufferline=bufferline+(" %d|" %(x))
    bufferall[y]=bufferline
    print(bufferall[y])
