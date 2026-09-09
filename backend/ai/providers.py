"""
Multi-Model AI Providers for DebugVerse.
Unifies streaming inference across:
  - AWS Bedrock (Claude 3.5 Sonnet / Claude 3.5 Haiku)
  - Google Gemini (Gemini 2.5 Flash)
Includes automatic fallback and health checking.
"""

from typing import AsyncGenerator, Dict, Any, Optional
import os
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

# Try importing boto3
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed; AWS Bedrock provider will be unavailable.")

# Try importing Google GenAI
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed; Gemini provider will be unavailable.")


from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

class BedrockClaudeProvider:
    """AWS Bedrock Provider for Anthropic Claude 3.5 models."""
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.session_token = os.getenv("AWS_SESSION_TOKEN")
        self._client = None
        self.is_configured = False
        self._init_client()

    def _init_client(self):
        if not BOTO3_AVAILABLE:
            return

        if not (self.access_key and self.secret_key):
            self.is_configured = False
            return

        try:
            session_kwargs = {
                "region_name": self.region,
                "aws_access_key_id": self.access_key,
                "aws_secret_access_key": self.secret_key,
            }
            if self.session_token:
                session_kwargs["aws_session_token"] = self.session_token

            session = boto3.Session(**session_kwargs)
            self._client = session.client("bedrock-runtime")
            self.is_configured = True
            logger.info("AWS Bedrock runtime client initialized successfully.")
        except Exception as e:
            logger.info(f"AWS Bedrock initialization failed: {e}")
            self.is_configured = False

    async def stream_generate(
        self,
        prompt: str,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Streams response from Claude via AWS Bedrock ConverseStream / InvokeModelStream."""
        if not self.is_configured or not self._client:
            raise RuntimeError("AWS Bedrock client is not configured with valid credentials.")

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        def _invoke():
            return self._client.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(payload),
                contentType="application/json",
                accept="application/json",
            )

        # Run blocking boto3 network call in threadpool
        response = await asyncio.to_thread(_invoke)
        event_stream = response.get("body")

        for event in event_stream:
            chunk = event.get("chunk")
            if chunk:
                data = json.loads(chunk.get("bytes").decode("utf-8"))
                if data.get("type") == "content_block_delta":
                    delta = data.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield delta.get("text", "")


class GeminiProvider:
    """Google Gemini Provider using google-genai SDK."""
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_id = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client = None
        self.is_configured = False
        self._init_client()

    def _init_client(self):
        if not GENAI_AVAILABLE or not self.api_key:
            return
        try:
            self._client = genai.Client(api_key=self.api_key)
            self.is_configured = True
            logger.info(f"Gemini client initialized with {self.model_id}.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.is_configured = False

    async def stream_generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        if not self.is_configured or not self._client:
            raise RuntimeError("Google Gemini client is not configured with a valid API key.")

        full_contents = prompt
        if system_prompt:
            full_contents = f"{system_prompt}\n\n---\n\n{prompt}"

        # Run native non-blocking async stream generator
        try:
            stream = await self._client.aio.models.generate_content_stream(
                model=self.model_id,
                contents=full_contents,
            )
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini async stream generation failed: {e}")
            raise


class AIProviderManager:
    """
    Unified manager that routes requests to Bedrock Claude or Gemini Flash
    with automatic failover.
    """
    def __init__(self):
        self.bedrock = BedrockClaudeProvider()
        self.gemini = GeminiProvider()

    def get_status(self) -> Dict[str, Any]:
        return {
            "bedrock": {
                "available": self.bedrock.is_configured,
                "region": self.bedrock.region,
                "models": [
                    "anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "anthropic.claude-3-5-haiku-20241022-v1:0",
                ],
            },
            "gemini": {
                "available": self.gemini.is_configured,
                "model": self.gemini.model_id,
            },
        }

    async def stream_debug(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_preference: str = "auto",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams debug analysis with model metadata and graceful fallback.
        Yields dicts with {"token": str, "model": str, "status": "streaming" | "done" | "error"}.
        """
        chosen_model = model_preference.lower().strip()
        active_model_name = "Gemini 2.5 Flash"

        # Check if user explicitly asked for Claude Bedrock or Auto
        use_bedrock = (
            chosen_model in ["claude-3-5-sonnet", "claude-3-5-haiku", "bedrock"]
            and self.bedrock.is_configured
        )

        if use_bedrock:
            bedrock_model_id = (
                "anthropic.claude-3-5-haiku-20241022-v1:0"
                if "haiku" in chosen_model
                else "anthropic.claude-3-5-sonnet-20241022-v2:0"
            )
            active_model_name = "Claude 3.5 Sonnet (AWS Bedrock)"
            try:
                async for token in self.bedrock.stream_generate(
                    prompt=prompt,
                    model_id=bedrock_model_id,
                    system_prompt=system_prompt,
                ):
                    yield {"token": token, "model": active_model_name, "status": "streaming"}
                yield {"token": "", "model": active_model_name, "status": "done"}
                return
            except Exception as e:
                logger.warning(f"Bedrock streaming failed ({e}), falling back to Gemini 2.5 Flash...")
                yield {
                    "token": f"> *Note: AWS Bedrock unavailable ({str(e)}). Auto-routed to Gemini 2.5 Flash.*\n\n",
                    "model": "Fallback to Gemini 2.5 Flash",
                    "status": "streaming",
                }

        # Fallback to Gemini 2.5 Flash
        active_model_name = "Gemini 2.5 Flash"
        try:
            async for token in self.gemini.stream_generate(prompt=prompt, system_prompt=system_prompt):
                yield {"token": token, "model": active_model_name, "status": "streaming"}
            yield {"token": "", "model": active_model_name, "status": "done"}
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            yield {
                "token": f"\n\n**AI Provider Error:** {str(e)}",
                "model": active_model_name,
                "status": "error",
            }


# Singleton instance
provider_manager = AIProviderManager()
