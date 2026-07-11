import abc
import json
import math
import httpx
from typing import AsyncGenerator, Any
from app.core.config import settings
from app.utils.logger import logger

# -------------------------------------------------------------
# Base LLM Provider Interface
# -------------------------------------------------------------
class BaseLLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate_response(
        self, prompt: str, system_prompt: str | None = None, history: list[dict[str, str]] | None = None
    ) -> str:
        pass

    @abc.abstractmethod
    async def stream_response(
        self, prompt: str, system_prompt: str | None = None, history: list[dict[str, str]] | None = None
    ) -> AsyncGenerator[str, None]:
        pass

# -------------------------------------------------------------
# Mock LLM Provider for local development & testing
# -------------------------------------------------------------
class MockLLMProvider(BaseLLMProvider):
    async def generate_response(
        self, prompt: str, system_prompt: str | None = None, history: list[dict[str, str]] | None = None
    ) -> str:
        logger.info("Executing mock generate_response")
        return f"[Mock AI Model: {settings.LLM_MODEL}]\nYou asked: '{prompt}'.\nHere is a simulated response indicating your setup works. You can switch to 'openai' or 'anthropic' in your .env file."

    async def stream_response(
        self, prompt: str, system_prompt: str | None = None, history: list[dict[str, str]] | None = None
    ) -> AsyncGenerator[str, None]:
        logger.info("Executing mock stream_response")
        parts = [
            f"[Mock Streaming: {settings.LLM_MODEL}]\n",
            "This ", "is ", "a ", "simulated ", "streamed ", "response ",
            "from ", "the ", "Mock ", "LLM ", "Provider.\n\n",
            f"Prompt: '{prompt}'\n\n",
            "To connect to real APIs, configure your OpenAI or Anthropic API Keys in the .env file."
        ]
        for part in parts:
            yield part

