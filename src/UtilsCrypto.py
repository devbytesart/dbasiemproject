""" 
Copyright 2026 ttdantett DevBytesArt

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

author: ttdantett
title: siem project
document: UtilsCrypto
"""

import os
import traceback
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import constant_time
import secrets

class Encryption:
    def __init__(self, algorithm: str, key_path: str, iv_path: str):
        self.algorithm = algorithm.upper()
        self.key_path = key_path
        self.iv_path = iv_path

        if self.algorithm != "AES256":
            raise ValueError("Only AES256 algorithm is currently supported.")

        try:
            self.key = self._load_key()
            self.iv = self._load_iv()

            if len(self.key) != 32:
                raise ValueError("Key must be 32 bytes for AES-256.")

            if len(self.iv) != 16:
                raise ValueError("Initialization Vector (IV) must be 16 bytes.")
        except Exception as e:
            print("Error initializing encryption:")
            traceback.print_exc()
            raise e

    def _load_key(self) -> bytes:
        try:
            with open(self.key_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print("Error loading key:")
            traceback.print_exc()
            raise e

    def _load_iv(self) -> bytes:
        try:
            with open(self.iv_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print("Error loading IV:")
            traceback.print_exc()
            raise e

    @staticmethod
    def generate_key(file_path: str):
        try:
            key = secrets.token_bytes(32)  # 256-bit key
            with open(file_path, 'wb') as f:
                f.write(key)
            print(f"Key generated and saved to {file_path}")
        except Exception as e:
            print("Error generating key:")
            traceback.print_exc()
            raise e

    @staticmethod
    def generate_iv(file_path: str):
        try:
            iv = secrets.token_bytes(16)  # 128-bit IV
            with open(file_path, 'wb') as f:
                f.write(iv)
            print(f"IV generated and saved to {file_path}")
        except Exception as e:
            print("Error generating IV:")
            traceback.print_exc()
            raise e

    def encrypt_text(self, plaintext: str) -> bytes:
        try:
            # Add padding to plaintext
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(plaintext.encode()) + padder.finalize()

            # Create AES cipher and encrypt
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
            encryptor = cipher.encryptor()
            return encryptor.update(padded_data) + encryptor.finalize()
        except Exception as e:
            print("Error encrypting text:")
            traceback.print_exc()
            raise e

    def decrypt_text(self, ciphertext: bytes) -> str:
        try:
            # Create AES cipher and decrypt
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

            # Remove padding from plaintext
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(decrypted_padded) + unpadder.finalize()
            return plaintext.decode()
        except Exception as e:
            print("Error decrypting text:")
            traceback.print_exc()
            raise e

    def encrypt_file(self, input_path: str, output_path: str):
        try:
            # Read input file
            with open(input_path, 'rb') as f:
                data = f.read()

            # Add padding
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data) + padder.finalize()

            # Encrypt data
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted = encryptor.update(padded_data) + encryptor.finalize()

            # Write encrypted data to output file
            with open(output_path, 'wb') as f:
                f.write(encrypted)
        except Exception as e:
            print("Error encrypting file:")
            traceback.print_exc()
            raise e

    def decrypt_file(self, input_path: str, output_path: str):
        try:
            # Read encrypted file
            with open(input_path, 'rb') as f:
                encrypted = f.read()

            # Decrypt data
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()

            # Remove padding
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(decrypted_padded) + unpadder.finalize()

            # Write decrypted data to output file
            with open(output_path, 'wb') as f:
                f.write(data)
        except Exception as e:
            print("Error decrypting file:")
            traceback.print_exc()
            raise e
