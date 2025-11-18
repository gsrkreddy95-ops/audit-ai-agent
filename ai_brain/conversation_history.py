"""
Conversation History Manager - Persistent chat history storage

Stores recent exchanges to provide context for follow-up questions
and enables arrow-key navigation through previous commands.
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from rich.console import Console

console = Console()


class ConversationHistory:
    """
    Manages persistent conversation history for the agent.
    
    Features:
    - Stores user/agent exchanges with timestamps
    - Auto-prunes to max_exchanges limit
    - Persists to JSON file (survives restarts)
    - Provides recent context for LLM injection
    """
    
    def __init__(self, max_exchanges: int = 20, history_file: Optional[str] = None):
        """
        Initialize conversation history manager.
        
        Args:
            max_exchanges: Maximum number of exchanges to keep (default: 20)
            history_file: Path to JSON history file (default: ./conversation_history.json)
        """
        self.max_exchanges = max_exchanges
        self.history_file = history_file or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'conversation_history.json'
        )
        self.exchanges: List[Dict[str, Any]] = []
        self._load_history()
    
    def _load_history(self) -> None:
        """Load history from file if it exists."""
        if not os.path.exists(self.history_file):
            return
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.exchanges = data.get('exchanges', [])
                # Trim to max if file has more
                if len(self.exchanges) > self.max_exchanges:
                    self.exchanges = self.exchanges[-self.max_exchanges:]
                console.print(f"[dim]📜 Loaded {len(self.exchanges)} previous exchanges[/dim]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not load history: {e}[/yellow]")
            self.exchanges = []
    
    def _save_history(self) -> None:
        """Persist history to file."""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'exchanges': self.exchanges
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not save history: {e}[/yellow]")
    
    def add_exchange(
        self,
        user_message: str,
        agent_response: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add a new user/agent exchange to history.
        
        Args:
            user_message: User's input
            agent_response: Agent's response
            tool_calls: Optional list of tools that were called
        """
        exchange = {
            'timestamp': datetime.now().isoformat(),
            'user': user_message,
            'agent': agent_response,
            'tool_calls': tool_calls or []
        }
        
        self.exchanges.append(exchange)
        
        # Auto-prune if exceeded max
        if len(self.exchanges) > self.max_exchanges:
            self.exchanges = self.exchanges[-self.max_exchanges:]
        
        # Persist to file
        self._save_history()
    
    def get_recent_exchanges(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the N most recent exchanges.
        
        Args:
            limit: Number of recent exchanges to return
            
        Returns:
            List of exchange dictionaries
        """
        return self.exchanges[-limit:] if self.exchanges else []
    
    def get_all_exchanges(self) -> List[Dict[str, Any]]:
        """Get all stored exchanges."""
        return self.exchanges.copy()
    
    def get_context_for_llm(self, limit: int = 3) -> str:
        """
        Format recent exchanges as context string for LLM injection.
        
        Args:
            limit: Number of recent exchanges to include
            
        Returns:
            Formatted context string
        """
        recent = self.get_recent_exchanges(limit)
        if not recent:
            return ""
        
        context_lines = ["Recent conversation context:"]
        for i, exchange in enumerate(recent, 1):
            user_msg = exchange.get('user', '')[:200]  # Truncate long messages
            agent_msg = exchange.get('agent', '')[:200]
            context_lines.append(f"\nExchange {i}:")
            context_lines.append(f"  User: {user_msg}")
            context_lines.append(f"  Agent: {agent_msg}")
            
            # Include tool calls if any
            tools = exchange.get('tool_calls', [])
            if tools:
                tool_names = [t.get('name', '?') for t in tools[:3]]
                context_lines.append(f"  Tools used: {', '.join(tool_names)}")
        
        return "\n".join(context_lines)
    
    def clear(self) -> None:
        """Clear all history (both memory and file)."""
        self.exchanges = []
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
        console.print("[green]✅ Conversation history cleared[/green]")
    
    def get_command_history(self) -> List[str]:
        """
        Extract just the user commands for arrow-key navigation.
        
        Returns:
            List of user command strings
        """
        return [exchange.get('user', '') for exchange in self.exchanges if exchange.get('user')]

