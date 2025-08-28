import json
import base64
from typing import Any, Dict, Optional
import time

class SimpleEncryption:
    """简单的对称加密工具 - 与前端对应"""
    
    KEY = 'mtg-ai-2024-secret-key-12345'  # 16字节密钥
    IV = 'mtg-ai-iv-2024'  # 16字节初始向量
    
    @staticmethod
    def string_to_bytes(s: str) -> bytes:
        """字符串转字节数组"""
        return s.encode('utf-8')
    
    @staticmethod
    def bytes_to_string(b: bytes) -> str:
        """字节数组转字符串"""
        return b.decode('utf-8')
    
    @staticmethod
    def xor_encrypt(data: str, key: str) -> str:
        """简单的XOR加密"""
        data_bytes = SimpleEncryption.string_to_bytes(data)
        key_bytes = SimpleEncryption.string_to_bytes(key)
        result = bytearray(len(data_bytes))
        
        for i in range(len(data_bytes)):
            result[i] = data_bytes[i] ^ key_bytes[i % len(key_bytes)]
        
        return base64.b64encode(bytes(result)).decode('utf-8')
    
    @staticmethod
    def xor_decrypt(encrypted_data: str, key: str) -> str:
        """简单的XOR解密"""
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        key_bytes = SimpleEncryption.string_to_bytes(key)
        result = bytearray(len(encrypted_bytes))
        
        for i in range(len(encrypted_bytes)):
            result[i] = encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)]
        
        return SimpleEncryption.bytes_to_string(bytes(result))
    
    @staticmethod
    def encrypt(data: Any) -> str:
        """加密数据"""
        json_string = json.dumps(data, ensure_ascii=False)
        return SimpleEncryption.xor_encrypt(json_string, SimpleEncryption.KEY)
    
    @staticmethod
    def decrypt(encrypted_data: str) -> Any:
        """解密数据"""
        decrypted_string = SimpleEncryption.xor_decrypt(encrypted_data, SimpleEncryption.KEY)
        return json.loads(decrypted_string)
    
    @staticmethod
    def generate_signature(data: Any, timestamp: int) -> str:
        """生成请求签名"""
        data_string = json.dumps(data, ensure_ascii=False) + str(timestamp)
        return SimpleEncryption.xor_encrypt(data_string, SimpleEncryption.KEY)[:16]
    
    @staticmethod
    def verify_signature(data: Any, timestamp: int, signature: str) -> bool:
        """验证请求签名"""
        try:
            expected_signature = SimpleEncryption.generate_signature(data, timestamp)[:16]
            return signature == expected_signature
        except Exception as e:
            print(f"签名验证错误: {e}")
            return False
    
    @staticmethod
    def verify_timestamp(timestamp: int, max_age: int = 300000) -> bool:
        """验证时间戳（防止重放攻击）"""
        try:
            current_time = int(time.time() * 1000)  # 毫秒时间戳
            time_diff = abs(current_time - timestamp)
            return time_diff < max_age  # 默认5分钟内有效
        except Exception as e:
            print(f"时间戳验证错误: {e}")
            return False
