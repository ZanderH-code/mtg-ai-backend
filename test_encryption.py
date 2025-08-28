#!/usr/bin/env python3
"""
测试加密和解密功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.simple_encryption import SimpleEncryption
import json

def test_encryption():
    """测试加密和解密功能"""
    print("=== 测试加密和解密功能 ===")
    
    # 测试数据
    test_data = {
        "query": "蓝色瞬间法术",
        "language": "zh",
        "api_key": "test_key_123"
    }
    
    print(f"原始数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        # 加密
        print("\n🔐 开始加密...")
        encrypted_data = SimpleEncryption.encrypt(test_data)
        print(f"加密结果: {encrypted_data}")
        print(f"加密数据长度: {len(encrypted_data)}")
        
        # 检查是否已加密
        is_encrypted = SimpleEncryption.is_encrypted({"encrypted_data": encrypted_data})
        print(f"是否已加密: {is_encrypted}")
        
        # 解密
        print("\n🔓 开始解密...")
        decrypted_data = SimpleEncryption.decrypt(encrypted_data)
        print(f"解密结果: {json.dumps(decrypted_data, ensure_ascii=False, indent=2)}")
        
        # 验证结果
        if decrypted_data == test_data:
            print("✅ 加密解密测试成功！")
        else:
            print("❌ 加密解密测试失败！")
            print(f"期望: {test_data}")
            print(f"实际: {decrypted_data}")
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_encryption()
