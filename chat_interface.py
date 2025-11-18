"""
Interactive Chat Interface for AuditMate AI Agent
Provides a user-friendly terminal chat experience
"""

import os
import sys
import signal
import atexit
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai_brain.intelligent_agent import IntelligentAgent

console = Console()

# Global agent instance for cleanup
_agent_instance = None

def cleanup_handler(signum=None, frame=None):
    """Handle cleanup on exit/interrupt (for signals)"""
    global _agent_instance
    if _agent_instance:
        console.print("\n[cyan]🧹 Cleaning up resources...[/cyan]")
        try:
            _agent_instance.cleanup()
            console.print("[green]✅ Cleanup complete[/green]\n")
        except Exception as e:
            console.print(f"[yellow]⚠️  Cleanup warning: {e}[/yellow]\n")
    # Only exit if called from signal handler (not atexit)
    if signum is not None:
        sys.exit(0)

def atexit_cleanup_handler():
    """Handle cleanup on normal exit (no sys.exit call)"""
    global _agent_instance
    if _agent_instance:
        console.print("\n[cyan]🧹 Cleaning up resources...[/cyan]")
        try:
            _agent_instance.cleanup()
            console.print("[green]✅ Cleanup complete[/green]\n")
        except Exception as e:
            console.print(f"[yellow]⚠️  Cleanup warning: {e}[/yellow]\n")

# Register cleanup handlers
signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)
atexit.register(atexit_cleanup_handler)

def print_welcome():
    """Print welcome banner"""
    welcome_text = """
# 👋 Hi! I'm AuditMate

Your intelligent AI assistant for audit evidence collection, powered by Claude 3.5 Sonnet.

I can help you collect screenshots, export data, debug issues, and even generate new features on the fly. 
Just ask me anything - I'm here to make audit season easier!

💬 **Ask me:**
- "What can you do?"
- "Take a screenshot of RDS cluster X"
- "What evidence do I need for RFI BCR-06.01?"

Type **'help'** for commands or just start chatting naturally!
"""
    console.print(Panel(Markdown(welcome_text), title="AuditMate", border_style="cyan"))

def print_help():
    """Print help information"""
    help_text = """
## 💬 How to Talk to Me:

I understand natural language! Just ask me what you need. Here are some examples:

### 📸 Evidence Collection:
- "Take a screenshot of RDS cluster prod-xdr-01"
- "Export S3 bucket list to CSV for ctr-prod account"
- "Collect evidence for RFI BCR-06.01 under XDR Platform"
- "What evidence exists for this RFI from last year?"

### 📁 Evidence Management:
- **"review"** / **"show evidence"** - See what we've collected
- **"open folder"** / **"open evidence"** - Open evidence folder in Finder
- **"upload"** - Upload collected evidence to SharePoint FY2025

### 🔐 Authentication:
- "Refresh my AWS authentication"
- "Check my auth status"

### 💡 Questions & Help:
- "What can you do?"
- "How does this work?"
- "What AWS services do you support?"
- "Can you help me with [topic]?"
- "Why did [X] fail?"

### 🔧 Debugging & Fixes:
- Just paste any error and say "fix this"
- "Debug the screenshot issue"
- "Add support for DynamoDB"

### 🛠️ Utilities:
- **help** - Show this help
- **clear** - Clear conversation history
- **status** - Show agent status
- **quit** / **exit** - Exit the agent

### 📋 Typical Workflow:
1. Ask me to collect evidence (I save it locally first)
2. Type **"review"** to see what we collected
3. Type **"open evidence"** to review files yourself
4. Type **"upload"** when ready to push to SharePoint

**Remember:** You can ask me anything! I'm conversational like ChatGPT or Claude. 😊
"""
    console.print(Panel(Markdown(help_text), title="How to Use AuditMate", border_style="green"))

