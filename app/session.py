import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP


class Session:
    """Handles encryption/decryption for a session."""

    def __init__(self, public_key: bytes):
        self.public_key = public_key
        self.rsa = RSA.import_key(public_key)
        self.rsa_cipher = PKCS1_OAEP.new(self.rsa)
        self.aes_key = os.urandom(32)

    def get_encrypted_aes_key(self):
        return self.rsa_cipher.encrypt(self.aes_key)

    def encrypt(self, data: bytes) -> bytes:
        """Returns the encrypted data, with the 12 byte long nonce prepended to it."""
        nonce = os.urandom(12)
        aes_cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=nonce)
        return nonce + aes_cipher.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        """Returns the decrypted version of data as a bytes object. Data must have a 12 bytes nonce prepended before it."""
        aes_cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=data[:12])
        return aes_cipher.decrypt(data[12:])
