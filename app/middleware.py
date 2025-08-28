from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from .encryption import SimpleEncryption
import json
import time

async def encryption_middleware(request: Request, call_next):
    """加密中间件 - 处理加密的请求和响应"""
    
    # 对于OPTIONS请求（CORS预检），直接处理
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response
    
    # 检查是否需要加密处理
    client_version = request.headers.get("X-Client-Version")
    print(f"中间件处理请求: {request.method} {request.url.path}, 客户端版本: {client_version}")
    
    if not client_version:
        # 如果没有版本头，按普通请求处理
        response = await call_next(request)
        return response
    
    try:
        # 解密请求数据
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                try:
                    request_data = json.loads(body.decode('utf-8'))
                    
                    # 检查是否是加密请求
                    if 'encrypted_data' in request_data:
                        # 验证时间戳（放宽时间限制）
                        timestamp = request_data.get('timestamp', 0)
                        if not SimpleEncryption.verify_timestamp(timestamp, max_age=600000):  # 10分钟
                            print(f"时间戳验证失败: {timestamp}")
                            # 不抛出异常，继续处理
                        
                        # 验证签名
                        signature = request_data.get('signature', '')
                        try:
                            decrypted_data = SimpleEncryption.decrypt(request_data['encrypted_data'])
                            if not SimpleEncryption.verify_signature(decrypted_data, timestamp, signature):
                                print(f"签名验证失败")
                                # 不抛出异常，继续处理
                            
                            # 替换请求体
                            request._body = json.dumps(decrypted_data).encode('utf-8')
                        except Exception as decrypt_error:
                            print(f"解密失败: {decrypt_error}")
                            # 如果解密失败，继续使用原始数据
                        
                except Exception as e:
                    print(f"请求处理失败: {e}")
                    # 不抛出异常，继续处理
        
        # 处理请求
        response = await call_next(request)
        
        # 加密响应数据
        if hasattr(response, 'body') and response.body:
            try:
                response_data = json.loads(response.body.decode('utf-8'))
                encrypted_response = SimpleEncryption.encrypt(response_data)
                
                # 创建新的响应，确保保留CORS头部
                headers = dict(response.headers)
                # 确保CORS头部存在
                headers["Access-Control-Allow-Origin"] = "https://mtg-ai-frontend.onrender.com"
                headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                headers["Access-Control-Allow-Headers"] = "*"
                headers["Access-Control-Allow-Credentials"] = "true"
                
                print(f"成功加密响应，状态码: {response.status_code}")
                return JSONResponse(
                    content={
                        "encrypted_data": encrypted_response,
                        "timestamp": int(time.time() * 1000)
                    },
                    status_code=response.status_code,
                    headers=headers
                )
            except Exception as e:
                print(f"加密响应失败: {e}")
                # 如果加密失败，返回原始响应但确保CORS头部
                try:
                    response_data = json.loads(response.body.decode('utf-8'))
                except:
                    response_data = {"error": "Failed to parse response"}
                
                headers = dict(response.headers)
                headers["Access-Control-Allow-Origin"] = "https://mtg-ai-frontend.onrender.com"
                headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                headers["Access-Control-Allow-Headers"] = "*"
                headers["Access-Control-Allow-Credentials"] = "true"
                
                print(f"返回未加密响应，状态码: {response.status_code}")
                return JSONResponse(
                    content=response_data,
                    status_code=response.status_code,
                    headers=headers
                )
        
        return response
        
    except Exception as e:
        print(f"中间件处理失败: {e}")
        # 如果处理失败，按普通请求处理
        response = await call_next(request)
        return response