def main():
    """Main chat loop"""
    global _agent_instance
    
    # Load environment variables
    load_dotenv()
    
    # Print welcome
    print_welcome()
    
    # Initialize intelligent agent (uses Claude's function calling)
    console.print("\n[cyan]🔄 Initializing Intelligent Agent...[/cyan]")
    try:
        agent = IntelligentAgent()
        _agent_instance = agent  # Store for cleanup
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize: {e}[/red]")
        console.print(f"[yellow]Check your .env file configuration[/yellow]")
        sys.exit(1)
    
    # Initialize prompt session with history support
    history_file = os.path.join(os.path.dirname(__file__), '.chat_history')
    session = PromptSession(
        history=FileHistory(history_file),
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=True
    )
    
    # Show initial prompt
    console.print("[bold cyan]💬 How can I help you today?[/bold cyan]")
    console.print("[dim]💡 Tip: Use ↑/↓ arrow keys to navigate previous commands[/dim]")
    
    # Main chat loop
    while True:
        try:
            # Get user input with history support
            user_input = session.prompt("\n[You] > ", style='cyan bold')
            
            if not user_input.strip():
                continue
            
            # Handle special commands
            user_input_lower = user_input.lower().strip()
            
            if user_input_lower in ['quit', 'exit', 'q']:
                console.print("\n[yellow]👋 Goodbye![/yellow]\n")
                break
            
            elif user_input_lower == 'help':
                print_help()
                continue
            
            elif user_input_lower == 'clear':
                agent.clear_memory()
                console.clear()
                print_welcome()
                continue
            
            elif user_input_lower == 'clear history':
                # Clear command history file
                if os.path.exists(history_file):
                    os.remove(history_file)
                agent.clear_conversation_history()
                console.print("[green]✅ Chat history cleared[/green]")
                continue
            
            elif user_input_lower == 'show history':
                # Display recent conversation history
                history = agent.get_conversation_history()
                if not history:
                    console.print("[yellow]No conversation history yet[/yellow]")
                else:
                    console.print(f"\n[cyan]📜 Recent Conversation ({len(history)} exchanges):[/cyan]")
                    for i, exchange in enumerate(history[-10:], 1):
                        console.print(f"\n[bold]#{i}:[/bold]")
                        console.print(f"  [cyan]User:[/cyan] {exchange.get('user', '')[:100]}...")
                        console.print(f"  [green]Agent:[/green] {exchange.get('agent', '')[:100]}...")
                continue
            
            elif user_input_lower == 'status':
                console.print("\n[green]✅ Agent Status: Online[/green]")
                console.print(f"[cyan]Conversation turns: {len(agent.get_conversation_history())}[/cyan]")
                console.print(f"[cyan]Evidence directory: {agent.evidence_manager.evidence_dir}[/cyan]")
                continue
            
            elif user_input_lower == 'review' or user_input_lower == 'show evidence':
                # Show collected evidence
                agent.evidence_manager.display_evidence_summary()
                continue
            
            elif user_input_lower == 'open evidence' or user_input_lower == 'open folder':
                # Open evidence folder in Finder
                agent.evidence_manager.open_evidence_folder()
                continue
            
            elif user_input_lower == 'upload':
                # Trigger upload approval workflow
                if agent.evidence_manager.prompt_for_upload_approval():
                    console.print("[cyan]🔄 Initiating SharePoint upload...[/cyan]")
                    console.print("[yellow]⚠️  SharePoint upload integration pending implementation[/yellow]")
                continue
            
            # Process user request with agent
            response = agent.chat(user_input)
            
            # Display response
            console.print(f"\n[green]{response}[/green]\n")
        
        except KeyboardInterrupt:
            console.print("\n\n[yellow]👋 Interrupted. Goodbye![/yellow]\n")
            break
        
        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]\n")
            continue
    
    # Cleanup on exit
    try:
        console.print("\n[cyan]🧹 Cleaning up resources...[/cyan]")
        agent.cleanup()
        console.print("[green]✅ Cleanup complete[/green]\n")
    except Exception as e:
        console.print(f"[yellow]⚠️  Cleanup warning: {e}[/yellow]\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 Interrupted. Exiting...[/yellow]\n")
        sys.exit(0)

