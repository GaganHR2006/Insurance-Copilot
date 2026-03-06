"""
chat_memory.py — InsuranceChatbot: Conversational chatbot with sliding-window memory.
Uses LangChain ConversationChain backed by Groq LLM.
"""

import os
from typing import List

from dotenv import load_dotenv
from langchain_classic.chains import ConversationChain
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq

load_dotenv()


class InsuranceChatbot:
    """
    A conversational insurance assistant with rolling window memory.

    Maintains the last *k* = 10 conversation turns using
    ConversationBufferWindowMemory so the LLM always has recent context
    without ballooning the prompt size.
    """

    def __init__(self):
        """Initialise the Groq LLM, memory, and conversation chain."""
        api_key = os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=api_key,
            temperature=0.5,
        )
        self.memory = ConversationBufferWindowMemory(
            k=10,
            return_messages=False,
        )
        self.chain = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            verbose=False,
        )

    # ------------------------------------------------------------------
    def chat(self, user_message: str) -> str:
        """
        Send a message to the chatbot and receive a response.

        Memory is automatically maintained across calls; no explicit history
        management is required from the caller.

        Args:
            user_message: The user's question or statement.

        Returns:
            The assistant's response as a string.
        """
        try:
            response = self.chain.predict(input=user_message)
            return response
        except Exception as exc:
            return f"[ERROR] Chat failed: {exc}"

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Clear all conversation history and start fresh."""
        self.memory.clear()

    # ------------------------------------------------------------------
    def get_history(self) -> List[dict]:
        """
        Return the full conversation history as a list of message dicts.

        Returns:
            A list of dicts, each with 'role' ('human' or 'ai') and
            'content' keys.
        """
        messages = self.memory.chat_memory.messages
        history = []
        for msg in messages:
            role = "human" if msg.type == "human" else "ai"
            history.append({"role": role, "content": msg.content})
        return history
