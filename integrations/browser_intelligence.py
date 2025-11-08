"""
Browser Intelligence Layer - LLM-Powered Browser Automation
Gives the browser agent "eyes" and "brain" to understand context and make decisions
"""

import time
import base64
from typing import Dict, List, Optional, Any
from pathlib import Path
from rich.console import Console

console = Console()


class BrowserIntelligence:
    """
    LLM-powered browser intelligence that can:
    1. Analyze page state and understand what's visible
    2. Detect and handle modal overlays/dialogs automatically
    3. Make smart navigation decisions (which tabs to click, what to screenshot)
    4. Learn from evidence analysis to know what to collect
    """
    
    def __init__(self, llm, page):
        """
        Initialize browser intelligence
        
        Args:
            llm: ChatBedrock or LangChain LLM instance
            page: Playwright page object
        """
        self.llm = llm
        self.page = page
        self.context_memory = []  # Remember what we've done
        
    def analyze_page_state(self) -> Dict[str, Any]:
        """
        Use LLM to analyze current page state by taking screenshot and analyzing DOM
        Returns understanding of what's on screen
        """
        try:
            console.print("[cyan]🧠 Analyzing page state with LLM...[/cyan]")
            
            # Take screenshot for visual analysis
            screenshot_bytes = self.page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Get page title and URL
            page_title = self.page.title()
            page_url = self.page.url
            
            # Get visible interactive elements
            buttons = self.page.query_selector_all('button:visible, [role="button"]:visible')
            button_texts = [btn.inner_text()[:50] for btn in buttons[:20] if btn.is_visible()]
            
            tabs = self.page.query_selector_all('[role="tab"]:visible, .tab:visible, a[class*="tab"]:visible')
            tab_texts = [tab.inner_text()[:50] for tab in tabs[:15] if tab.is_visible()]
            
            links = self.page.query_selector_all('a:visible')
            link_texts = [link.inner_text()[:50] for link in links[:20] if link.is_visible() and link.inner_text()]
            
            # Detect modals/overlays
            modals = self.page.query_selector_all('[role="dialog"]:visible, .modal:visible, [class*="overlay"]:visible')
            has_modal = len(modals) > 0
            
            prompt = f"""You are analyzing a web page to help automate evidence collection.

**PAGE CONTEXT:**
- URL: {page_url}
- Title: {page_title}
- Has Modal/Overlay Open: {has_modal}

**VISIBLE ELEMENTS:**
Buttons: {button_texts[:10]}
Tabs: {tab_texts}
Links: {link_texts[:10]}

**SCREENSHOT:** (base64 image provided)

Please analyze and respond in JSON:
{{
  "page_type": "aws_console|sharepoint_list|sharepoint_preview|login|other",
  "current_state": "Brief description of what's on screen",
  "modal_or_overlay_open": true/false,
  "modal_close_method": "close_button|escape_key|click_outside|none",
  "available_tabs": ["tab1", "tab2"],
  "recommended_action": "close_modal|click_tab|take_screenshot|navigate|wait",
  "reasoning": "Why this action is recommended"
}}"""

            # Create message with image
            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                    }
                ]
            )
            
            response = self.llm.invoke([message])
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response (using same sanitization as evidence analyzer)
            import re
            import json
            
            cleaned = response_text.strip()
            cleaned = re.sub(r"```(?:json)?", "", cleaned)
            cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)
            
            json_match = re.search(r"(\{.*?\})", cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                analysis = json.loads(json_str)
            else:
                analysis = {
                    "page_type": "unknown",
                    "current_state": "Unable to parse",
                    "modal_or_overlay_open": has_modal,
                    "recommended_action": "wait"
                }
            
            console.print(f"[green]✓ Page State: {analysis.get('current_state', 'unknown')}[/green]")
            console.print(f"[dim]  Recommended: {analysis.get('recommended_action', 'wait')}[/dim]")
            
            return analysis
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Page analysis failed: {e}[/yellow]")
            return {
                "page_type": "unknown",
                "current_state": "Analysis failed",
                "modal_or_overlay_open": False,
                "recommended_action": "wait"
            }
    
    def auto_handle_modals(self) -> bool:
        """
        Automatically detect and close any modal/overlay that's blocking interaction
        Returns True if a modal was closed
        """
        try:
            # Common modal/overlay selectors
            modal_selectors = [
                '[role="dialog"]',
                '.modal',
                '[class*="overlay"]',
                '[class*="preview"]',
                '[data-automation-id*="dialog"]',
                '.ms-Dialog',
                '[class*="Modal"]'
            ]
            
            modal_found = False
            for selector in modal_selectors:
                modals = self.page.query_selector_all(f'{selector}:visible')
                if modals:
                    modal_found = True
                    console.print(f"[yellow]🔍 Modal detected: {selector}[/yellow]")
                    break
            
            if not modal_found:
                return False
            
            # Try to close it intelligently
            console.print("[cyan]🤖 Auto-handling modal...[/cyan]")
            
            # Method 1: Look for close button
            close_selectors = [
                'button[aria-label*="Close"]',
                'button[title*="Close"]',
                '[data-automation-id*="close"]',
                'button.ms-Dialog-button--close',
                '[role="dialog"] button[aria-label*="Close"]',
                '.modal button[aria-label*="Close"]',
                'button[class*="close"]',
                '[class*="close"][role="button"]'
            ]
            
            for close_sel in close_selectors:
                close_btn = self.page.query_selector(close_sel)
                if close_btn and close_btn.is_visible():
                    console.print(f"[green]✓ Clicking close button: {close_sel}[/green]")
                    close_btn.click()
                    time.sleep(0.5)
                    return True
            
            # Method 2: Press Escape key
            console.print("[dim]⌨️  Trying Escape key...[/dim]")
            self.page.keyboard.press('Escape')
            time.sleep(0.5)
            
            # Method 3: Click outside modal (backdrop)
            backdrop = self.page.query_selector('[class*="backdrop"]:visible, [class*="overlay"]:visible')
            if backdrop:
                console.print("[dim]🖱️  Clicking backdrop...[/dim]")
                backdrop.click()
                time.sleep(0.5)
            
            return True
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Modal handling failed: {e}[/yellow]")
            return False
    
    def smart_tab_navigation(self, evidence_context: Dict) -> List[str]:
        """
        Use LLM to determine which tabs to click based on evidence requirements
        
        Args:
            evidence_context: What evidence we're collecting (from previous year analysis)
        
        Returns:
            List of tab names/labels to click in order
        """
        try:
            console.print("[cyan]🧠 LLM deciding which tabs to navigate...[/cyan]")
            
            # Get all visible tabs
            tab_elements = self.page.query_selector_all('[role="tab"]:visible, .tab:visible, a[class*="tab"]:visible, button[class*="tab"]:visible')
            available_tabs = []
            for tab in tab_elements:
                if tab.is_visible():
                    tab_text = tab.inner_text().strip()
                    if tab_text and len(tab_text) < 100:
                        available_tabs.append(tab_text)
            
            if not available_tabs:
                console.print("[yellow]⚠️  No tabs found on page[/yellow]")
                return []
            
            console.print(f"[dim]  Available tabs: {available_tabs}[/dim]")
            
            # Ask LLM which tabs to click
            prompt = f"""You are helping collect audit evidence. Based on the evidence requirements, decide which tabs to click.

**EVIDENCE CONTEXT:**
{evidence_context}

**AVAILABLE TABS ON PAGE:**
{available_tabs}

**TASK:** 
Select which tabs to click and in what order to collect all required evidence.
For example, if collecting RDS cluster evidence, you might need:
- "Connectivity & security" tab
- "Configuration" tab
- "Maintenance & backups" tab

Respond in JSON:
{{
  "tabs_to_click": ["Tab Name 1", "Tab Name 2"],
  "reasoning": "Why these tabs are needed for this evidence"
}}

IMPORTANT: Only include tabs that are in the available tabs list above!"""

            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse response
            import re
            import json
            
            cleaned = response_text.strip()
            cleaned = re.sub(r"```(?:json)?", "", cleaned)
            cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)
            
            json_match = re.search(r"(\{.*?\})", cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                decision = json.loads(json_str)
                tabs_to_click = decision.get('tabs_to_click', [])
                
                console.print(f"[green]✓ LLM decided to click tabs: {tabs_to_click}[/green]")
                console.print(f"[dim]  Reasoning: {decision.get('reasoning', 'N/A')}[/dim]")
                
                return tabs_to_click
            else:
                console.print("[yellow]⚠️  Could not parse LLM tab decision[/yellow]")
                return []
                
        except Exception as e:
            console.print(f"[yellow]⚠️  Smart tab navigation failed: {e}[/yellow]")
            return []
    
    def click_tab_by_name(self, tab_name: str) -> bool:
        """
        Intelligently click a tab by name (fuzzy matching)
        """
        try:
            console.print(f"[cyan]🖱️  Looking for tab: {tab_name}[/cyan]")
            
            # Get all tab elements
            tab_elements = self.page.query_selector_all('[role="tab"], .tab, a[class*="tab"], button[class*="tab"]')
            
            # Find matching tab (case-insensitive, partial match)
            target_tab = None
            for tab in tab_elements:
                if not tab.is_visible():
                    continue
                tab_text = tab.inner_text().strip().lower()
                if tab_name.lower() in tab_text or tab_text in tab_name.lower():
                    target_tab = tab
                    break
            
            if not target_tab:
                # Try more aggressive matching
                for tab in tab_elements:
                    if not tab.is_visible():
                        continue
                    tab_text = tab.inner_text().strip().lower()
                    # Remove special chars and compare
                    clean_tab = ''.join(c for c in tab_text if c.isalnum())
                    clean_target = ''.join(c for c in tab_name.lower() if c.isalnum())
                    if clean_target in clean_tab or clean_tab in clean_target:
                        target_tab = tab
                        break
            
            if target_tab:
                console.print(f"[green]✓ Found and clicking tab: {target_tab.inner_text()}[/green]")
                target_tab.click()
                time.sleep(1.5)  # Wait for tab content to load
                
                # Auto-handle any modals that might have appeared
                self.auto_handle_modals()
                
                return True
            else:
                console.print(f"[yellow]⚠️  Tab not found: {tab_name}[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Tab click failed: {e}[/red]")
            return False
    
    def should_take_screenshot(self, evidence_requirements: Dict) -> Dict[str, Any]:
        """
        LLM decides if current page state matches evidence requirements
        Returns decision with confidence and filename suggestion
        """
        try:
            console.print("[cyan]🧠 LLM evaluating if screenshot is needed...[/cyan]")
            
            # Take screenshot for analysis
            screenshot_bytes = self.page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            page_title = self.page.title()
            page_url = self.page.url
            
            # Get visible text content (sample)
            body_text = self.page.query_selector('body')
            visible_text = body_text.inner_text()[:2000] if body_text else ""
            
            prompt = f"""You are evaluating if the current page view matches evidence requirements.

**CURRENT PAGE:**
- URL: {page_url}
- Title: {page_title}
- Visible Text (sample): {visible_text[:500]}

**EVIDENCE REQUIREMENTS:**
{evidence_requirements}

**SCREENSHOT:** (provided as image)

Analyze the screenshot and decide:
1. Does this page show the required evidence?
2. What should the screenshot filename be?
3. Confidence level (0-100%)

Respond in JSON:
{{
  "should_screenshot": true/false,
  "confidence": 85,
  "filename": "aws_rds_cluster_connectivity_us-east-1.png",
  "reasoning": "Page shows RDS cluster connectivity settings as required",
  "what_is_visible": "Brief description of what's on screen"
}}"""

            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                    }
                ]
            )
            
            response = self.llm.invoke([message])
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse decision
            import re
            import json
            
            cleaned = response_text.strip()
            cleaned = re.sub(r"```(?:json)?", "", cleaned)
            cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)
            
            json_match = re.search(r"(\{.*?\})", cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                decision = json.loads(json_str)
                
                console.print(f"[green]✓ LLM Decision: {'TAKE SCREENSHOT' if decision.get('should_screenshot') else 'SKIP'}[/green]")
                console.print(f"[dim]  Confidence: {decision.get('confidence', 0)}%[/dim]")
                console.print(f"[dim]  Reasoning: {decision.get('reasoning', 'N/A')}[/dim]")
                
                return decision
            else:
                return {"should_screenshot": False, "confidence": 0, "reasoning": "Parse failed"}
                
        except Exception as e:
            console.print(f"[yellow]⚠️  Screenshot decision failed: {e}[/yellow]")
            return {"should_screenshot": False, "confidence": 0, "reasoning": f"Error: {e}"}
    
    def remember_context(self, action: str, result: str):
        """Store context for learning and error recovery"""
        self.context_memory.append({
            "action": action,
            "result": result,
            "timestamp": time.time(),
            "url": self.page.url
        })
        
        # Keep only last 50 actions
        if len(self.context_memory) > 50:
            self.context_memory = self.context_memory[-50:]
    
    def get_error_recovery_suggestion(self, error: str) -> Dict[str, Any]:
        """
        LLM analyzes error and suggests recovery actions
        """
        try:
            console.print("[cyan]🧠 LLM analyzing error for recovery...[/cyan]")
            
            recent_actions = self.context_memory[-5:] if self.context_memory else []
            
            prompt = f"""You encountered an error during browser automation. Suggest recovery action.

**ERROR:** {error}

**RECENT ACTIONS:**
{recent_actions}

**CURRENT URL:** {self.page.url}

Suggest how to recover. Respond in JSON:
{{
  "recovery_action": "close_modal|retry|navigate_back|refresh|wait|skip",
  "wait_time": 2,
  "reasoning": "Why this recovery should work"
}}"""

            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            import re
            import json
            
            cleaned = response_text.strip()
            cleaned = re.sub(r"```(?:json)?", "", cleaned)
            cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)
            
            json_match = re.search(r"(\{.*?\})", cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                suggestion = json.loads(json_str)
                
                console.print(f"[green]✓ Recovery suggestion: {suggestion.get('recovery_action')}[/green]")
                return suggestion
            else:
                return {"recovery_action": "wait", "wait_time": 2}
                
        except Exception as e:
            console.print(f"[yellow]⚠️  Error recovery analysis failed: {e}[/yellow]")
            return {"recovery_action": "wait", "wait_time": 2}
