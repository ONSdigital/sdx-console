from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

import base64
import os
from console import settings
import jwt
import hashlib
import logging


logger = logging.getLogger(__name__)


class Encrypter (object):
    def __init__(self):
        private_key_bytes = self._to_bytes(settings.EQ_PRIVATE_KEY)
        self.private_key = serialization.load_pem_private_key(private_key_bytes,
                                                              password=None,
                                                              backend=backend)
        eq_public_key_bytes = self.private_key.public_key().public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )

        self.signing_kid = Encrypter._generate_kid_from_key(eq_public_key_bytes)
        logger.info("Signing KID is {}".format(self.signing_kid))

        private_decryption_key = serialization.load_pem_private_key(
            settings.PRIVATE_KEY.encode(),
            password=None,
            backend=backend
        )

        public_key_bytes = private_decryption_key.public_key().public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )

        self.encryption_kid = Encrypter._generate_kid_from_key(public_key_bytes)
        logger.info("Encryption KID is {}".format(self.encryption_kid))

        self.public_key = serialization.load_pem_public_key(public_key_bytes, backend=backend)

        # first generate a random key
        self.cek = os.urandom(32)  # 256 bit random CEK

        # now generate a random IV
        self.iv = os.urandom(12)  # 96 bit random IV

    @staticmethod
    def _generate_kid_from_key(public_key):
        hash_object = hashlib.sha1(public_key)
        kid = hash_object.hexdigest()
        return kid

    def _to_bytes(self, bytes_or_str):
        if isinstance(bytes_or_str, str):
            value = bytes_or_str.encode()
        else:
            value = bytes_or_str
        return value

    def _jwe_protected_header(self):
        return self._base_64_encode(bytes('{"alg":"RSA-OAEP","enc":"A256GCM","kid":"' + self.encryption_kid + '"}', 'utf-8'))

    def _encrypted_key(self, cek):
        ciphertext = self.public_key.encrypt(cek, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA1(), label=None))
        return self._base_64_encode(ciphertext)

    def _encode_iv(self, iv):
        return self._base_64_encode(iv)

    def _base_64_encode(self, text):
        # strip the trailing = as they are padding to make the result a multiple of 4
        # the RFC does the same, as do other base64 libraries so this is a safe operation
        return base64.urlsafe_b64encode(text).decode().strip("=").encode()

    def _encode_and_signed(self, payload):
        return jwt.encode(payload, self.private_key, algorithm="RS256", headers={'kid': self.signing_kid, 'typ': 'jwt'})

    def encrypt(self, json):
        payload = self._encode_and_signed(json)
        jwe_protected_header = self._jwe_protected_header()
        encrypted_key = self._encrypted_key(self.cek)

        cipher = Cipher(algorithms.AES(self.cek), modes.GCM(self.iv), backend=backend)
        encryptor = cipher.encryptor()

        encryptor.authenticate_additional_data(jwe_protected_header)

        ciphertext = encryptor.update(payload) + encryptor.finalize()

        tag = encryptor.tag

        encoded_ciphertext = self._base_64_encode(ciphertext)
        encoded_tag = self._base_64_encode(tag)

        # assemble result
        jwe = jwe_protected_header + b"." + encrypted_key + b"." + self._encode_iv(self.iv) + b"." + encoded_ciphertext + b"." + encoded_tag

        return jwe