# -------------------------------------------------------------
# OpenAI LLM Provider
# -------------------------------------------------------------
class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def _prepare_payload(self, prompt: str, system_prompt: str | None, history: list[dict[str, str]] | None, stream: bool) -> dict:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        return {
            "model": settings.LLM_MODEL if settings.LLM_MODEL else "gpt-4o-mini",
            "messages": messages,
            "stream": stream
        }

    async def generate_response(
        self, prompt: str, system_prompt: str | None = None, history: list[dict[str, str]] | None = None
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = self._prepare_payload(prompt, system_prompt, history, stream=False)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}")
                return f"Error communicating with OpenAI API: {e}"

    async def stream_response(
        self, prompt: str, system_prompt: str | None = None, history: list[dict[str, str]] | None = None
    ) -> AsyncGenerator[str, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = self._prepare_payload(prompt, system_prompt, history, stream=True)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                async with client.stream("POST", self.api_url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line or line.strip() == "":
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                continue
            except Exception as e:
                yield f"\n[Streaming Error: {e}]"

# -------------------------------------------------------------
# Anthropic LLM Provider
# -------------------------------------------------------------
class AnthropicLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"

    def _prepare_payload(self, prompt: str, system_prompt: str | None, history: list[dict[str, str]] | None, stream: bool) -> dict:
        messages = []
        if history:
            # Anthropic history maps to messages array format
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.LLM_MODEL if settings.LLM_MODEL else "claude-3-5-sonnet-20240620",
            "messages": messages,
            "max_tokens": 1024,
            "stream": stream
        }
        if system_prompt:
            payload["system"] = system_prompt
        return payload

    async def generate_response(
        self, prompt: str, system_prompt: str | None = None, history: list[dict[str, str]] | None = None
    ) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = self._prepare_payload(prompt, system_prompt, history, stream=False)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["content"][0]["text"]
            except Exception as e:
                logger.error(f"Anthropic API call failed: {e}")
                return f"Error communicating with Anthropic API: {e}"

    async def stream_response(
        self, prompt: str, system_prompt: str | None = None, history: list[dict[str, str]] | None = None
    ) -> AsyncGenerator[str, None]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = self._prepare_payload(prompt, system_prompt, history, stream=True)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                async with client.stream("POST", self.api_url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line or line.strip() == "":
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            try:
                                event = json.loads(data_str)
                                if event.get("type") == "content_block_delta":
                                    text = event["delta"].get("text", "")
                                    if text:
                                        yield text
                            except Exception:
                                continue
            except Exception as e:
                yield f"\n[Streaming Error: {e}]"

# -------------------------------------------------------------
# Memory Vector Database & RAG Service
# -------------------------------------------------------------
class InMemVectorDB:
    """
    In-memory vector database mock.
    Uses TF-IDF / term-matching representations for query cosine similarity simulation.
    """
    def __init__(self):
        # Format: {"text": str, "metadata": dict}
        self.documents = []

    def add_document(self, text: str, metadata: dict | None = None):
        self.documents.append({"text": text, "metadata": metadata or {}})

    def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        if not self.documents:
            return []
            
        # Simulating cosine similarity based on word overlap count
        query_words = set(query.lower().split())
        scored_docs = []
        for doc in self.documents:
            doc_words = set(doc["text"].lower().split())
            overlap = query_words.intersection(doc_words)
            # score = overlap count / sqrt(doc length * query length)
            score = len(overlap) / math.sqrt(max(len(doc_words), 1) * max(len(query_words), 1))
            scored_docs.append((score, doc))
            
        # Sort desc by score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:limit]]

# -------------------------------------------------------------
# AI Service Coordination Layer
# -------------------------------------------------------------
class AIService:
    def __init__(self):
        self.provider_name = settings.DEFAULT_LLM_PROVIDER
        self.vector_db = InMemVectorDB()
        self._init_provider()
        self._seed_vector_db()

    def _init_provider(self):
        if self.provider_name == "openai":
            self.provider = OpenAILLMProvider(settings.OPENAI_API_KEY)
        elif self.provider_name == "anthropic":
            self.provider = AnthropicLLMProvider(settings.ANTHROPIC_API_KEY)
        else:
            self.provider = MockLLMProvider()

    def _seed_vector_db(self):
        self.vector_db.add_document(
            "QualityHub test cases include title, module, priority, steps, expected result, and optional tags.",
            {"topic": "test_cases"},
        )
        self.vector_db.add_document(
            "Failed automated test runs can be ingested via POST /api/v1/test-runs with source set to automated.",
            {"topic": "automation"},
        )
        self.vector_db.add_document(
            "Release readiness shows coverage percentage, pass rate, and open defect count for a release.",
            {"topic": "releases"},
        )
        self.vector_db.add_document(
            "Defect statuses include open, triaged, fixed, verified, and closed.",
            {"topic": "defects"},
        )

    def get_prompt_template(self, role_description: str) -> str:
        templates = {
            "qa_engineer": "You are a senior QA engineer helping draft and review test cases for SecPod's security products.",
            "qa_lead": "You are a QA lead analyzing test coverage, defects, and release readiness.",
            "standard": "You are a helpful QA assistant for the QualityHub test management platform.",
        }
        return templates.get(role_description, templates["standard"])

    async def get_response_with_rag(self, prompt: str, system_prompt: str | None = None) -> str:
        # 1. Query vector db
        docs = self.vector_db.search(prompt, limit=2)
        
        # 2. Build augmented prompt
        context_str = "\n".join([f"- {d['text']}" for d in docs])
        augmented_system = (
            f"{system_prompt or 'You are an AI assistant.'}\n"
            f"Here is some relevant context that might help answer the user's question:\n"
            f"{context_str}\n"
            f"If the context is irrelevant, answer the user's question anyway using your default capabilities."
        )
        
        # 3. Request LLM
        return await self.provider.generate_response(prompt, system_prompt=augmented_system)

    async def stream_response_with_rag(self, prompt: str, system_prompt: str | None = None) -> AsyncGenerator[str, None]:
        docs = self.vector_db.search(prompt, limit=2)
        context_str = "\n".join([f"- {d['text']}" for d in docs])
        augmented_system = (
            f"{system_prompt or 'You are an AI assistant.'}\n"
            f"Here is some relevant context that might help answer the user's question:\n"
            f"{context_str}\n"
            f"If the context is irrelevant, answer the user's question anyway using your default capabilities."
        )
        
        async for chunk in self.provider.stream_response(prompt, system_prompt=augmented_system):
            yield chunk

    async def draft_test_case(self, requirement_text: str) -> dict:
        if len(requirement_text) > 2000:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="Requirement text exceeds 2000 characters limit.")
            
        system_prompt = (
            "You are a professional QA automation engineer. Convert the given requirement description "
            "into a structured draft test case. You must respond ONLY with a JSON object containing "
            "exactly two keys: 'draft_steps' (a list of step descriptions) and 'expected_result' (a string description "
            "of the expected behavior). Do not include markdown code block formatting or any other text outside the JSON."
        )
        
        prompt = f"Requirement: {requirement_text}"
        
        if isinstance(self.provider, MockLLMProvider):
            return {
                "draft_steps": [
                    "Navigate to the application login page.",
                    "Enter valid username and password credentials.",
                    "Click on the 'Login' submission button.",
                    "Verify the user is redirected to the main dashboard."
                ],
                "expected_result": "The user is logged in successfully and redirected to the dashboard."
            }
            
        response_str = await self.provider.generate_response(prompt, system_prompt=system_prompt)
        try:
            clean_str = response_str.strip()
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            clean_str = clean_str.strip()
            return json.loads(clean_str)
        except Exception as e:
            logger.error(f"Failed to parse LLM response as JSON: {response_str}. Error: {e}")
            return {
                "draft_steps": [f"Follow requirement: {requirement_text}"],
                "expected_result": "Satisfy the requirement successfully."
            }

    async def summarize_failures(self, failed_runs_logs: list[str]) -> dict:
        if not failed_runs_logs:
            return {
                "summary": "No failed runs found for this release.",
                "themes": []
            }
            
        system_prompt = (
            "You are a principal QA engineer analyzing automated test failure logs. "
            "Analyze the logs provided and summarize the recurring failure patterns/themes. "
            "You must respond ONLY with a JSON object containing exactly two keys: "
            "'summary' (a brief text summary of the overall failures) and 'themes' (a list of identified failure themes, "
            "such as 'Database connection timeouts' or 'UI element locator mismatch'). Do not include markdown code block formatting "
            "or any other text outside the JSON."
        )
        
        logs_joined = "\n---\n".join(failed_runs_logs[:20])
        prompt = f"Failure Logs:\n{logs_joined}"
        
        if isinstance(self.provider, MockLLMProvider):
            return {
                "summary": f"Analyzed {len(failed_runs_logs)} failures. Major causes relate to network timeouts and database lock failures.",
                "themes": [
                    "SQLite/PostgreSQL transaction lock contention during concurrent test executions.",
                    "UI element rendering delay causing Selenium timeouts on login button clicks.",
                    "API authentication token expiry during long-running end-to-end suites."
                ]
            }
            
        response_str = await self.provider.generate_response(prompt, system_prompt=system_prompt)
        try:
            clean_str = response_str.strip()
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            clean_str = clean_str.strip()
            return json.loads(clean_str)
        except Exception as e:
            logger.error(f"Failed to parse LLM failure summary response: {response_str}. Error: {e}")
            return {
                "summary": f"Failed to generate AI summary. Analyzed {len(failed_runs_logs)} logs.",
                "themes": ["Unable to determine failure patterns due to parsing errors."]
            }
