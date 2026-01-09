# api/services/llm_service.py
import aiohttp
import json
from typing import List, Dict, Any, AsyncGenerator, Optional
from dataclasses import dataclass
from config import config
import logging

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    role: str  # system/user/assistant
    content: str

class DeepSeekService:
    """DeepSeek API服务"""
    
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.base_url = config.DEEPSEEK_API_BASE
        self.model = config.DEEPSEEK_MODEL
        self.timeout = 30
        
        # 初始化tokenizer
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except (ImportError, Exception):
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """计算token数量"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return len(text) // 4  # 粗略估算
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """调用DeepSeek API"""

        if not self.api_key:
            return {
                "error": True,
                "message": "DeepSeek API key 未配置，请设置 DEEPSEEK_API_KEY 环境变量"
            }

        # 验证参数
        if not messages or not isinstance(messages, list):
            return {
                "error": True,
                "message": "无效的消息格式"
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": max(0.0, min(2.0, temperature)),  # 限制范围
            "max_tokens": max_tokens,
            "stream": stream
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        error_msg = f"API调用失败 (状态码: {response.status})"

                        # 尝试解析错误信息
                        try:
                            error_data = json.loads(error_text)
                            if "error" in error_data:
                                error_msg = error_data["error"].get("message", error_msg)
                        except:
                            pass

                        return {
                            "error": True,
                            "status_code": response.status,
                            "message": error_msg
                        }

                    if stream:
                        # 流式响应处理
                        return await self._handle_stream_response(response)
                    else:
                        data = await response.json()

                        # 验证响应格式
                        if "choices" not in data or not data["choices"]:
                            return {
                                "error": True,
                                "message": "API返回格式错误"
                            }

                        # 计算使用量
                        usage = data.get("usage", {})
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        completion_tokens = usage.get("completion_tokens", 0)
                        total_tokens = usage.get("total_tokens", 0)

                        # 计算成本（DeepSeek价格：¥0.14/百万tokens）
                        cost = total_tokens * 0.14 / 1_000_000

                        return {
                            "success": True,
                            "content": data["choices"][0]["message"]["content"],
                            "finish_reason": data["choices"][0].get("finish_reason", "stop"),
                            "usage": {
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "total_tokens": total_tokens,
                                "cost": round(cost, 6)
                            }
                        }

        except aiohttp.ClientError as e:
            return {
                "error": True,
                "message": f"网络请求失败: {str(e)}"
            }
        except json.JSONDecodeError as e:
            return {
                "error": True,
                "message": f"响应解析失败: {str(e)}"
            }
        except KeyError as e:
            return {
                "error": True,
                "message": f"响应数据缺失字段: {str(e)}"
            }
        except Exception as e:
            return {
                "error": True,
                "message": f"未知错误: {str(e)}"
            }
    
    async def _handle_stream_response(self, response) -> AsyncGenerator[str, None]:
        """处理流式响应"""
        async for line in response.content:
            if line:
                decoded = line.decode('utf-8').strip()
                
                if decoded.startswith("data: "):
                    data = decoded[6:]
                    
                    if data == "[DONE]":
                        break
                    
                    try:
                        chunk_data = json.loads(data)
                        if "choices" in chunk_data and chunk_data["choices"]:
                            delta = chunk_data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except:
                        continue
    
    async def generate_with_context(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """基于上下文生成回答"""
        
        if system_prompt is None:
            system_prompt = """请根据提供的参考信息回答问题。

参考信息如下：
{context}

请仔细分析以上信息，如果包含与问题相关的内容，请基于这些信息给出回答。可以适当总结、归纳，但不要编造信息中不存在的内容。

如果信息中确实没有相关内容，你可以说："根据提供的信息，没有找到直接相关的答案。"但请先仔细检查所有信息。"""

        messages = [
            {
                "role": "system",
                "content": system_prompt.format(context=context)
            },
            {
                "role": "user",
                "content": question
            }
        ]

        logger.info(f"Generating completion with message: {messages}")
        
        return await self.chat_completion(messages)