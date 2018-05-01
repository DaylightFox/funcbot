from hashlib import md5

class steganography():
    def __init__(self):
        self.fin = False
    async def encrypt(self, image, message):
        # Store pixel info
        self.pixels = image.load()
        w, h = image.size
        self.msg = " ".join(message)
        self.c = 0
        self.i = 0
        for x in range(w):
            for y in range(h):
                r, g, b = self.pixels[x,y]
                if self.c != len(self.msg):
                    # Build binary version of message
                    self.charbin = format(ord(self.msg[self.c]), '08b')
                else:
                    # If c is the length of the msg (number of characters) then finish
                    return(image)
                # Edit each colour value of the pixel
                r = await self._set_bit(self.charbin[self.i],r)
                g = await self._set_bit(self.charbin[self.i],g)
                b = await self._set_bit(self.charbin[self.i],b)
                # If r/g/b are null, then finish
                if r is None or g is None or b is None:
                    return(image)
                else:
                    # Set the pixels
                    self.pixels[x,y] = r, g, b
    async def decrypt(self, image):
        self.pixels = image.load()
        w, h = image.size
        self.c = 0
        self.i = 0
        msgbin = ""
        msg = ""
        for x in range(w):
            for y in range(h):
                r, g, b = self.pixels[x,y]
                # Compile full binaryversion of message
                msgbin = msgbin + format(r, '08b')[7] + format(g, '08b')[7] + format(b, '08b')[7]
        # Split the binary version of the message every 8 characters (to form a byte each)
        msgbinlist = [msgbin[i:i+8] for i in range(0, len(msgbin), 8)]
        # Convert each byte into its respective character equivalent
        for letter in msgbinlist:
            msg = msg + chr(int(letter, base=2))
        return(msg)
    async def _set_bit(self,bit,colour):
        # Set or remove bit using bitwise operators.
        bit = int(bit)
        # If data bit is 1, then set, otherwise remove
        if bit == 1:
            colour = colour | 1
        else:
            colour = colour & 244
        await self._incrementer()
        if self.fin:
            # if self.fin is True, c is equal to the length and thus program must halt
            return None
        else:
            return(colour)
    async def _incrementer(self):
        # Increments i and c if i is 8
        self.i += 1
        if self.i == 8:
            self.i = 0
            self.c += 1
            # If c is still within the length of the message, continue, otherwise set finish to true
            if self.c != len(self.msg):
                self.charbin = format(ord(self.msg[self.c]), '08b')
            else:
                self.fin = True
