import json
import base64
import time
from typing import Any, Dict, Optional

class SimpleEncryption:
    """简化的API密钥保护工具"""
    
    # 简单的混淆密钥 - 与前端保持一致
    MASK_KEY = "mtg2024"
    
    @staticmethod
    def _simple_mask(data: str, key: str) -> str:
        """简单的混淆"""
        masked = ""
        key_length = len(key)
        for i, char in enumerate(data):
            key_char = key[i % key_length]
            masked += chr(ord(char) ^ ord(key_char))
        return masked
    
    @staticmethod
    def encrypt(data: Any) -> str:
        """加密数据"""
        try:
            print(f"🔐 开始加密数据: {type(data)}")
            print(f"🔐 原始数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 转换为JSON字符串
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            print(f"📄 JSON字符串长度: {len(json_str)}")
            print(f"📄 JSON字符串样本: {repr(json_str[:100])}...")
            
            # 简单混淆
            masked = SimpleEncryption._simple_mask(json_str, SimpleEncryption.MASK_KEY)
            print(f"🔑 混淆完成，长度: {len(masked)}")
            print(f"🔑 混淆字符串样本: {repr(masked[:50])}...")
            
            # Base64编码
            result = base64.b64encode(masked.encode('utf-8')).decode('utf-8')
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
            decoded_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decoded = decoded_bytes.decode('utf-8')
            print(f"📄 Base64解码完成，字符串长度: {len(decoded)}")
            print(f"📄 解码字符串样本: {repr(decoded[:50])}...")
            
            # 简单解混淆
            unmasked = SimpleEncryption._simple_mask(decoded, SimpleEncryption.MASK_KEY)
            print(f"🔑 解混淆完成，长度: {len(unmasked)}")
            print(f"🔑 解混淆字符串样本: {repr(unmasked[:100])}...")
            
            # JSON解析
            result = json.loads(unmasked)
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
