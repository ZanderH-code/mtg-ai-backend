import base64
import json
import time
from typing import Any, Dict, Optional

class SimpleEncryption:
    """简化的对称加密工具"""
    
    # 简单的密钥 - 在实际部署中应该使用环境变量
    SECRET_KEY = "mtg-ai-secret-key-2024"
    
    @staticmethod
    def _xor_encrypt(data: str, key: str) -> str:
        """简单的XOR加密"""
        encrypted = ""
        key_length = len(key)
        for i, char in enumerate(data):
            key_char = key[i % key_length]
            encrypted += chr(ord(char) ^ ord(key_char))
        return encrypted
    
    @staticmethod
    def _xor_decrypt(encrypted_data: str, key: str) -> str:
        """简单的XOR解密"""
        return SimpleEncryption._xor_encrypt(encrypted_data, key)
    
    @staticmethod
    def encrypt(data: Any) -> str:
        """加密数据"""
        try:
            print(f"🔐 开始加密数据: {type(data)}")
            # 转换为JSON字符串
            json_str = json.dumps(data, ensure_ascii=False)
            print(f"📄 JSON字符串长度: {len(json_str)}")
            # XOR加密
            encrypted = SimpleEncryption._xor_encrypt(json_str, SimpleEncryption.SECRET_KEY)
            print(f"🔑 XOR加密完成，长度: {len(encrypted)}")
            # Base64编码
            result = base64.b64encode(encrypted.encode('utf-8')).decode('utf-8')
            print(f"✅ Base64编码完成，最终长度: {len(result)}")
            return result
        except Exception as e:
            print(f"❌ 加密失败: {type(e).__name__}: {e}")
            raise
    
    @staticmethod
    def decrypt(encrypted_data: str) -> Any:
        """解密数据"""
        try:
            print(f"🔓 开始解密数据，长度: {len(encrypted_data)}")
            # Base64解码
            decoded = base64.b64decode(encrypted_data.encode('utf-8')).decode('utf-8')
            print(f"📄 Base64解码完成，长度: {len(decoded)}")
            # XOR解密
            decrypted = SimpleEncryption._xor_decrypt(decoded, SimpleEncryption.SECRET_KEY)
            print(f"🔑 XOR解密完成，长度: {len(decrypted)}")
            # JSON解析
            result = json.loads(decrypted)
            print(f"✅ JSON解析完成，类型: {type(result)}")
            return result
        except Exception as e:
            print(f"❌ 解密失败: {type(e).__name__}: {e}")
            print(f"🔍 解密数据: {encrypted_data[:100]}...")
            raise
    
    @staticmethod
    def is_encrypted(data: Dict) -> bool:
        """检查数据是否已加密"""
        return isinstance(data, dict) and 'encrypted_data' in data
    
    @staticmethod
    def create_encrypted_payload(data: Any) -> Dict:
        """创建加密的请求载荷"""
        try:
            encrypted_data = SimpleEncryption.encrypt(data)
            return {
                'encrypted_data': encrypted_data,
                'timestamp': int(time.time() * 1000),
                'version': '1.0'
            }
        except Exception as e:
            print(f"创建加密载荷失败: {e}")
            # 如果加密失败，返回原始数据
            return data
