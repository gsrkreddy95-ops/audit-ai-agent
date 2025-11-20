"""
Web Search Tool - Real-time Knowledge Retrieval

Enables the agent to search the web for current information about:
- AWS service behaviors (regional vs global, API limits, etc.)
- Jira/Confluence API documentation
- Error messages and troubleshooting
- Best practices and configurations
"""

import os
import json
from typing import Dict, List, Optional, Any
from rich.console import Console
import requests

console = Console()


class WebSearchTool:
    """
    Web search integration for real-time knowledge retrieval.
    
    Supports multiple search backends:
    - Perplexity API (recommended for technical queries)
    - Tavily API (good for general searches)
    - DuckDuckGo (fallback, no API key needed)
    """
    
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        
        # Try to load multiple search APIs
        self.perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        self.tavily_key = os.getenv('TAVILY_API_KEY')
        
        # Determine which backend to use
        if self.perplexity_key:
            self.backend = 'perplexity'
            console.print("[dim]🔍 Web search: Using Perplexity API[/dim]")
        elif self.tavily_key:
            self.backend = 'tavily'
            console.print("[dim]🔍 Web search: Using Tavily API[/dim]")
        else:
            self.backend = 'duckduckgo'
            console.print("[dim]🔍 Web search: Using DuckDuckGo (no API key)[/dim]")
    
    def search(
        self,
        query: str,
        focus_domains: Optional[List[str]] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search the web for current information.
        
        Args:
            query: Search query (e.g., "is AWS S3 regional or global service")
            focus_domains: Preferred domains (e.g., ["docs.aws.amazon.com", "atlassian.com"])
            max_results: Maximum number of results to return
            
        Returns:
            {
                "success": bool,
                "query": str,
                "results": [{"title": str, "url": str, "snippet": str, "relevance": float}],
                "answer": str (synthesized answer if available),
                "sources": [urls]
            }
        """
        console.print(f"[cyan]🔍 Searching web: {query}[/cyan]")
        
        try:
            if self.backend == 'perplexity':
                return self._search_perplexity(query, focus_domains, max_results)
            elif self.backend == 'tavily':
                return self._search_tavily(query, focus_domains, max_results)
            else:
                return self._search_duckduckgo(query, max_results)
        except Exception as e:
            console.print(f"[red]❌ Search error: {e}[/red]")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
                "sources": []
            }
    
    def _search_perplexity(
        self,
        query: str,
        focus_domains: Optional[List[str]],
        max_results: int
    ) -> Dict[str, Any]:
        """Search using Perplexity AI API (best for technical queries)"""
        url = "https://api.perplexity.ai/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.perplexity_key}",
            "Content-Type": "application/json"
        }
        
        # Build search-optimized prompt
        prompt = f"Search query: {query}\n\nProvide a concise answer with sources."
        if focus_domains:
            prompt += f"\n\nPrefer information from: {', '.join(focus_domains)}"
        
        payload = {
            "model": "llama-3.1-sonar-large-128k-online",  # Online search model
            "messages": [
                {"role": "system", "content": "You are a helpful search assistant. Provide accurate, cited answers."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1000
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Extract citations if available
        citations = data.get("citations", [])
        
        return {
            "success": True,
            "query": query,
            "answer": answer,
            "sources": citations[:max_results],
            "results": [{"title": "Perplexity Result", "snippet": answer, "url": url} for url in citations[:max_results]],
            "backend": "perplexity"
        }
    
    def _search_tavily(
        self,
        query: str,
        focus_domains: Optional[List[str]],
        max_results: int
    ) -> Dict[str, Any]:
        """Search using Tavily API"""
        url = "https://api.tavily.com/search"
        
        payload = {
            "api_key": self.tavily_key,
            "query": query,
            "search_depth": "advanced",
            "include_domains": focus_domains or [],
            "max_results": max_results
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
                "relevance": item.get("score", 0.0)
            })
        
        # Tavily provides a synthesized answer
        answer = data.get("answer", "")
        
        return {
            "success": True,
            "query": query,
            "answer": answer,
            "results": results,
            "sources": [r["url"] for r in results],
            "backend": "tavily"
        }
    
    def _search_duckduckgo(self, query: str, max_results: int) -> Dict[str, Any]:
        """Fallback search using DuckDuckGo (no API key required)"""
        try:
            from duckduckgo_search import DDGS
            
            ddgs = DDGS()
            results = []
            
            # Get search results
            search_results = ddgs.text(query, max_results=max_results)
            
            for item in search_results:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                    "relevance": 0.5  # DDG doesn't provide scores
                })
            
            # Synthesize answer from top results
            snippets = [r["snippet"] for r in results[:3]]
            answer = "\n\n".join(snippets) if snippets else "No answer found"
            
            return {
                "success": True,
                "query": query,
                "answer": answer,
                "results": results,
                "sources": [r["url"] for r in results],
                "backend": "duckduckgo"
            }
        except ImportError:
            console.print("[yellow]⚠️  DuckDuckGo search requires: pip install duckduckgo-search[/yellow]")
            return {
                "success": False,
                "error": "duckduckgo-search not installed",
                "query": query,
                "results": [],
                "sources": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
                "sources": []
            }
    
    def quick_lookup(self, query: str) -> str:
        """
        Quick answer for simple factual queries.
        Returns just the answer text (no metadata).
        """
        result = self.search(query, max_results=3)
        if result.get("success"):
            return result.get("answer", "No answer found")
        return f"Search failed: {result.get('error', 'Unknown error')}"


# Convenience function for tool executor
def web_search(
    query: str,
    focus_domains: Optional[List[str]] = None,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Search the web for real-time information.
    
    Args:
        query: What to search for
        focus_domains: Preferred websites/domains
        max_results: Number of results
        
    Returns:
        Search results with synthesized answer
    """
    searcher = WebSearchTool()
    return searcher.search(query, focus_domains, max_results)

