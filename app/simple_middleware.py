from fastapi import Request, Response
from fastapi.responses import JSONResponse
import json
from .simple_encryption import SimpleEncryption

async def simple_encryption_middleware(request: Request, call_next):
    """简化的加密中间件"""
    
    print(f"🔍 中间件开始处理: {request.method} {request.url.path}")
    
    # 跳过非POST/PUT请求
    if request.method not in ["POST", "PUT", "PATCH"]:
        print(f"⏭️ 跳过非POST/PUT请求: {request.method}")
        response = await call_next(request)
        return response
    
    # 跳过OPTIONS请求（CORS预检）
    if request.method == "OPTIONS":
        print(f"⏭️ 跳过OPTIONS请求")
        response = await call_next(request)
        return response
    
    try:
        # 读取请求体
        body = await request.body()
        if not body:
            print("⚠️ 请求体为空，直接处理")
            response = await call_next(request)
            return response
        
        print(f"📦 请求体大小: {len(body)} 字节")
        
        # 解析JSON
        try:
            request_data = json.loads(body.decode('utf-8'))
            print(f"✅ JSON解析成功: {type(request_data)}")
        except json.JSONDecodeError as json_error:
            print(f"❌ JSON解析失败: {json_error}")
            print(f"📄 原始请求体: {body.decode('utf-8', errors='ignore')[:200]}...")
            # 如果不是JSON，按普通请求处理
            response = await call_next(request)
            return response
        
        # 检查是否是加密请求
        print(f"🔐 检查加密状态: {SimpleEncryption.is_encrypted(request_data)}")
        if SimpleEncryption.is_encrypted(request_data):
            print("🔓 检测到加密请求，尝试解密...")
            print(f"📋 加密数据字段: {list(request_data.keys())}")
            print(f"📋 请求数据完整内容: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
            
            try:
                # 解密数据
                encrypted_data = request_data.get('encrypted_data')
                if not encrypted_data:
                    raise ValueError("缺少encrypted_data字段")
                
                print(f"🔑 开始解密数据...")
                print(f"🔑 加密数据长度: {len(encrypted_data)}")
                print(f"🔑 加密数据前50字符: {encrypted_data[:50]}...")
                decrypted_data = SimpleEncryption.decrypt(encrypted_data)
                print(f"✅ 解密成功: {type(decrypted_data)}")
                print(f"📄 解密内容: {json.dumps(decrypted_data, ensure_ascii=False, indent=2)}")
                
                # 替换请求体
                new_body = json.dumps(decrypted_data, ensure_ascii=False).encode('utf-8')
                request._body = new_body
                print(f"🔄 请求体已替换，新大小: {len(new_body)} 字节")
                
            except Exception as decrypt_error:
                print(f"❌ 解密失败: {type(decrypt_error).__name__}: {decrypt_error}")
                print(f"🔍 错误详情: {str(decrypt_error)}")
                # 解密失败时，返回错误响应
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "解密失败",
                        "message": "无法解密请求数据",
                        "details": str(decrypt_error),
                        "error_type": type(decrypt_error).__name__
                    }
                )
        else:
            print("📝 检测到明文请求，直接处理")
            print(f"📄 请求数据: {str(request_data)[:200]}...")
        
        # 调用下一个处理器
        print(f"🔄 调用下一个处理器...")
        response = await call_next(request)
        print(f"✅ 处理器返回，状态码: {response.status_code}")
        
        # 检查响应是否需要加密
        if hasattr(response, 'body') and response.body:
            try:
                # 解析响应数据
                response_data = json.loads(response.body.decode('utf-8'))
                print(f"📄 响应数据解析成功: {type(response_data)}")
                
                # 检查请求是否包含加密标志
                if SimpleEncryption.is_encrypted(request_data):
                    print("🔐 加密响应数据...")
                    try:
                        encrypted_response = SimpleEncryption.create_encrypted_payload(response_data)
                        print(f"✅ 响应加密成功")
                        
                        # 确保CORS头部被正确设置
                        headers = dict(response.headers)
                        headers.update({
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                            "Access-Control-Allow-Headers": "*",
                            "Access-Control-Allow-Credentials": "true"
                        })
                        
                        return JSONResponse(
                            content=encrypted_response,
                            status_code=response.status_code,
                            headers=headers
                        )
                    except Exception as encrypt_error:
                        print(f"❌ 响应加密失败: {type(encrypt_error).__name__}: {encrypt_error}")
                        # 加密失败时，返回原始响应
                        pass
                else:
                    print("📝 明文响应，无需加密")
            except Exception as response_error:
                print(f"❌ 响应数据处理失败: {type(response_error).__name__}: {response_error}")
                # 响应处理失败时，返回原始响应
                pass
        
        print(f"🏁 中间件处理完成")
        return response
        
    except Exception as e:
        print(f"💥 中间件处理错误: {type(e).__name__}: {e}")
        print(f"🔍 错误详情: {str(e)}")
        import traceback
        print(f"📚 错误堆栈: {traceback.format_exc()}")
        
        # 发生错误时，尝试正常处理请求
        try:
            print(f"🔄 尝试回退处理...")
            response = await call_next(request)
            print(f"✅ 回退处理成功，状态码: {response.status_code}")
            return response
        except Exception as fallback_error:
            print(f"❌ 回退处理也失败: {type(fallback_error).__name__}: {fallback_error}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "中间件错误",
                    "message": "请求处理失败",
                    "details": str(e),
                    "error_type": type(e).__name__,
                    "fallback_error": str(fallback_error)
                }
            )
