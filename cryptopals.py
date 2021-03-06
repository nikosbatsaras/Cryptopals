from Crypto.Cipher import AES
from random    import choice
from binascii  import hexlify, unhexlify
from base64    import b64encode, b64decode
from string    import ascii_letters, punctuation, digits, whitespace, printable


def HexToAscii(s):
    """Convert hex string to ascii string.

        Args:
            s (str): Hex string to convert.

        Returns:
            Ascii string.
    """
    return bytes.fromhex(s).decode("ascii")


def AsciiToHex(s):
    """Convert ascii string to hex string.

        Args:
            s (str): Ascii string to convert.

        Returns:
            Hex string.
    """
    hexstring = ""
    for c in s:
        r = format(ord(c), 'x')

        if len(r) == 1:
            hexstring += '0' + r
        else:
            hexstring += r

    return hexstring


def HexToBase64(s):
    """Convert hex string to base64 string.

        Args:
            s (str): Hex string to convert.

        Returns:
            Base64 string.
    """
    return b64encode(unhexlify(s)).decode("ascii")


def Base64ToHex(s):
    """Convert base64 string to hex string.

        Args:
            s (str): Base64 string to convert.

        Returns:
            Hex string.
    """
    return hexlify(b64decode(s)).decode("ascii")


def HexXOR(s1, s2):
    """XOR two equal-sized hex strings.

        Args:
            s1 (str): Hex string.
            s2 (str): Hex string.

        Returns:
            Hex string, result of 's1 XOR s2'.
    """
    xor = int(s1, 16) ^ int(s2, 16)
    xor = format(xor, 'x')

    if len(xor) == 1 or len(xor) % 2 != 0:
        return '0' + xor

    return xor


def IsPlaintext(text, factor=0.95):
    """Check if text contains 'mostly' alpharithmetics.

        Args:
            text (str):     Ascii string to check.
            factor (float): Percentage of alphas in text in order qualify
                            as plaintext.

        Returns:
            true, if number of alphas is above given percentage
            false, otherwise.
    """
    text = text.strip().replace(' ', '')

    counter = 0
    for c in text:
        if c.isalpha():
            counter += 1

    return counter > factor * len(text)


def RepeatingXOR(plaintext, key):
    """XOR each byte of plaintext with a single byte of key.
        When XOR'd with the last byte of key, reset key index.

        Args:
            plaintext (str): Text to encrypt.
            key (str):       Key used for encryption.

        Returns:
            Hex string, ciphertext.
    """
    index = 0
    ciphertext = ""
    for c in plaintext:
        hexchar1 = format(ord(c), 'x')
        hexchar2 = format(ord(key[index]), 'x')

        ciphertext += HexXOR(hexchar1, hexchar2)

        index += 1
        if index == len(key):
            index = 0

    return ciphertext


def PKCS7(text, blocksize=16):
    """Pad text to blocksize according to PKCS#7.

        Args:
            text (str):      Text to pad.
            blocksize (int): Blocksize.

        Returns:
            Text padded to blocksize.
    """
    if len(text) % blocksize == 0:
        return text

    return text + (blocksize - len(text) % blocksize) * '\x04'


def PKCS7Validate(plaintext):
    """Validate PKCS#7 padding.
    Check both if length is a multiple of 8 and if padding consists of the
    character \x04.

        Args:
            plaintext (str): Text to validate.

        Returns:
            Plaintext without the padding or an exception if padding is
            invalid.
    """
    if len(plaintext) % 8 != 0:
        raise Exception("Invalid PKCS7 padding")

    plaintext = list(plaintext)
    for i in range(len(plaintext)):
        if plaintext[i] not in printable:
            if plaintext[i] == '\x04':
                plaintext[i] = ""
            else:
                raise Exception("Invalid PKCS7 padding")
    return "".join(plaintext)


def EncryptCBC(plaintext, key, blocksize, iv):
    """Encrypt plaintext using AES in CBC mode.

        Args:
            plaintext (str): Text to encrypt.
            key (binary):    Key used in encyption.
            blocksize (int): Size of blocks.
            iv (hex str):    Initialization vector.

        Returns:
            Ciphertext.
    """
    cipher = AES.new(key, AES.MODE_ECB)

    plaintext = PKCS7(plaintext)

    plaintext = AsciiToHex(plaintext)
    iv        = AsciiToHex(iv)

    xor = HexXOR(plaintext[0*blocksize:2*blocksize], iv)
    xor = unhexlify(xor)

    cipherblock = cipher.encrypt(xor)
    cipherblock = hexlify(cipherblock).decode("ascii")

    ciphertext = cipherblock

    for index in range(2*blocksize, len(plaintext), 2*blocksize):
        xor = HexXOR(plaintext[index:index+2*blocksize], cipherblock)
        xor = unhexlify(xor)

        while len(xor) % 16 != 0:
            xor = b'\x00' + xor

        cipherblock = cipher.encrypt(xor)
        cipherblock = hexlify(cipherblock).decode("ascii")

        ciphertext += cipherblock

    return ciphertext


def DecryptCBC(ciphertext, key, blocksize, iv):
    """Decrypt plaintext using AES in CBC mode.

        Args:
            plaintext (str): Text to decrypt.
            key (binary):    Key used in decyption.
            blocksize (int): Size of blocks.
            iv (hex str):    Initialization vector.

        Returns:
            Plaintext.
    """
    cipher = AES.new(key, AES.MODE_ECB)

    iv = AsciiToHex(iv)

    cipherblock = unhexlify(ciphertext[0*blocksize:2*blocksize])

    plainblock = cipher.decrypt(cipherblock)
    plainblock = hexlify(plainblock).decode("ascii")

    xor = HexXOR(plainblock, iv)

    plaintext = HexToAscii(xor)

    for index in range(2*blocksize, len(ciphertext), 2*blocksize):
        cipherblock = unhexlify(ciphertext[index:index+2*blocksize])

        plainblock = cipher.decrypt(cipherblock)
        plainblock = hexlify(plainblock).decode("ascii")

        xor = HexXOR(plainblock, ciphertext[index-2*blocksize:index])

        plaintext += HexToAscii(xor)

    return plaintext.replace('\x04', '')


def RandomString(length):
    """Return a random string of size 'length'.

        Args:
            length (int): The number of characters.

        Returns:
            Ascii string.
    """
    dictionary = ascii_letters + punctuation + digits + whitespace
    randstr = "".join(choice(dictionary) for x in range(length))

    return randstr
