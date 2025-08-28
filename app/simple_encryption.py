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
            print(f"🔐 原始数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 转换为JSON字符串 - 与前端保持一致
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            print(f"📄 JSON字符串长度: {len(json_str)}")
            print(f"📄 JSON字符串样本: {repr(json_str[:100])}...")
            
            # 将JSON字符串转换为UTF-8字节
            json_bytes = json_str.encode('utf-8')
            print(f"📄 UTF-8字节长度: {len(json_bytes)}")
            print(f"📄 UTF-8字节样本: {json_bytes[:20]}...")
            
            # 对字节进行XOR加密
            key_bytes = SimpleEncryption.SECRET_KEY.encode('utf-8')
            encrypted_bytes = bytearray()
            for i, byte in enumerate(json_bytes):
                key_byte = key_bytes[i % len(key_bytes)]
                encrypted_bytes.append(byte ^ key_byte)
            
            print(f"🔑 XOR加密完成，字节长度: {len(encrypted_bytes)}")
            print(f"🔑 加密字节样本: {encrypted_bytes[:20]}...")
            
            # Base64编码
            result = base64.b64encode(encrypted_bytes).decode('utf-8')
            print(f"✅ Base64编码完成，最终长度: {len(result)}")
            print(f"✅ 最终结果样本: {result[:50]}...")
            return result
        except Exception as e:
            print(f"❌ 加密失败: {type(e).__name__}: {e}")
            import traceback
            print(f"🔍 错误堆栈: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def decrypt(encrypted_data: str) -> Any:
        """解密数据"""
        try:
            print(f"🔓 开始解密数据，长度: {len(encrypted_data)}")
            print(f"🔓 加密数据样本: {encrypted_data[:100]}...")
            
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            print(f"📄 Base64解码完成，字节长度: {len(encrypted_bytes)}")
            print(f"📄 解码字节样本: {encrypted_bytes[:20]}...")
            
            # 对字节进行XOR解密
            key_bytes = SimpleEncryption.SECRET_KEY.encode('utf-8')
            decrypted_bytes = bytearray()
            for i, byte in enumerate(encrypted_bytes):
                key_byte = key_bytes[i % len(key_bytes)]
                decrypted_bytes.append(byte ^ key_byte)
            
            print(f"🔑 XOR解密完成，字节长度: {len(decrypted_bytes)}")
            print(f"🔑 解密字节样本: {decrypted_bytes[:20]}...")
            
            # 将字节转换回UTF-8字符串
            decrypted_str = decrypted_bytes.decode('utf-8')
            print(f"📄 UTF-8解码完成，字符串长度: {len(decrypted_str)}")
            print(f"📄 解密字符串样本: {repr(decrypted_str[:100])}...")
            
            # JSON解析
            result = json.loads(decrypted_str)
            print(f"✅ JSON解析完成，类型: {type(result)}")
            print(f"✅ 解析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        except Exception as e:
            print(f"❌ 解密失败: {type(e).__name__}: {e}")
            print(f"🔍 解密数据: {encrypted_data[:100]}...")
            import traceback
            print(f"🔍 错误堆栈: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def is_encrypted(data: Dict) -> bool:
        """检查数据是否已加密"""
        return isinstance(data, dict) and 'encrypted_data' in data
    
    @staticmethod
    def create_encrypted_payload(data: Any) -> Dict:
        """创建加密的请求载荷"""
        encrypted_data = SimpleEncryption.encrypt(data)
        return {
            'encrypted_data': encrypted_data,
            'timestamp': int(time.time() * 1000),
            'version': '1.0'
        }
