"""
OpenAI API integration with vision capabilities (GPT-4o).
"""

import base64
import json
import re
from typing import Any, Dict, List

from openai import OpenAI

from config import get_config


SYSTEM_PROMPT = """Ты — браузерный агент. Ты управляешь браузером, чтобы выполнить задачу пользователя.

На скриншоте интерактивные элементы помечены красными номерами в квадратных скобках.
Проанализируй скриншот и реши, какое действие выполнить дальше.

ВАЖНЫЕ ПРАВИЛА:
1. Используй ТОЛЬКО номера элементов, которые видишь на скриншоте
2. НЕ выдумывай элементы или номера
3. Если нужно перейти на сайт — используй goto
4. Если задача выполнена — используй done
5. Если нужна информация от пользователя — используй ask
6. Если страница загружается — используй wait
7. Перед кликом убедись, что элемент виден на скриншоте

Ответь ТОЛЬКО валидным JSON (без markdown, без ```):

Возможные действия:
{"action": "goto", "url": "https://example.com", "thought": "почему это делаю"}
{"action": "click", "element": 5, "thought": "кликаю на кнопку поиска"}
{"action": "type", "element": 3, "text": "текст для ввода", "thought": "ввожу поисковый запрос"}
{"action": "press", "key": "Enter", "thought": "нажимаю Enter для отправки формы"}
{"action": "scroll", "direction": "down", "thought": "скроллю чтобы увидеть больше"}
{"action": "wait", "thought": "жду загрузки страницы"}
{"action": "done", "result": "описание результата"}
{"action": "ask", "question": "вопрос пользователю"}

Поле "thought" обязательно для click, type, scroll, wait, goto, press — объясни свои действия.
После ввода текста в поле поиска — используй press Enter для отправки."""


class VisionClient:
    """OpenAI API client with vision support (GPT-4o)."""

    def __init__(self):
        config = get_config()
        self.client = OpenAI(api_key=config.api_key)
        self.model = config.model
        self.max_tokens = config.max_tokens

    def ask_claude(
        self,
        screenshot_b64: str,
        task: str,
        history: List[Dict[str, Any]],
        current_url: str,
        elements_text: str,
    ) -> Dict[str, Any]:
        """
        Send screenshot to GPT-4o and get next action.

        Args:
            screenshot_b64: Base64 encoded screenshot with markers
            task: User's task description
            history: List of previous actions
            current_url: Current page URL
            elements_text: Text description of elements

        Returns:
            Action dict with keys like 'action', 'element', 'text', etc.
        """
        # Build history text
        history_text = ""
        if history:
            history_text = "\n\nИстория действий:\n"
            for i, h in enumerate(history[-10:], 1):  # Last 10 actions
                action = h.get("action", "unknown")
                if action == "click":
                    history_text += f"{i}. Клик на элемент [{h.get('element')}]\n"
                elif action == "type":
                    history_text += f"{i}. Ввод текста '{h.get('text')}' в элемент [{h.get('element')}]\n"
                elif action == "goto":
                    history_text += f"{i}. Переход на {h.get('url')}\n"
                elif action == "scroll":
                    history_text += f"{i}. Скролл {h.get('direction')}\n"
                elif action == "press":
                    history_text += f"{i}. Нажатие клавиши {h.get('key', 'Enter')}\n"
                elif action == "wait":
                    history_text += f"{i}. Ожидание\n"

                # Add result if present
                if h.get("result"):
                    history_text += f"   Результат: {h.get('result')}\n"
                if h.get("error"):
                    history_text += f"   Ошибка: {h.get('error')}\n"

        # Build user message
        user_text = f"""Задача: {task}

Текущий URL: {current_url}
{history_text}
{elements_text}

Посмотри на скриншот и определи следующее действие."""

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{screenshot_b64}",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": user_text,
                        },
                    ],
                }
            ],
        )

        # Parse response
        response_text = response.choices[0].message.content.strip()

        # Try to extract JSON from response
        try:
            # First try direct parse
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in response (handle markdown code blocks)
            # Remove markdown code blocks if present
            cleaned = re.sub(r'```json\s*', '', response_text)
            cleaned = re.sub(r'```\s*', '', cleaned)

            try:
                return json.loads(cleaned.strip())
            except json.JSONDecodeError:
                # Try to find JSON object in text
                json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass

            # Return error action
            return {
                "action": "error",
                "error": f"Failed to parse GPT-4o response: {response_text[:200]}",
            }


def encode_image(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")
