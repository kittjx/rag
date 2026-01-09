# api/services/unified_llm_service.py
from typing import Dict, List, Any, AsyncGenerator
from enum import Enum
import aiohttp
import json
from config import config
import logging

logger = logging.getLogger(__name__)

class LLMBackend(Enum):
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    OPENAI = "openai"
    QWEN = "qwen"

class UnifiedLLMService:
    """统一LLM服务，支持热切换"""

    def __init__(self):
        # 从环境变量或配置文件读取当前模式
        self.current_backend = self._detect_backend()
        logger.info(f"当前LLM后端: {self.current_backend.value}")

        # 后端配置
        self.configs = {
            LLMBackend.DEEPSEEK: {
                "base_url": config.DEEPSEEK_API_BASE,
                "model": config.DEEPSEEK_MODEL,
                "api_key": config.DEEPSEEK_API_KEY,
                "headers": lambda: {
                    "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                }
            },
            LLMBackend.QWEN: {
                "base_url": config.QWEN_API_BASE,
                "model": config.QWEN_MODEL,
                "api_key": config.QWEN_API_KEY,
                "headers": lambda: {
                    "Authorization": f"Bearer {config.QWEN_API_KEY}",
                    "Content-Type": "application/json"
                }
            },
            LLMBackend.OPENAI: {
                "base_url": config.OPENAI_API_BASE,
                "model": config.OPENAI_MODEL,
                "api_key": config.OPENAI_API_KEY,
                "headers": lambda: {
                    "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
            },
            LLMBackend.OLLAMA: {
                "base_url": config.OLLAMA_BASE_URL,
                "model": config.OLLAMA_MODEL,
                "api_key": None,
                "headers": lambda: {"Content-Type": "application/json"}
            }
        }
        
        # 健康状态
        self.backend_health = {
            LLMBackend.DEEPSEEK: False,
            LLMBackend.QWEN: False,
            LLMBackend.OPENAI: False,
            LLMBackend.OLLAMA: False
        }

        # 初始化时不自动检测（避免阻塞启动）
        # 将在第一次调用时检测
        self._backends_checked = False

    def _detect_backend(self) -> LLMBackend:
        """自动检测最佳后端"""

        # 如果明确指定了后端
        backend_name = config.LLM_BACKEND.lower()
        if backend_name != "auto":
            try:
                return LLMBackend(backend_name)
            except ValueError:
                logger.warning(f"未知的LLM后端: {backend_name}，使用自动检测")

        # 优先使用本地LLM
        if config.USE_LOCAL_LLM:
            logger.info("配置为使用本地LLM (Ollama)")
            return LLMBackend.OLLAMA

        # 按优先级检测API密钥
        if config.DEEPSEEK_API_KEY and config.DEEPSEEK_API_KEY != "your_deepseek_api_key_here":
            logger.info("检测到DeepSeek API密钥")
            return LLMBackend.DEEPSEEK

        if config.QWEN_API_KEY:
            logger.info("检测到Qwen API密钥")
            return LLMBackend.QWEN

        if config.OPENAI_API_KEY:
            logger.info("检测到OpenAI API密钥")
            return LLMBackend.OPENAI

        # 默认使用Ollama（本地）
        logger.warning("未检测到任何API密钥，默认使用Ollama（需要本地安装）")
        return LLMBackend.OLLAMA
    
    async def _check_backends(self):
        """检查各后端健康状态"""
        if self._backends_checked:
            return

        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 检查Ollama
            try:
                async with session.get(
                    self.configs[LLMBackend.OLLAMA]["base_url"] + "/api/tags"
                ) as response:
                    self.backend_health[LLMBackend.OLLAMA] = response.status == 200
                    if response.status == 200:
                        logger.info("Ollama后端可用")
            except Exception as e:
                self.backend_health[LLMBackend.OLLAMA] = False
                logger.debug(f"Ollama不可用: {e}")

            # API后端通过密钥判断
            self.backend_health[LLMBackend.DEEPSEEK] = bool(
                self.configs[LLMBackend.DEEPSEEK]["api_key"] and
                self.configs[LLMBackend.DEEPSEEK]["api_key"] != "your_deepseek_api_key_here"
            )
            self.backend_health[LLMBackend.QWEN] = bool(
                self.configs[LLMBackend.QWEN]["api_key"]
            )
            self.backend_health[LLMBackend.OPENAI] = bool(
                self.configs[LLMBackend.OPENAI]["api_key"]
            )

        self._backends_checked = True
        logger.info(f"后端健康状态: {[(k.value, v) for k, v in self.backend_health.items()]}")
    
    def switch_backend(self, backend: LLMBackend):
        """手动切换后端"""
        if self.backend_health.get(backend, False):
            self.current_backend = backend
            logger.info(f"已切换到后端: {backend}")
            return True
        return False
    
    def auto_switch_on_failure(self):
        """失败时自动切换到备用后端"""
        if not self.backend_health[self.current_backend]:
            for backend, healthy in self.backend_health.items():
                if healthy and backend != self.current_backend:
                    self.current_backend = backend
                    logger.warning(f"自动切换到备用后端: {backend}")
                    return True
        return False
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """统一生成接口，自动路由到当前后端"""

        # 首次调用时检查后端
        await self._check_backends()

        backend_config = self.configs[self.current_backend]

        if self.current_backend == LLMBackend.DEEPSEEK:
            async for chunk in self._call_openai_compatible(
                messages, temperature, max_tokens, stream, backend_config, "DeepSeek"
            ):
                yield chunk

        elif self.current_backend == LLMBackend.QWEN:
            async for chunk in self._call_openai_compatible(
                messages, temperature, max_tokens, stream, backend_config, "Qwen"
            ):
                yield chunk

        elif self.current_backend == LLMBackend.OPENAI:
            async for chunk in self._call_openai_compatible(
                messages, temperature, max_tokens, stream, backend_config, "OpenAI"
            ):
                yield chunk

        elif self.current_backend == LLMBackend.OLLAMA:
            async for chunk in self._call_ollama(
                messages, temperature, max_tokens, stream, backend_config
            ):
                yield chunk
    
    async def _call_openai_compatible(
        self, messages, temperature, max_tokens, stream, config, backend_name: str
    ):
        """调用OpenAI兼容的API (DeepSeek, Qwen, OpenAI)"""
        payload = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{config['base_url']}/chat/completions",
                    json=payload,
                    headers=config["headers"]()
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"{backend_name} API错误 ({response.status}): {error_text}")
                        raise Exception(f"{backend_name} API返回错误: {response.status}")

                    if stream:
                        async for line in response.content:
                            if line:
                                chunk = line.decode('utf-8').strip()
                                if chunk.startswith("data: "):
                                    if chunk == "data: [DONE]":
                                        break
                                    try:
                                        data = json.loads(chunk[6:])
                                        if "choices" in data and data["choices"]:
                                            delta = data["choices"][0].get("delta", {})
                                            if "content" in delta:
                                                yield delta["content"]
                                    except json.JSONDecodeError:
                                        continue
                    else:
                        data = await response.json()
                        if "choices" in data and data["choices"]:
                            yield data["choices"][0]["message"]["content"]
                        else:
                            logger.error(f"{backend_name}返回格式错误: {data}")
                            raise Exception(f"{backend_name}返回格式错误")

        except Exception as e:
            logger.error(f"{backend_name}调用失败: {e}")
            # 尝试自动切换到备用后端
            if self.auto_switch_on_failure():
                logger.info(f"切换到备用后端: {self.current_backend.value}")
                async for chunk in self.generate(messages, temperature, max_tokens, stream):
                    yield chunk
            else:
                raise Exception(f"{backend_name}调用失败且无可用备用后端: {e}")

    async def _call_ollama(self, messages, temperature, max_tokens, stream, config):
        """调用Ollama本地模型"""
        payload = {
            "model": config["model"],
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        try:
            timeout = aiohttp.ClientTimeout(total=180)  # Ollama需要更长时间
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{config['base_url']}/api/chat",
                    json=payload
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API错误 ({response.status}): {error_text}")
                        raise Exception(f"Ollama API返回错误: {response.status}")

                    if stream:
                        async for line in response.content:
                            if line:
                                chunk = line.decode('utf-8').strip()
                                try:
                                    data = json.loads(chunk)
                                    if data.get("done", False):
                                        break
                                    if "message" in data and "content" in data["message"]:
                                        yield data["message"]["content"]
                                except json.JSONDecodeError:
                                    continue
                    else:
                        data = await response.json()
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                        else:
                            logger.error(f"Ollama返回格式错误: {data}")
                            raise Exception("Ollama返回格式错误")

        except Exception as e:
            logger.error(f"Ollama调用失败: {e}")
            # 尝试自动切换到云端API
            if self.auto_switch_on_failure():
                logger.info(f"切换到备用后端: {self.current_backend.value}")
                async for chunk in self.generate(messages, temperature, max_tokens, stream):
                    yield chunk
            else:
                raise Exception(f"Ollama调用失败且无可用备用后端: {e}")
    
    async def generate_with_context(
        self,
        question: str,
        context: str,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """RAG专用接口"""

        if system_prompt is None:
            system_prompt = """请根据提供的参考信息回答问题。

参考信息如下：

{context}

请仔细分析以上信息，如果包含与问题相关的内容，请基于这些信息给出回答。可以适当总结、归纳，但不要编造信息中不存在的内容。

如果信息中确实没有相关内容，你可以说："根据提供的信息，没有找到直接相关的答案。"但请先仔细检查所有信息。"""

        messages = [
            {"role": "system", "content": system_prompt.format(context=context)},
            {"role": "user", "content": question}
        ]

        response = ""
        async for chunk in self.generate(messages, stream=False):
            response += chunk

        return {
            "success": True,
            "content": response,
            "backend": self.current_backend.value,
            "model": self.configs[self.current_backend]["model"]
        }

    def get_backend_info(self) -> Dict[str, Any]:
        """获取当前后端信息"""
        return {
            "current_backend": self.current_backend.value,
            "current_model": self.configs[self.current_backend]["model"],
            "available_backends": [
                {
                    "name": backend.value,
                    "model": self.configs[backend]["model"],
                    "healthy": self.backend_health.get(backend, False),
                    "api_key_configured": bool(self.configs[backend].get("api_key"))
                }
                for backend in LLMBackend
            ]
        }