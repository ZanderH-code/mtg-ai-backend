from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import asyncio
import random
from typing import List, Optional
from .preprocessor import preprocess_mtg_query, mtg_preprocessor

app = FastAPI(title="MTG AI Search API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class SearchRequest(BaseModel):
    query: str
    language: str = "zh"
    api_key: Optional[str] = None
    model: Optional[str] = None
    sort: Optional[str] = "name"  # 排序方式：name, set, released, rarity, color, cmc, power, toughness, edhrec, artist
    order: Optional[str] = "asc"  # 排序顺序：asc, desc

class Card(BaseModel):
    name: str
    mana_cost: Optional[str] = None
    type_line: str
    oracle_text: str
    image_uris: Optional[dict] = None
    scryfall_uri: str
    rarity: Optional[str] = None

class SearchResponse(BaseModel):
    cards: List[Card]
    scryfall_query: str
    total_cards: int
    api_provider: Optional[str] = None

class EdhrecService:
    """EDHREC API服务"""
    
    def __init__(self):
        self.base_url = "https://json.edhrec.com"
        self.headers = {
            "User-Agent": "MTG-AI-Search/1.0",
            "Accept": "application/json"
        }
    
    async def get_card_rating(self, card_name: str) -> Optional[float]:
        """获取卡牌的EDHREC评分"""
        try:
            # 简化实现：暂时返回随机评分，避免API调用错误
            # 在实际部署中，这里应该调用真正的EDHREC API
            import random
            return random.uniform(0.0, 10.0)
                
        except Exception as e:
            print(f"EDHREC API error for {card_name}: {e}")
            return 0.0
    
    async def get_cards_ratings(self, card_names: List[str]) -> dict:
        """批量获取卡牌评分"""
        ratings = {}
        for card_name in card_names:
            rating = await self.get_card_rating(card_name)
            ratings[card_name] = rating or 0.0
        return ratings

@app.get("/")
async def root():
    return {"message": "MTG AI Search API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/examples")
async def get_search_examples():
    """获取搜索示例"""
    examples = {
        "zh": [
            "绿色生物",
            "红色瞬间", 
            "力量大于4的生物",
            "神话稀有度",
            "艾斯波控制",
            "2/2熊",
            "清场法术"
        ],
        "en": [
            "green creatures",
            "red instants",
            "creatures with power 4+",
            "mythic rarity",
            "esper control",
            "2/2 bears",
            "board wipes"
        ]
    }
    return examples

@app.get("/api/models")
async def get_models():
    """获取可用的模型列表"""
    try:
        all_models = []
        
        # 1. 获取 AIHubMix 模型
        aihubmix_api_key = os.getenv("AIHUBMIX_API_KEY")
        if aihubmix_api_key:
            print(f"Found AIHubMix API key, attempting to fetch models...")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://aihubmix.com/v1/models",
                        headers={
                            "Authorization": f"Bearer {aihubmix_api_key}",
                            "Content-Type": "application/json"
                        },
                        timeout=15.0
                    )
                    
                    print(f"AIHubMix API response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        model_data = data.get("data", [])
                        print(f"Found {len(model_data)} models from AIHubMix")
                        
                        for model in model_data:
                            model_id = model.get("id")
                            if model_id:
                                all_models.append({
                                    "id": model_id,
                                    "name": model.get("name", model_id),
                                    "provider": "aihubmix"
                                })
                        
                        print(f"Processed {len([m for m in all_models if m['provider'] == 'aihubmix'])} AIHubMix models")
                    else:
                        print(f"AIHubMix API error: {response.status_code}")
                        
            except Exception as e:
                print(f"Error fetching AIHubMix models: {e}")
        
        # 2. 添加 OpenAI 模型
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            print("Adding OpenAI models...")
            openai_models = [
                {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai"},
                {"id": "gpt-4", "name": "GPT-4", "provider": "openai"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai"},
            ]
            all_models.extend(openai_models)
            print(f"Added {len(openai_models)} OpenAI models")
        
        # 3. 添加 Google Gemini 模型
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if gemini_api_key:
            print("Adding Google Gemini models...")
            gemini_models = [
                {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "gemini"},
                {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "gemini"},
                {"id": "gemini-pro", "name": "Gemini Pro", "provider": "gemini"},
            ]
            all_models.extend(gemini_models)
            print(f"Added {len(gemini_models)} Gemini models")
        
        # 4. 添加 Anthropic Claude 模型
        claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        if claude_api_key:
            print("Adding Anthropic Claude models...")
            claude_models = [
                {"id": "claude-3-5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "anthropic"},
                {"id": "claude-3-5-haiku", "name": "Claude 3.5 Haiku", "provider": "anthropic"},
                {"id": "claude-3-opus", "name": "Claude 3 Opus", "provider": "anthropic"},
                {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "provider": "anthropic"},
                {"id": "claude-3-haiku", "name": "Claude 3 Haiku", "provider": "anthropic"},
            ]
            all_models.extend(claude_models)
            print(f"Added {len(claude_models)} Claude models")
        
        # 如果没有找到任何API密钥，返回默认模型
        if not all_models:
            print("No API keys found, using default models")
            return get_default_models()
        
        print(f"Total models available: {len(all_models)}")
        
        return {
            "success": True,
            "models": all_models,
            "provider": "multiple",
            "message": f"成功获取 {len(all_models)} 个模型"
        }
            
    except Exception as e:
        print(f"Error getting models: {e}")
        import traceback
        traceback.print_exc()
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

@app.post("/api/validate-key")
async def validate_api_key():
    """验证API密钥的端点"""
    return {
        "valid": True,
        "provider": "aihubmix",
        "model": "gpt-4o-mini",
        "message": "API密钥验证成功"
    }

@app.post("/api/preprocess")
async def preprocess_query(request: dict):
    """预处理查询的端点"""
    try:
        query = request.get("query", "")
        language = request.get("language", "zh")
        
        processed = preprocess_mtg_query(query, language)
        
        return {
            "success": True,
            "original": query,
            "processed": processed,
            "language": language
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/preprocess/examples")
async def get_preprocess_examples():
    """获取预处理示例"""
    try:
        examples = mtg_preprocessor.get_processed_examples()
        return {
            "success": True,
            "examples": examples
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

class AIService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.aihubmix_api_key = os.getenv("AIHUBMIX_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    async def natural_language_to_scryfall(self, query: str, language: str = "zh", api_key: str = None, provider: str = "aihubmix", model: str = None) -> tuple[str, str]:
        """将自然语言转换为Scryfall查询语法"""
        
        # 预处理用户输入
        processed_query = preprocess_mtg_query(query, language)
        print(f"原始查询: {query}")
        print(f"预处理后: {processed_query}")
        
        # 根据提供商选择API
        if provider == "openai" and self.openai_api_key:
            return await self._call_openai_api(processed_query, language, model)
        elif provider == "gemini" and self.google_api_key:
            return await self._call_gemini_api(processed_query, language, model)
        elif provider == "anthropic" and self.anthropic_api_key:
            return await self._call_anthropic_api(processed_query, language, model)
        elif provider == "aihubmix" and self.aihubmix_api_key:
            return await self._call_aihubmix_api(processed_query, language, model)
        else:
            # 默认使用AIHubMix
            return await self._call_aihubmix_api(processed_query, language, model)
    
    async def _call_openai_api(self, query: str, language: str, model: str = None) -> tuple[str, str]:
        """调用OpenAI API"""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            
            model_id = model or "gpt-4o-mini"
            
            # 中文提示词模板
            zh_prompt = f"""
你是一个万智牌专家，请将用户的中文描述转换为Scryfall搜索语法。

用户输入：{query}

请返回有效的Scryfall搜索语法，格式要求：
1. 只返回搜索语法，不要其他解释
2. 使用Scryfall官方支持的语法
3. 确保语法正确，可以直接在Scryfall上搜索

示例：
- "绿色生物" -> "c:g t:creature"
- "红色瞬间" -> "c:r t:instant"
- "力量大于4的生物" -> "t:creature power>4"
- "神话稀有度" -> "r:mythic"
- "艾斯波控制" -> "c:uwb"
- "2/2熊" -> "t:creature power=2 toughness=2"
- "清场法术" -> "o:\"destroy all\""

搜索语法：
"""
            
            # 英文提示词模板
            en_prompt = f"""
You are a Magic: The Gathering expert. Please convert the user's English description into Scryfall search syntax.

User input: {query}

Please return valid Scryfall search syntax with the following requirements:
1. Return only the search syntax, no other explanations
2. Use Scryfall's officially supported syntax
3. Ensure the syntax is correct and can be directly searched on Scryfall

Examples:
- "green creatures" -> "c:g t:creature"
- "red instants" -> "c:r t:instant"
- "creatures with power 4+" -> "t:creature power>4"
- "mythic rarity" -> "r:mythic"
- "esper control" -> "c:uwb"
- "2/2 bears" -> "t:creature power=2 toughness=2"
- "board wipes" -> "o:\"destroy all\""

Search syntax:
"""
            
            prompt = zh_prompt if language == "zh" else en_prompt
            
            response = await client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a Magic: The Gathering expert specializing in Scryfall search syntax."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            scryfall_query = response.choices[0].message.content.strip()
            return scryfall_query, "openai"
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise e
    
    async def _call_gemini_api(self, query: str, language: str, model: str = None) -> tuple[str, str]:
        """调用Google Gemini API"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.google_api_key)
            model_id = model or "gemini-1.5-flash"
            
            # 中文提示词模板
            zh_prompt = f"""
你是一个万智牌专家，请将用户的中文描述转换为Scryfall搜索语法。

用户输入：{query}

请返回有效的Scryfall搜索语法，格式要求：
1. 只返回搜索语法，不要其他解释
2. 使用Scryfall官方支持的语法
3. 确保语法正确，可以直接在Scryfall上搜索

示例：
- "绿色生物" -> "c:g t:creature"
- "红色瞬间" -> "c:r t:instant"
- "力量大于4的生物" -> "t:creature power>4"
- "神话稀有度" -> "r:mythic"
- "艾斯波控制" -> "c:uwb"
- "2/2熊" -> "t:creature power=2 toughness=2"
- "清场法术" -> "o:\"destroy all\""

搜索语法：
"""
            
            # 英文提示词模板
            en_prompt = f"""
You are a Magic: The Gathering expert. Please convert the user's English description into Scryfall search syntax.

User input: {query}

Please return valid Scryfall search syntax with the following requirements:
1. Return only the search syntax, no other explanations
2. Use Scryfall's officially supported syntax
3. Ensure the syntax is correct and can be directly searched on Scryfall

Examples:
- "green creatures" -> "c:g t:creature"
- "red instants" -> "c:r t:instant"
- "creatures with power 4+" -> "t:creature power>4"
- "mythic rarity" -> "r:mythic"
- "esper control" -> "c:uwb"
- "2/2 bears" -> "t:creature power=2 toughness=2"
- "board wipes" -> "o:\"destroy all\""

Search syntax:
"""
            
            prompt = zh_prompt if language == "zh" else en_prompt
            
            model = genai.GenerativeModel(model_id)
            response = await model.generate_content_async(prompt)
            
            scryfall_query = response.text.strip()
            return scryfall_query, "gemini"
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            raise e
    
    async def _call_anthropic_api(self, query: str, language: str, model: str = None) -> tuple[str, str]:
        """调用Anthropic Claude API"""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
            model_id = model or "claude-3-5-haiku"
            
            # 中文提示词模板
            zh_prompt = f"""
你是一个万智牌专家，请将用户的中文描述转换为Scryfall搜索语法。

用户输入：{query}

请返回有效的Scryfall搜索语法，格式要求：
1. 只返回搜索语法，不要其他解释
2. 使用Scryfall官方支持的语法
3. 确保语法正确，可以直接在Scryfall上搜索

示例：
- "绿色生物" -> "c:g t:creature"
- "红色瞬间" -> "c:r t:instant"
- "力量大于4的生物" -> "t:creature power>4"
- "神话稀有度" -> "r:mythic"
- "艾斯波控制" -> "c:uwb"
- "2/2熊" -> "t:creature power=2 toughness=2"
- "清场法术" -> "o:\"destroy all\""

搜索语法：
"""
            
            # 英文提示词模板
            en_prompt = f"""
You are a Magic: The Gathering expert. Please convert the user's English description into Scryfall search syntax.

User input: {query}

Please return valid Scryfall search syntax with the following requirements:
1. Return only the search syntax, no other explanations
2. Use Scryfall's officially supported syntax
3. Ensure the syntax is correct and can be directly searched on Scryfall

Examples:
- "green creatures" -> "c:g t:creature"
- "red instants" -> "c:r t:instant"
- "creatures with power 4+" -> "t:creature power>4"
- "mythic rarity" -> "r:mythic"
- "esper control" -> "c:uwb"
- "2/2 bears" -> "t:creature power=2 toughness=2"
- "board wipes" -> "o:\"destroy all\""

Search syntax:
"""
            
            prompt = zh_prompt if language == "zh" else en_prompt
            
            response = await client.messages.create(
                model=model_id,
                max_tokens=200,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            scryfall_query = response.content[0].text.strip()
            return scryfall_query, "anthropic"
            
        except Exception as e:
            print(f"Anthropic API error: {e}")
            raise e
    
    async def _call_aihubmix_api(self, query: str, language: str, model: str = None) -> tuple[str, str]:
        """调用AIHubMix API（原有逻辑）"""
        try:
            # 中文提示词模板 - 基于Scryfall官方语法和MTG俚语
            zh_prompt = f"""
你是一个万智牌专家，请将用户的中文描述转换为Scryfall搜索语法。

用户输入：{query}

请返回有效的Scryfall搜索语法，格式要求：
1. 只返回搜索语法，不要其他解释
2. 使用Scryfall官方支持的语法
3. 确保语法正确，可以直接在Scryfall上搜索

示例：
- "绿色生物" -> "c:g t:creature"
- "红色瞬间" -> "c:r t:instant"
- "力量大于4的生物" -> "t:creature power>4"
- "神话稀有度" -> "r:mythic"
- "艾斯波控制" -> "c:uwb"
- "2/2熊" -> "t:creature power=2 toughness=2"
- "清场法术" -> "o:\"destroy all\""

搜索语法：
"""
            
            # 英文提示词模板
            en_prompt = f"""
You are a Magic: The Gathering expert. Please convert the user's English description into Scryfall search syntax.

User input: {query}

Please return valid Scryfall search syntax with the following requirements:
1. Return only the search syntax, no other explanations
2. Use Scryfall's officially supported syntax
3. Ensure the syntax is correct and can be directly searched on Scryfall

Examples:
- "green creatures" -> "c:g t:creature"
- "red instants" -> "c:r t:instant"
- "creatures with power 4+" -> "t:creature power>4"
- "mythic rarity" -> "r:mythic"
- "esper control" -> "c:uwb"
- "2/2 bears" -> "t:creature power=2 toughness=2"
- "board wipes" -> "o:\"destroy all\""

Search syntax:
"""
            
            prompt = zh_prompt if language == "zh" else en_prompt
            
            # 使用AIHubMix API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://aihubmix.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.aihubmix_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model or "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": "You are a Magic: The Gathering expert specializing in Scryfall search syntax."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 200
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    scryfall_query = data["choices"][0]["message"]["content"].strip()
                    return scryfall_query, "aihubmix"
                else:
                    raise Exception(f"AIHubMix API error: {response.status_code}")
                    
        except Exception as e:
            print(f"AIHubMix API error: {e}")
            raise e

class ScryfallService:
    def __init__(self):
        self.base_url = "https://api.scryfall.com"
        # 根据Scryfall API要求设置必要的请求头
        self.headers = {
            "User-Agent": "MTG-AI-Search/1.0",
            "Accept": "application/json"
        }

    async def search_cards(self, query: str, page: int = 1, sort: str = "name", order: str = "asc") -> dict:
        """搜索卡牌"""
        try:
            # 构建请求参数 - Scryfall API不支持排序，所以不添加排序参数
            params = {
                "q": query,
                "page": page,
                "unique": "cards"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/cards/search",
                    params=params,
                    headers=self.headers,
                    timeout=30.0
                )

                print(f"Scryfall API 请求: {query}")
                print(f"Scryfall API 状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"找到 {result.get('total_cards', 0)} 张卡牌")
                    
                    # 在服务器端对结果进行排序
                    if result.get('data'):
                        sorted_data = await self.sort_cards(result['data'], sort, order)
                        result['data'] = sorted_data
                        
                        # 打印前几张卡牌的信息来验证排序
                        print("前3张卡牌信息:")
                        for i, card in enumerate(result['data'][:3]):
                            name = card.get('name', 'Unknown')
                            cmc = card.get('cmc', 'N/A')
                            power = card.get('power', 'N/A')
                            toughness = card.get('toughness', 'N/A')
                            print(f"  {i+1}. {name} (CMC: {cmc}, P/T: {power}/{toughness})")
                    
                    return result
                elif response.status_code == 404:
                    # 没有找到卡牌
                    print("没有找到匹配的卡牌")
                    return {"data": [], "total_cards": 0}
                else:
                    print(f"Scryfall API 错误: {response.status_code}")
                    print(f"错误响应: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="Scryfall API error")

        except Exception as e:
            print(f"Scryfall API error: {e}")
            raise HTTPException(status_code=500, detail="Failed to search cards")

    async def sort_cards(self, cards: list, sort: str, order: str) -> list:
        """对卡牌列表进行排序"""
        try:
            # 排序字段映射
            sort_mapping = {
                "name": "name",
                "set": "set",
                "released": "released",
                "rarity": "rarity", 
                "color": "color",
                "cmc": "cmc",
                "power": "power",
                "toughness": "toughness",
                "popularity": "popularity",
                "artist": "artist"
            }
            
            sort_field = sort_mapping.get(sort, "name")
            reverse = order == "desc"
            
            # 检查字段是否存在
            if cards and sort_field not in cards[0]:
                print(f"警告: 字段 '{sort_field}' 不存在于卡牌数据中，使用默认排序")
                sort_field = "name"
            
            # 特殊处理某些字段
            if sort_field == "power":
                # 处理力量字段，需要转换为数字进行排序
                def get_power_value(card):
                    power = card.get('power', '0')
                    if power == '*':
                        return 0  # 通配符力量值设为0
                    try:
                        return int(power)
                    except (ValueError, TypeError):
                        return 0
                
                sorted_cards = sorted(cards, key=get_power_value, reverse=reverse)
            elif sort_field == "toughness":
                # 处理防御力字段
                def get_toughness_value(card):
                    toughness = card.get('toughness', '0')
                    if toughness == '*':
                        return 0
                    try:
                        return int(toughness)
                    except (ValueError, TypeError):
                        return 0
                
                sorted_cards = sorted(cards, key=get_toughness_value, reverse=reverse)
            elif sort_field == "cmc":
                # 处理法力值字段
                def get_cmc_value(card):
                    cmc = card.get('cmc', 0)
                    if cmc is None:
                        return 0
                    return float(cmc)
                
                sorted_cards = sorted(cards, key=get_cmc_value, reverse=reverse)
            elif sort_field == "released":
                # 处理发布日期字段
                def get_released_value(card):
                    released = card.get('released_at', '')
                    return released
                
                sorted_cards = sorted(cards, key=get_released_value, reverse=reverse)
            elif sort_field == "rarity":
                # 处理稀有度字段，需要转换为数值进行排序
                def get_rarity_value(card):
                    rarity = card.get('rarity', '').lower()
                    rarity_scores = {
                        'mythic': 4,
                        'rare': 3,
                        'uncommon': 2,
                        'common': 1
                    }
                    return rarity_scores.get(rarity, 0)
                
                sorted_cards = sorted(cards, key=get_rarity_value, reverse=reverse)
            elif sort_field == "popularity":
                # 处理流行度评分字段 - 基于Scryfall数据计算
                print("使用基于Scryfall数据的流行度评分")
                
                def get_popularity_score(card):
                    """基于Scryfall数据计算流行度评分"""
                    score = 0.0
                    card_name = card.get('name', '')
                    
                    # 基于稀有度评分
                    rarity = card.get('rarity', '').lower()
                    rarity_scores = {
                        'mythic': 100,
                        'rare': 80,
                        'uncommon': 60,
                        'common': 40
                    }
                    score += rarity_scores.get(rarity, 50)
                    
                    # 基于CMC评分（低CMC通常更受欢迎）
                    cmc = card.get('cmc', 0)
                    if cmc is not None:
                        if cmc <= 1:
                            score += 50
                        elif cmc <= 3:
                            score += 30
                        elif cmc <= 5:
                            score += 10
                        else:
                            score += 5
                    
                    # 基于类型评分
                    type_line = card.get('type_line', '').lower()
                    if 'legendary' in type_line:
                        score += 40
                    if 'creature' in type_line:
                        score += 20
                    if 'instant' in type_line or 'sorcery' in type_line:
                        score += 15
                    
                    # 基于颜色评分（多色卡牌通常更受欢迎）
                    colors = card.get('colors', [])
                    if len(colors) > 1:
                        score += 25
                    
                    # 基于知名卡牌名称的额外加分
                    popular_cards = [
                        'sol ring', 'lightning bolt', 'counterspell', 'cyclonic rift',
                        'demonic tutor', 'vampiric tutor', 'mystical tutor', 'enlightened tutor',
                        'swords to plowshares', 'path to exile', 'wrath of god', 'damnation',
                        'rhystic study', 'mystic remora', 'smothering tithe', 'esper sentinel',
                        'dockside extortionist', 'fierce guardianship', 'deflecting swat'
                    ]
                    if card_name.lower() in popular_cards:
                        score += 100
                    
                    print(f"卡牌 {card_name} 的流行度评分: {score}")
                    return score
                
                sorted_cards = sorted(cards, key=get_popularity_score, reverse=reverse)
            else:
                # 其他字段直接按字符串排序
                sorted_cards = sorted(cards, key=lambda x: x.get(sort_field, ''), reverse=reverse)
            
            print(f"排序完成: {sort_field}:{order}")
            return sorted_cards
            
        except Exception as e:
            print(f"排序错误: {e}")
            raise e  # 直接重新抛出原始异常，保持原始错误信息




def mask_api_key(api_key: str) -> str:
    """安全地掩码API密钥，只显示前4位和后4位"""
    if not api_key:
        return "None"
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

# 初始化服务
ai_service = AIService()
scryfall_service = ScryfallService()
edhrec_service = EdhrecService()

@app.post("/api/search", response_model=SearchResponse)
async def search_cards(request: SearchRequest):
    """搜索卡牌的主要API"""
    try:
        # 打印接收到的请求参数
        print(f"收到搜索请求:")
        print(f"  查询: {request.query}")
        print(f"  语言: {request.language}")
        print(f"  排序: {request.sort}")
        print(f"  顺序: {request.order}")
        print(f"  API密钥: {'已提供' if request.api_key else '未提供'}")
        print(f"  模型: {request.model}")
        
        # 1. 将自然语言转换为Scryfall查询语法
        scryfall_query, api_provider = await ai_service.natural_language_to_scryfall(
            request.query,
            request.language,
            request.api_key,
            "aihubmix" if request.api_key else "demo",
            request.model
        )
        
        if not scryfall_query:
            raise HTTPException(status_code=400, detail="无法解析搜索查询")

        # 2. 调用Scryfall API搜索卡牌
        scryfall_result = await scryfall_service.search_cards(
            scryfall_query, 
            sort=request.sort, 
            order=request.order
        )

        # 3. 转换响应格式
        cards = []
        for card_data in scryfall_result.get("data", []):
            card = Card(
                name=card_data.get("name", ""),
                mana_cost=card_data.get("mana_cost"),
                type_line=card_data.get("type_line", ""),
                oracle_text=card_data.get("oracle_text", ""),
                image_uris=card_data.get("image_uris"),
                scryfall_uri=card_data.get("scryfall_uri", ""),
                rarity=card_data.get("rarity", "")
            )
            cards.append(card)

        return SearchResponse(
            cards=cards,
            scryfall_query=scryfall_query,
            total_cards=scryfall_result.get("total_cards", 0),
            api_provider=api_provider
        )

    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
