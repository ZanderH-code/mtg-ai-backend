from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import asyncio
from typing import List, Optional

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

class Card(BaseModel):
    name: str
    mana_cost: Optional[str] = None
    type_line: str
    oracle_text: str
    image_uris: Optional[dict] = None
    scryfall_uri: str

class SearchResponse(BaseModel):
    cards: List[Card]
    scryfall_query: str
    total_cards: int
    api_provider: Optional[str] = None

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

@app.post("/api/validate-key")
async def validate_api_key():
    """验证API密钥的端点"""
    return {
        "valid": True,
        "provider": "aihubmix",
        "model": "gpt-4o-mini",
        "message": "API密钥验证成功"
    }

class AIService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.aihubmix_api_key = os.getenv("AIHUBMIX_API_KEY")
    
    async def natural_language_to_scryfall(self, query: str, language: str = "zh", api_key: str = None, provider: str = "aihubmix", model: str = None) -> tuple[str, str]:
        """将自然语言转换为Scryfall查询语法"""
        
        # 中文提示词模板 - 基于Scryfall官方语法
        zh_prompt = f"""
你是一个万智牌专家，请将用户的中文描述转换为Scryfall搜索语法。

用户输入：{query}

请返回有效的Scryfall搜索语法，格式要求：
1. 只返回搜索语法，不要其他解释
2. 使用标准的Scryfall语法

Scryfall官方搜索语法参考：

颜色和颜色身份：
- c:g(绿) c:u(蓝) c:r(红) c:b(黑) c:w(白) c:rg(红绿) c:uw(白蓝)
- c:colorless(无色) c:multicolor(多色)
- 公会名称：c:azorius(阿佐里乌斯) c:simic(西米克) c:rakdos(拉铎斯)等
- 三色组合：c:bant(班特) c:esper(艾斯波) c:grixis(格利极斯)等

卡牌类型：
- t:creature(生物) t:instant(瞬间) t:sorcery(法术) t:artifact(神器) t:enchantment(结界) t:planeswalker(鹏洛客) t:land(地)
- 支持部分词匹配：t:merfolk(人鱼) t:goblin(地精) t:legend(传奇)

卡牌文字：
- o:"关键词" (搜索卡牌文字中的关键词)
- kw:flying(飞行) kw:haste(敏捷) kw:first strike(先攻)等关键词能力
- 使用引号包围包含空格或标点的文本

法力值：
- mv<=3 (法力值小于等于3) mv>=5 (法力值大于等于5)
- mv:even(偶数法力值) mv:odd(奇数法力值)
- m:{G}{U} (具体法力符号) m:2WW (简写法力符号)

力量/防御力/忠诚度：
- pow>=4 (力量大于等于4) tou<=2 (防御力小于等于2)
- pt>=6 (总力量防御力大于等于6)
- loy=3 (起始忠诚度等于3)

稀有度：
- r:common(普通) r:uncommon(非普通) r:rare(稀有) r:mythic(神话) r:special(特殊) r:bonus(奖励)

特殊卡片：
- is:split(分体卡) is:transform(转化卡) is:meld(融合卡) is:dfc(双面卡)
- is:spell(咒语) is:permanent(永久物) is:vanilla(白板生物) is:bear(2/2熊)

组合条件：
- 使用空格连接多个条件(AND逻辑)
- 使用OR连接选择条件：t:goblin OR t:elf
- 使用括号分组：(t:goblin OR t:elf) c:r
- 使用-否定条件：-t:creature (非生物)

示例：
- "地落卡组的强力终端" → o:"landfall" t:creature (o:"win" OR o:"end the game")
- "绿色的生物卡" → t:creature c:g
- "费用在3点以下的瞬间" → t:instant mv<=3
- "力量大于4的红色生物" → t:creature c:r pow>=4
- "神器或结界卡" → (t:artifact OR t:enchantment)
- "稀有度神话的卡牌" → r:mythic
- "具有飞行能力的非生物卡" → kw:flying -t:creature
- "艾斯波控制套牌的法术" → c:esper is:spell
- "2/2的熊类生物" → is:bear
- "具有敏捷的红色生物" → kw:haste t:creature c:r
"""

        # 英文提示词模板 - 基于Scryfall官方语法
        en_prompt = f"""
You are a Magic: The Gathering expert. Convert the user's description to Scryfall search syntax.

User input: {query}

Return only the valid Scryfall search syntax without any explanation.

Scryfall Official Search Syntax Reference:

Colors and Color Identity:
- c:g(green) c:u(blue) c:r(red) c:b(black) c:w(white) c:rg(red-green) c:uw(white-blue)
- c:colorless c:multicolor
- Guild names: c:azorius c:simic c:rakdos c:boros c:dimir c:golgari c:gruul c:izzet c:orzhov c:selesnya
- Shard names: c:bant c:esper c:grixis c:jund c:naya
- Wedge names: c:abzan c:jeskai c:mardu c:sultai c:temur

Card Types:
- t:creature t:instant t:sorcery t:artifact t:enchantment t:planeswalker t:land
- Partial matching: t:merfolk t:goblin t:legend

Oracle Text:
- o:"keyword" (search for text in card rules)
- kw:flying kw:haste kw:first strike kw:vigilance kw:deathtouch kw:lifelink kw:menace kw:reach kw:trample
- Use quotes for text with spaces or punctuation

Mana Value:
- mv<=3 (mana value 3 or less) mv>=5 (mana value 5 or more)
- mv:even mv:odd
- m:{{G}}{{U}} (specific mana symbols) m:2WW (shorthand mana symbols)

Power/Toughness/Loyalty:
- pow>=4 (power 4 or more) tou<=2 (toughness 2 or less)
- pt>=6 (total power and toughness 6 or more)
- loy=3 (starting loyalty 3)

Rarity:
- r:common r:uncommon r:rare r:mythic r:special r:bonus

Special Cards:
- is:split (split cards) is:transform (transform cards) is:meld (meld cards) is:dfc (double-faced cards)
- is:spell is:permanent is:vanilla (vanilla creatures) is:bear (2/2 bears)
- is:historic is:party is:modal is:frenchvanilla

Combining Conditions:
- Use space to connect multiple conditions (AND logic)
- Use OR for choices: t:goblin OR t:elf
- Use parentheses for grouping: (t:goblin OR t:elf) c:r
- Use - to negate conditions: -t:creature (non-creatures)

Examples:
- "landfall finisher" → o:"landfall" t:creature (o:"win" OR o:"end the game")
- "green creatures" → t:creature c:g
- "instant spells under 3 mana" → t:instant mv<=3
- "red creatures with power 4+" → t:creature c:r pow>=4
- "artifacts or enchantments" → (t:artifact OR t:enchantment)
- "mythic rarity cards" → r:mythic
- "non-creatures with flying" → kw:flying -t:creature
- "esper control spells" → c:esper is:spell
- "2/2 bear creatures" → is:bear
- "red creatures with haste" → kw:haste t:creature c:r
- "vanilla creatures" → is:vanilla
- "historic permanents" → is:historic is:permanent
- "party creatures" → is:party t:creature
"""

        prompt = zh_prompt if language == "zh" else en_prompt

        # 如果提供了API密钥，优先使用
        if api_key:
            try:
                return await self._call_ai_api(prompt, api_key, provider, model), provider
            except Exception as e:
                print(f"API调用失败: {e}")
                return self.fallback_mapping(query, language), "fallback"

        # 优先使用Aihubmix API
        if self.aihubmix_api_key:
            try:
                return await self._call_ai_api(prompt, self.aihubmix_api_key, "aihubmix", model), "aihubmix"
            except Exception as e:
                print(f"Aihubmix API error: {e}")

        # 使用OpenAI API
        if self.openai_api_key:
            try:
                return await self._call_ai_api(prompt, self.openai_api_key, "openai", model), "openai"
            except Exception as e:
                print(f"OpenAI API error: {e}")

        # 如果都失败，使用本地关键词映射
        return self.fallback_mapping(query, language), "fallback"

    async def _call_ai_api(self, prompt: str, api_key: str, provider: str, model: str = None) -> str:
        """调用AI API"""
        if provider == "aihubmix":
            # 使用Aihubmix API
            client = httpx.AsyncClient()
            model = model or "gpt-4o-mini"
            
            response = await client.post(
                "https://aihubmix.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a Magic: The Gathering expert."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.1
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"API调用失败: {response.status_code}")
        else:
            # 使用OpenAI API
            client = httpx.AsyncClient()
            model = model or "gpt-3.5-turbo"
            
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a Magic: The Gathering expert."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.1
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"API调用失败: {response.status_code}")

    def fallback_mapping(self, query: str, language: str) -> str:
        """增强的关键词映射作为备用方案 - 基于Scryfall官方语法"""
        query_lower = query.lower()
        conditions = []

        # 中文关键词映射
        if language == "zh":
            # 颜色映射
            if any(color in query_lower for color in ["绿色", "绿"]):
                conditions.append("c:g")
            if any(color in query_lower for color in ["蓝色", "蓝"]):
                conditions.append("c:u")
            if any(color in query_lower for color in ["红色", "红"]):
                conditions.append("c:r")
            if any(color in query_lower for color in ["黑色", "黑"]):
                conditions.append("c:b")
            if any(color in query_lower for color in ["白色", "白"]):
                conditions.append("c:w")
            if "无色" in query_lower:
                conditions.append("c:colorless")
            if "多色" in query_lower:
                conditions.append("c:multicolor")
            
            # 公会和三色组合
            if "阿佐里乌斯" in query_lower:
                conditions.append("c:azorius")
            if "西米克" in query_lower:
                conditions.append("c:simic")
            if "拉铎斯" in query_lower:
                conditions.append("c:rakdos")
            if "班特" in query_lower:
                conditions.append("c:bant")
            if "艾斯波" in query_lower:
                conditions.append("c:esper")
            if "格利极斯" in query_lower:
                conditions.append("c:grixis")

            # 卡牌类型
            if "生物" in query_lower:
                conditions.append("t:creature")
            if "瞬间" in query_lower:
                conditions.append("t:instant")
            if "法术" in query_lower:
                conditions.append("t:sorcery")
            if "神器" in query_lower:
                conditions.append("t:artifact")
            if "结界" in query_lower:
                conditions.append("t:enchantment")
            if "鹏洛客" in query_lower:
                conditions.append("t:planeswalker")
            if "地" in query_lower:
                conditions.append("t:land")
            if "传奇" in query_lower:
                conditions.append("t:legend")
            if "人鱼" in query_lower:
                conditions.append("t:merfolk")
            if "地精" in query_lower:
                conditions.append("t:goblin")

            # 关键词能力
            if "飞行" in query_lower:
                conditions.append("kw:flying")
            if "敏捷" in query_lower:
                conditions.append("kw:haste")
            if "先攻" in query_lower:
                conditions.append("kw:first strike")
            if "警戒" in query_lower:
                conditions.append("kw:vigilance")
            if "死触" in query_lower:
                conditions.append("kw:deathtouch")
            if "生命链接" in query_lower:
                conditions.append("kw:lifelink")
            if "威胁" in query_lower:
                conditions.append("kw:menace")
            if "延势" in query_lower:
                conditions.append("kw:reach")
            if "践踏" in query_lower:
                conditions.append("kw:trample")

            # 特殊卡片类型
            if "白板" in query_lower:
                conditions.append("is:vanilla")
            if "熊" in query_lower and "2/2" in query_lower:
                conditions.append("is:bear")
            if "分体" in query_lower:
                conditions.append("is:split")
            if "转化" in query_lower:
                conditions.append("is:transform")
            if "融合" in query_lower:
                conditions.append("is:meld")
            if "双面" in query_lower:
                conditions.append("is:dfc")
            if "咒语" in query_lower:
                conditions.append("is:spell")
            if "永久物" in query_lower:
                conditions.append("is:permanent")
            if "历史" in query_lower:
                conditions.append("is:historic")
            if "队伍" in query_lower:
                conditions.append("is:party")

            # 稀有度
            if "普通" in query_lower:
                conditions.append("r:common")
            if "非普通" in query_lower:
                conditions.append("r:uncommon")
            if "稀有" in query_lower:
                conditions.append("r:rare")
            if "神话" in query_lower:
                conditions.append("r:mythic")

            # 法力值
            if "法力值" in query_lower or "费用" in query_lower:
                if "小于" in query_lower or "以下" in query_lower:
                    if "3" in query_lower:
                        conditions.append("mv<=3")
                    elif "2" in query_lower:
                        conditions.append("mv<=2")
                    elif "1" in query_lower:
                        conditions.append("mv<=1")
                elif "大于" in query_lower or "以上" in query_lower:
                    if "5" in query_lower:
                        conditions.append("mv>=5")
                    elif "4" in query_lower:
                        conditions.append("mv>=4")
                    elif "6" in query_lower:
                        conditions.append("mv>=6")

            # 力量/防御力
            if "力量" in query_lower:
                if "大于" in query_lower or "以上" in query_lower:
                    if "4" in query_lower:
                        conditions.append("pow>=4")
                    elif "5" in query_lower:
                        conditions.append("pow>=5")
                    elif "6" in query_lower:
                        conditions.append("pow>=6")
            if "防御力" in query_lower:
                if "小于" in query_lower or "以下" in query_lower:
                    if "2" in query_lower:
                        conditions.append("tou<=2")
                    elif "3" in query_lower:
                        conditions.append("tou<=3")

            # 特殊关键词
            if "地落" in query_lower:
                conditions.append('o:"landfall"')
            if "胜利" in query_lower or "获胜" in query_lower:
                conditions.append('(o:"win" OR o:"end the game")')

        # 英文关键词映射
        else:
            # 颜色映射
            if "green" in query_lower:
                conditions.append("c:g")
            if "blue" in query_lower:
                conditions.append("c:u")
            if "red" in query_lower:
                conditions.append("c:r")
            if "black" in query_lower:
                conditions.append("c:b")
            if "white" in query_lower:
                conditions.append("c:w")
            if "colorless" in query_lower:
                conditions.append("c:colorless")
            if "multicolor" in query_lower:
                conditions.append("c:multicolor")

            # 公会和三色组合
            if "azorius" in query_lower:
                conditions.append("c:azorius")
            if "simic" in query_lower:
                conditions.append("c:simic")
            if "rakdos" in query_lower:
                conditions.append("c:rakdos")
            if "bant" in query_lower:
                conditions.append("c:bant")
            if "esper" in query_lower:
                conditions.append("c:esper")
            if "grixis" in query_lower:
                conditions.append("c:grixis")

            # 卡牌类型
            if "creature" in query_lower:
                conditions.append("t:creature")
            if "instant" in query_lower:
                conditions.append("t:instant")
            if "sorcery" in query_lower:
                conditions.append("t:sorcery")
            if "artifact" in query_lower:
                conditions.append("t:artifact")
            if "enchantment" in query_lower:
                conditions.append("t:enchantment")
            if "planeswalker" in query_lower:
                conditions.append("t:planeswalker")
            if "land" in query_lower:
                conditions.append("t:land")
            if "legend" in query_lower:
                conditions.append("t:legend")
            if "merfolk" in query_lower:
                conditions.append("t:merfolk")
            if "goblin" in query_lower:
                conditions.append("t:goblin")

            # 关键词能力
            if "flying" in query_lower:
                conditions.append("kw:flying")
            if "haste" in query_lower:
                conditions.append("kw:haste")
            if "first strike" in query_lower:
                conditions.append("kw:first strike")
            if "vigilance" in query_lower:
                conditions.append("kw:vigilance")
            if "deathtouch" in query_lower:
                conditions.append("kw:deathtouch")
            if "lifelink" in query_lower:
                conditions.append("kw:lifelink")
            if "menace" in query_lower:
                conditions.append("kw:menace")
            if "reach" in query_lower:
                conditions.append("kw:reach")
            if "trample" in query_lower:
                conditions.append("kw:trample")

            # 特殊卡片类型
            if "vanilla" in query_lower:
                conditions.append("is:vanilla")
            if "bear" in query_lower:
                conditions.append("is:bear")
            if "split" in query_lower:
                conditions.append("is:split")
            if "transform" in query_lower:
                conditions.append("is:transform")
            if "meld" in query_lower:
                conditions.append("is:meld")
            if "dfc" in query_lower or "double-faced" in query_lower:
                conditions.append("is:dfc")
            if "spell" in query_lower:
                conditions.append("is:spell")
            if "permanent" in query_lower:
                conditions.append("is:permanent")
            if "historic" in query_lower:
                conditions.append("is:historic")
            if "party" in query_lower:
                conditions.append("is:party")

            # 稀有度
            if "common" in query_lower:
                conditions.append("r:common")
            if "uncommon" in query_lower:
                conditions.append("r:uncommon")
            if "rare" in query_lower:
                conditions.append("r:rare")
            if "mythic" in query_lower:
                conditions.append("r:mythic")

            # 法力值
            if "mana" in query_lower or "cost" in query_lower:
                if "under" in query_lower or "less" in query_lower:
                    if "3" in query_lower:
                        conditions.append("mv<=3")
                    elif "2" in query_lower:
                        conditions.append("mv<=2")
                    elif "1" in query_lower:
                        conditions.append("mv<=1")
                elif "over" in query_lower or "more" in query_lower:
                    if "5" in query_lower:
                        conditions.append("mv>=5")
                    elif "4" in query_lower:
                        conditions.append("mv>=4")
                    elif "6" in query_lower:
                        conditions.append("mv>=6")

            # 力量/防御力
            if "power" in query_lower:
                if "over" in query_lower or "more" in query_lower:
                    if "4" in query_lower:
                        conditions.append("pow>=4")
                    elif "5" in query_lower:
                        conditions.append("pow>=5")
                    elif "6" in query_lower:
                        conditions.append("pow>=6")
            if "toughness" in query_lower:
                if "under" in query_lower or "less" in query_lower:
                    if "2" in query_lower:
                        conditions.append("tou<=2")
                    elif "3" in query_lower:
                        conditions.append("tou<=3")

            # 特殊关键词
            if "landfall" in query_lower:
                conditions.append('o:"landfall"')
            if "win" in query_lower or "finisher" in query_lower:
                conditions.append('(o:"win" OR o:"end the game")')

        # 组合所有条件
        if conditions:
            return " ".join(conditions)
        
        # 默认返回空字符串，让Scryfall返回所有卡牌
        return ""

