from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI(title="MTG AI Search API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "MTG AI Search API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/models")
async def get_models():
    """获取可用的模型列表"""
    try:
        # 尝试从环境变量获取 Aihubmix API Key
        aihubmix_api_key = os.getenv("AIHUBMIX_API_KEY")
        
        if aihubmix_api_key:
            # 如果有 API Key，调用 Aihubmix API 获取真实模型列表
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://aihubmix.com/v1/models",
                    headers={
                        "Authorization": f"Bearer {aihubmix_api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # 转换 Aihubmix 格式为前端需要的格式
                    models = []
                    for model in data.get("data", []):
                        models.append({
                            "id": model.get("id"),
                            "name": model.get("id"),  # 使用 id 作为显示名称
                            "provider": "aihubmix"
                        })
                    
                    return {
                        "success": True,
                        "models": models,
                        "provider": "aihubmix",
                        "message": "模型列表获取成功"
                    }
                else:
                    print(f"Aihubmix API error: {response.status_code}")
                    # 如果 API 调用失败，返回默认模型列表
                    return get_default_models()
        else:
            # 如果没有 API Key，返回默认模型列表
            return get_default_models()
            
    except Exception as e:
        print(f"Error getting models: {e}")
        # 发生错误时返回默认模型列表
        return get_default_models()

def get_default_models():
    """返回默认的模型列表"""
    default_models = [
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "aihubmix"},
        {"id": "gpt-4o", "name": "GPT-4o", "provider": "aihubmix"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "aihubmix"},
        {"id": "claude-3-haiku", "name": "Claude 3 Haiku", "provider": "aihubmix"},
        {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "provider": "aihubmix"},
        {"id": "gemini-pro", "name": "Gemini Pro", "provider": "aihubmix"}
    ]
    
    return {
        "success": True,
        "models": default_models,
        "provider": "default",
        "message": "使用默认模型列表"
    }

@app.post("/api/search")
async def search_cards():
    """搜索卡牌的测试端点"""
    return {
        "cards": [
            {
                "name": "测试卡牌",
                "mana_cost": "{2}{G}",
                "type_line": "生物 — 测试",
                "oracle_text": "这是一个测试卡牌",
                "scryfall_uri": "https://scryfall.com/card/test/1"
            }
        ],
        "scryfall_query": "test",
        "total_cards": 1,
        "api_provider": "demo"
    }
