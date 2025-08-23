from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    default_models = {
        "aihubmix": [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "aihubmix"},
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "aihubmix"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "aihubmix"},
            {"id": "claude-3-haiku", "name": "Claude 3 Haiku", "provider": "aihubmix"},
            {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "provider": "aihubmix"},
            {"id": "gemini-pro", "name": "Gemini Pro", "provider": "aihubmix"}
        ],
        "openai": [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai"}
        ]
    }
    
    return {
        "success": True,
        "models": default_models,
        "message": "模型列表获取成功"
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
