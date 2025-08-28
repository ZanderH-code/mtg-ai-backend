from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from .encryption import SimpleEncryption
import json
import time

async def encryption_middleware(request: Request, call_next):
    """加密中间件 - 处理加密的请求和响应"""
    
    # 检查是否需要加密处理
    client_version = request.headers.get("X-Client-Version")
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
                        # 验证时间戳
                        timestamp = request_data.get('timestamp', 0)
                        if not SimpleEncryption.verify_timestamp(timestamp):
                            raise HTTPException(status_code=400, detail="请求已过期")
                        
                        # 验证签名
                        signature = request_data.get('signature', '')
                        decrypted_data = SimpleEncryption.decrypt(request_data['encrypted_data'])
                        if not SimpleEncryption.verify_signature(decrypted_data, timestamp, signature):
                            raise HTTPException(status_code=400, detail="签名验证失败")
                        
                        # 替换请求体
                        request._body = json.dumps(decrypted_data).encode('utf-8')
                        
                except Exception as e:
                    print(f"解密请求失败: {e}")
                    raise HTTPException(status_code=400, detail="请求解密失败")
        
        # 处理请求
        response = await call_next(request)
        
        # 加密响应数据
        if hasattr(response, 'body') and response.body:
            try:
                response_data = json.loads(response.body.decode('utf-8'))
                encrypted_response = SimpleEncryption.encrypt(response_data)
                
                # 创建新的响应
                return JSONResponse(
                    content={
                        "encrypted_data": encrypted_response,
                        "timestamp": int(time.time() * 1000)
                    },
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            except Exception as e:
                print(f"加密响应失败: {e}")
                # 如果加密失败，返回原始响应
                return response
        
        return response
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        print(f"中间件处理失败: {e}")
        # 如果处理失败，按普通请求处理
        response = await call_next(request)
        return response
