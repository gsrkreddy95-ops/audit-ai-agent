"""
Conversational Agent - General Q&A and Real-time Knowledge

Enables the agent to answer general questions using:
- LLM's built-in knowledge
- Real-time web search
- Synthesized responses combining both sources
"""

import json
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from ai_brain.web_search_tool import WebSearchTool
from ai_brain.knowledge_manager import KnowledgeManager

console = Console()


class ConversationalAgent:
    """
    Handles general questions and conversational interactions.
    
    Detects when user is asking general questions vs. requesting tool execution,
    and provides intelligent answers using LLM knowledge + web search.
    """
    
    def __init__(self, llm, knowledge_manager: Optional[KnowledgeManager] = None):
        """
        Initialize conversational agent.
        
        Args:
            llm: LLM instance (Claude, GPT, etc.)
            knowledge_manager: Knowledge manager for learned facts
        """
        self.llm = llm
        self.knowledge = knowledge_manager or KnowledgeManager()
        self.web_search = WebSearchTool()
        
        console.print("[bold cyan]💬 Conversational Agent Initialized[/bold cyan]")
        console.print("[dim]   General Q&A mode: ENABLED[/dim]")
        console.print("[dim]   Real-time knowledge: ENABLED[/dim]\n")
    
    def is_general_question(self, user_input: str) -> Dict[str, Any]:
        """
        Detect if user is asking a general question vs. requesting action.
        
        Args:
            user_input: User's input
            
        Returns:
            {
                "is_question": bool,
                "question_type": str,  # "factual", "how_to", "explanation", "comparison", etc.
                "requires_web_search": bool,
                "confidence": float
            }
        """
        question_indicators = [
            "what is", "what are", "what does", "what do",
            "how does", "how do", "how is", "how are",
            "why", "when", "where", "who",
            "explain", "describe", "tell me about",
            "is", "are", "can", "could", "should",
            "difference between", "compare", "vs", "versus"
        ]
        
        action_indicators = [
            "get", "fetch", "export", "download", "screenshot",
            "list", "show", "collect", "grab", "capture",
            "create", "generate", "make", "build"
        ]
        
        user_lower = user_input.lower()
        
        # Check for question patterns
        has_question = any(indicator in user_lower for indicator in question_indicators)
        has_action = any(indicator in user_lower for indicator in action_indicators)
        
        # Determine question type
        question_type = "factual"
        if "how" in user_lower:
            question_type = "how_to"
        elif "why" in user_lower:
            question_type = "explanation"
        elif any(word in user_lower for word in ["difference", "compare", "vs", "versus"]):
            question_type = "comparison"
        elif any(word in user_lower for word in ["explain", "describe", "tell me about"]):
            question_type = "explanation"
        
        # Determine if web search is needed
        requires_web_search = any(keyword in user_lower for keyword in [
            "current", "latest", "recent", "now", "today",
            "2025", "2024", "new", "updated", "changes",
            "best practice", "recommended", "should i"
        ])
        
        # Confidence score
        confidence = 0.8 if has_question and not has_action else 0.3
        
        return {
            "is_question": has_question and confidence > 0.5,
            "question_type": question_type,
            "requires_web_search": requires_web_search,
            "confidence": confidence
        }
    
    def answer_question(
        self,
        question: str,
        conversation_history: Optional[List[Dict]] = None,
        use_web_search: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a general question using LLM knowledge + web search.
        
        Args:
            question: User's question
            conversation_history: Recent conversation context
            use_web_search: Whether to search web for real-time data
            
        Returns:
            {
                "answer": str,
                "sources": [str],
                "confidence": float,
                "used_web_search": bool
            }
        """
        console.print(f"\n[bold cyan]💬 Answering question: {question}[/bold cyan]")
        
        # Step 1: Check knowledge base
        knowledge_context = self.knowledge.get_context_for_llm(limit=5)
        
        # Step 2: Search web if needed
        web_results = None
        if use_web_search:
            console.print("[cyan]🔍 Searching web for real-time information...[/cyan]")
            web_results = self.web_search.search(question, max_results=5)
        
        # Step 3: Synthesize answer using LLM
        answer = self._synthesize_answer(question, knowledge_context, web_results, conversation_history)
        
        # Extract sources
        sources = []
        if web_results and web_results.get("success"):
            sources = web_results.get("sources", [])
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": 0.9 if web_results and web_results.get("success") else 0.7,
            "used_web_search": web_results is not None and web_results.get("success")
        }
    
    def _synthesize_answer(
        self,
        question: str,
        knowledge_context: str,
        web_results: Optional[Dict[str, Any]],
        conversation_history: Optional[List[Dict]]
    ) -> str:
        """
        Synthesize answer from LLM knowledge + web search results.
        
        Args:
            question: User's question
            knowledge_context: Context from knowledge base
            web_results: Web search results
            conversation_history: Conversation history
            
        Returns:
            Synthesized answer
        """
        # Build prompt
        prompt_parts = [
            "You are an intelligent assistant helping users with technical questions.",
            "Answer the user's question using your knowledge and the provided information.",
            "",
            f"Question: {question}",
            ""
        ]
        
        # Add knowledge context
        if knowledge_context:
            prompt_parts.extend([
                "📚 Knowledge Base Context:",
                knowledge_context,
                ""
            ])
        
        # Add web search results
        if web_results and web_results.get("success"):
            answer = web_results.get("answer", "")
            results = web_results.get("results", [])
            sources = web_results.get("sources", [])
            
            prompt_parts.extend([
                "🌐 Real-time Web Search Results:",
                f"Answer from web: {answer}",
                ""
            ])
            
            if results:
                prompt_parts.append("Search Results:")
                for i, result in enumerate(results[:3], 1):
                    prompt_parts.append(f"{i}. {result.get('title', 'No title')}")
                    prompt_parts.append(f"   {result.get('snippet', '')[:200]}...")
                    prompt_parts.append(f"   Source: {result.get('url', '')}")
                    prompt_parts.append("")
            
            prompt_parts.extend([
                "Instructions:",
                "- Synthesize information from both your knowledge and web search results",
                "- Provide a clear, comprehensive answer",
                "- Cite sources when using web information",
                "- If web information contradicts your knowledge, prefer recent web information",
                "- Be conversational and helpful"
            ])
        else:
            prompt_parts.extend([
                "Instructions:",
                "- Use your knowledge to answer the question",
                "- Be conversational and helpful",
                "- If you're uncertain, say so and suggest searching for more information"
            ])
        
        # Add conversation context
        if conversation_history:
            recent_context = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')[:200]}"
                for msg in conversation_history[-3:]
            ])
            prompt_parts.extend([
                "",
                "📜 Recent Conversation:",
                recent_context
            ])
        
        prompt = "\n".join(prompt_parts)
        
        # Call LLM
        try:
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Format answer nicely
            if web_results and web_results.get("sources"):
                sources_text = "\n".join([
                    f"- {source}" for source in web_results.get("sources", [])[:3]
                ])
                answer += f"\n\n📚 Sources:\n{sources_text}"
            
            return answer
            
        except Exception as e:
            console.print(f"[red]❌ Failed to synthesize answer: {e}[/red]")
            if web_results and web_results.get("answer"):
                return web_results.get("answer", "I found some information but couldn't synthesize it properly.")
            return "I apologize, but I encountered an error while trying to answer your question. Could you rephrase it?"
    
    def process_conversational(self, user_input: str, conversation_history: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Process conversational input - answer questions or delegate to tools.
        
        Args:
            user_input: User's input
            conversation_history: Conversation history
            
        Returns:
            {
                "type": "answer" | "delegate",
                "response": str (if type is "answer"),
                "reason": str
            }
            or None if should proceed with normal tool flow
        """
        # Detect if this is a general question
        detection = self.is_general_question(user_input)
        
        if not detection["is_question"]:
            return None  # Not a question, proceed with normal flow
        
        console.print(f"[cyan]💬 Detected general question (type: {detection['question_type']})[/cyan]")
        
        # Answer the question
        answer_result = self.answer_question(
            user_input,
            conversation_history,
            use_web_search=detection["requires_web_search"]
        )
        
        return {
            "type": "answer",
            "response": answer_result["answer"],
            "sources": answer_result.get("sources", []),
            "used_web_search": answer_result.get("used_web_search", False),
            "reason": f"Detected {detection['question_type']} question"
        }