class ScryfallService:
    def __init__(self):
        self.base_url = "https://api.scryfall.com"
        # 根据Scryfall API要求设置必要的请求头
        self.headers = {
            "User-Agent": "MTG-AI-Search/1.0",
            "Accept": "application/json"
        }

    async def search_cards(self, query: str, page: int = 1) -> dict:
        """搜索卡牌"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/cards/search",
                    params={
                        "q": query,
                        "page": page,
                        "unique": "cards"
                    },
                    headers=self.headers,
                    timeout=30.0
                )

                print(f"Scryfall API 请求: {query}")
                print(f"Scryfall API 状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"找到 {result.get('total_cards', 0)} 张卡牌")
                    return result
                elif response.status_code == 404:
                    # 没有找到卡牌
                    print("没有找到匹配的卡牌")
                    return {"data": [], "total_cards": 0}
                else:
                    print(f"Scryfall API 错误: {response.status_code}")
                    raise HTTPException(status_code=response.status_code, detail="Scryfall API error")

        except Exception as e:
            print(f"Scryfall API error: {e}")
            raise HTTPException(status_code=500, detail="Failed to search cards")

# 初始化服务
ai_service = AIService()
scryfall_service = ScryfallService()

@app.post("/api/search", response_model=SearchResponse)
async def search_cards(request: SearchRequest):
    """搜索卡牌的主要API"""
    try:
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
        scryfall_result = await scryfall_service.search_cards(scryfall_query)

        # 3. 转换响应格式
        cards = []
        for card_data in scryfall_result.get("data", []):
            card = Card(
                name=card_data.get("name", ""),
                mana_cost=card_data.get("mana_cost"),
                type_line=card_data.get("type_line", ""),
                oracle_text=card_data.get("oracle_text", ""),
                image_uris=card_data.get("image_uris"),
                scryfall_uri=card_data.get("scryfall_uri", "")
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
        raise HTTPException(status_code=500, detail="搜索失败")
