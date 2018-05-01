class rot():
    """
    Rot cipher has the following properties:

    Attributes:
        abet: a string representing the alphabet
        out: the output of the encryption/decryption
    """
    def __init__(self):
        """
        Returns an object of rot
        """
        self.abet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.out = ""

    async def encrypt(self, txt, num):
        """
        Returns the encrypted text *txt* using key *num*
        """
        for i in txt:
            # Ignore non alphabet chars
            if i.isalpha() is False:
                self.out += i
            else:
                # Apply the caesar shift
                shift = self.abet.index(i.upper()) + num
                # Bring shift value back into range of alphabet
                while shift > 25:
                    shift -= 26
                # Accounts for a negative shift being provided
                while shift < 0:
                    shift += 26
                # Add new char to the output
                self.out += self.abet[shift]
        return(self.out)

    async def decrypt(self, txt, num):
        """
        Returns the decrypted text *txt* using key *num*
        """
        for i in txt:
            # Ignore non alphabet chars
            if i.isalpha() is False:
                self.out += i
            else:
                # Apply the caesar shift in reverse
                shift = self.abet.index(i.upper()) - num
                # Bring shift value back into range of alphabet
                while shift < 0:
                    shift += 26
                # Accounts for a negative shift being provided
                while shift > 25:
                    shift -= 26
                # Add new char to the output
                self.out += self.abet[shift]
        return(self.out)


class vigenere():
    """
    Vigenere cipher uses the equation from the Wikipedia entry.
    Vigenere cipher has the following properties:

    Attributes:
        abet: a string representing the alphabet
    """
    def __init__(self):
        """
        Returns an object of vigenere
        """
        self.abet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    async def encrypt(self, txt, key):
        """
        Returns the encrypted text *txt* with key *key*
        """
        key = key * (int(len(txt) / len(key))) \
            + key[:len(txt) % len(key)]  # Make key match the length of txt
        # Match spaces up on the key:
        key = list(key)
        for i in range(len(txt)):
            if txt[i].isalpha() is False:
                key.insert(i, " ")
        key = "".join(key)
        # End matching
        out = ""
        for i in range(len(txt)):
            # We want to ignore any non alphabet characters
            if txt[i].isalpha():
                val = self.abet.index(txt[i].upper()) \
                    + self.abet.index(key[i].upper())  # Mi + Ki = Ek
                while val > 25:
                    # Return to range of alphabet
                    val -= 26
                out += self.abet[val]
            else:
                out += txt[i]
        return(out)

    async def decrypt(self, txt, key):
        """
        Returns the decrypted text *txt* with key *key*
        """
        key = key * (int(len(txt) / len(key))) \
            + key[:len(txt) % len(key)]  # Make key match the length of txt
        # Match spaces up on the key:
        key = list(key)
        for i in range(len(txt)):
            if txt[i].isalpha() is False:
                key.insert(i, " ")
        key = "".join(key)
        # End matching
        out = ""
        for i in range(len(txt)):
            # Ignore any non alphabet characters
            if txt[i].isalpha():
                val = self.abet.index(txt[i].upper()) \
                    - self.abet.index(key[i].upper())  # Mi - Ki = Dk
                while val < 0:
                    # Return to range of alphabet
                    val += 26
                out += self.abet[val]
            else:
                out += txt[i]
        return(out)


class Railfence():
    """
    Railfence object to encryptd/decrypt with
    the railfence cipher. Has the following properties:
    
    Attributes:
        railfence: a list representing the railfence
    """
    def __init__(self):
        """
        Returns an object of Railfence
        """
        self.railfence = []
    async def encrypt(self, txt, key):
        """
        Returns a tuple which has the encrypted *txt* with key *key* in
        two forms:
            String: a string of the encrypted text, reading each row at a time
            String: a string of the encrypted text but with the whole fence
                    displayed.
        """
        # If railfence key is 1, txt is unchanged
        if key == 1:
            return(txt, None)
        # Build an empty railfence
        self.railfence = [['.' for c in range(len(txt))] for r in range(key)]
        r = 0
        down = True
        """
        Fills in the railfence using *down* to determine whetehr or not to
        be moving up or down as it travels across the width of the railfence
        """
        for c,char in enumerate(txt):
            self.railfence[r][c] = char
            r += 1 if down else -1
            if r == key-1:
                down = False
            elif r == 0:
                down = True
        return(self.__prettify(1))

    async def decrypt(self, txt, key):
        """
        Returns a tuple which has the decrypted *txt* with key *key* in
        two forms:
            String: a string of the decrypted text, reading each row at a time
            String: a string of the decrypted text but with the whole fence
                    displayed.
        """
        # *txt* is unchanged if key is 1
        if key == 1:
            return(txt, None)
        # Build an empty railfence
        self.railfence = [['.' for c in range(len(txt))] for r in range(key)]
        r = 0
        down = True
        # Cycle is how many spaces between the next char in that rail
        cycle = (key*2)-2
        basepos = 0
        for r in range(key):
            # Reset cycle at end of key
            if r == key-1:
                cycle = (key*2)-2
            pos = basepos
            count = 0
            for char in txt:
                self.railfence[r][pos] = char
                pos += cycle
                count += 1
                if pos >= len(self.railfence[r]):
                    break
            # Cycle reduced by two each time you go down a rail
            if r != key-1:
                cycle -= 2
            txt = txt[count:]
            print(txt)
            basepos += 1
        return(self.__prettify(0))

    async def __prettify(self, operation):
        """
        Private method that returns a tuple:
            String: a string that displays text, read a row at a time
            String: a string that contains the whole fence
        """
        output_table = ""
        output = ""
        if operation == 1:
            for row in self.railfence:
                for col in row:
                    if col != ".":
                        output += col
                        output_table += col
                    else:
                        output_table += "."
                output_table += "\n"
        else:
            for i in range(len(self.railfence[0])):
                for r in self.railfence:
                    pass
        return(output, output_table)


async def xor(mask, message, binaryout=True, binaryin=False):
    """
    Returns the result of an XOR operation
    on the message *message* with mask *mask*.
    By default, it outputs the result in binary,
    however it can output the unicode version by
    setting *binary* to True.
    """
    if binaryin:
        parts = message.split()
    else:
        # Splits each letter and converts into binary
        parts = [str(format(ord(i), 'b')) for i in message]
    # Stores result of XOR for each binary character
    result = [bin(int(i, 2) ^ int(mask, 2))[2:].zfill(8) for i in parts]
    if binaryout:
        # Output in binary
        output = " ".join(i for i in result)
    else:
        # Output in unicode
        output = " ".join(chr(int(i, 2)) for i in result)
    return(output)
