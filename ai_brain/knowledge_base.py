"""
RAG Knowledge Base for Previous Audit Data
Allows agent to learn from past audits
"""

import os
import json
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime
from rich.console import Console

console = Console()

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class AuditKnowledgeBase:
    """
    Stores and retrieves previous audit knowledge using RAG
    Supports both vector database (ChromaDB) and fallback JSON storage
    """
    
    def __init__(self, persist_directory: str = "./knowledge_base"):
        self.persist_directory = Path(persist_directory).expanduser()
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings model if available
        if EMBEDDINGS_AVAILABLE:
            try:
                console.print("[cyan]🧠 Loading embeddings model (all-MiniLM-L6-v2)...[/cyan]")
                self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
                console.print("[green]✅ Embeddings loaded[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️  Embeddings failed: {e}. Using fallback.[/yellow]")
                self.embeddings = None
        else:
            console.print("[yellow]💡 Install sentence-transformers for better search: pip install sentence-transformers[/yellow]")
            self.embeddings = None
        
        # Initialize ChromaDB vector store if available
        if CHROMADB_AVAILABLE and self.embeddings:
            try:
                console.print("[cyan]🗄️  Initializing ChromaDB vector database...[/cyan]")
                self.client = chromadb.PersistentClient(
                    path=str(self.persist_directory / "chroma"),
                    settings=Settings(anonymized_telemetry=False)
                )
                self.collection = self.client.get_or_create_collection(
                    name="audit_knowledge",
                    metadata={"description": "Historical audit evidence and knowledge"}
                )
                self.vectorstore = True
                console.print(f"[green]✅ Vector database ready ({self.collection.count()} documents)[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️  ChromaDB failed: {e}. Using fallback JSON storage.[/yellow]")
                self.vectorstore = None
        else:
            if not CHROMADB_AVAILABLE:
                console.print("[yellow]💡 Install chromadb for vector search: pip install chromadb[/yellow]")
            self.vectorstore = None
        
        # Fallback JSON storage
        self.json_path = self.persist_directory / "knowledge.json"
        self._load_json()
    
    def _load_json(self):
        """Load JSON knowledge store"""
        if self.json_path.exists():
            with open(self.json_path, 'r') as f:
                self.knowledge = json.load(f)
        else:
            self.knowledge = {
                'documents': [],
                'evidence_records': [],
                'rfi_history': {}
            }
    
    def _save_json(self):
        """Save JSON knowledge store"""
        with open(self.json_path, 'w') as f:
            json.dump(self.knowledge, f, indent=2)
    
    def load_audit_data(self, audit_data_path: str):
        """
        Load previous audit data from directory
        Indexes all documents for semantic search
        """
        try:
            data_path = Path(audit_data_path).expanduser()
            
            if not data_path.exists():
                console.print(f"[red]❌ Path not found: {audit_data_path}[/red]")
                return False
            
            console.print(f"[cyan]📚 Loading audit data from: {data_path}...[/cyan]")
            
            documents = []
            
            # Recursively find all readable files
            for file_path in data_path.rglob('*'):
                if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.json', '.csv']:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            if len(content.strip()) > 0:
                                documents.append({
                                    'content': content,
                                    'source': str(file_path.relative_to(data_path)),
                                    'full_path': str(file_path),
                                    'timestamp': datetime.now().isoformat()
                                })
                    except Exception as e:
                        console.print(f"[dim]⚠️  Skipped {file_path.name}: {e}[/dim]")
            
            if not documents:
                console.print("[yellow]⚠️  No readable documents found[/yellow]")
                return False
            
            console.print(f"[cyan]📄 Found {len(documents)} documents, indexing...[/cyan]")
            
            # Use vector store if available
            if self.vectorstore and self.embeddings:
                for i, doc in enumerate(documents):
                    # Generate embedding
                    embedding = self.embeddings.encode(doc['content'][:1000]).tolist()  # Limit to first 1000 chars
                    
                    # Store in ChromaDB
                    self.collection.add(
                        embeddings=[embedding],
                        documents=[doc['content']],
                        metadatas=[{
                            'source': doc['source'],
                            'full_path': doc['full_path'],
                            'timestamp': doc['timestamp']
                        }],
                        ids=[f"doc_{i}_{int(datetime.now().timestamp() * 1000)}"]
                    )
                
                console.print(f"[green]✅ Indexed {len(documents)} documents in vector database[/green]")
            
            # Also save to JSON fallback
            self.knowledge['documents'].extend(documents)
            self._save_json()
            
            console.print(f"[green]✅ Loaded {len(documents)} documents into knowledge base[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error loading audit data: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query: str, k: int = 3) -> Optional[str]:
        """
        Search knowledge base for relevant previous audit information
        Returns: Relevant context string or None
        """
        try:
            if not query or not query.strip():
                return None
            
            # Use vector search if available
            if self.vectorstore and self.embeddings:
                console.print(f"[cyan]🔍 Searching knowledge base: '{query[:50]}...'[/cyan]")
                
                # Generate query embedding
                query_embedding = self.embeddings.encode(query).tolist()
                
                # Search ChromaDB
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k
                )
                
                if results['documents'] and len(results['documents'][0]) > 0:
                    console.print(f"[green]✅ Found {len(results['documents'][0])} relevant results[/green]")
                    
                    # Format as context
                    context = "\n\n---\n\n".join(results['documents'][0])
                    return context
                else:
                    console.print("[yellow]⚠️  No relevant results found[/yellow]")
                    return None
            
            # Fallback: Simple keyword search in JSON
            else:
                console.print(f"[cyan]🔍 Keyword search: '{query[:50]}...'[/cyan]")
                
                query_lower = query.lower()
                matching_docs = []
                
                for doc in self.knowledge.get('documents', []):
                    content = doc.get('content', '')
                    if query_lower in content.lower():
                        matching_docs.append(f"Source: {doc['source']}\n\n{content}")
                
                if matching_docs:
                    context = "\n\n---\n\n".join(matching_docs[:k])
                    console.print(f"[green]✅ Found {min(len(matching_docs), k)} matches[/green]")
                    return context
                else:
                    console.print("[yellow]⚠️  No matches found[/yellow]")
                    return None
        
        except Exception as e:
            console.print(f"[red]❌ Search error: {e}[/red]")
            return None
    
    def add_evidence_record(self, evidence_info: dict):
        """
        Add new evidence collection record to knowledge base
        Helps agent learn what evidence was collected when
        """
        try:
            record = {
                **evidence_info,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to JSON
            self.knowledge['evidence_records'].append(record)
            
            # Track by RFI code
            rfi_code = evidence_info.get('rfi_code')
            if rfi_code:
                if rfi_code not in self.knowledge['rfi_history']:
                    self.knowledge['rfi_history'][rfi_code] = []
                self.knowledge['rfi_history'][rfi_code].append(record)
            
            self._save_json()
            
            # Also add to vector store if available
            if self.vectorstore and self.embeddings:
                content = json.dumps(evidence_info, indent=2)
                embedding = self.embeddings.encode(content).tolist()
                
                self.collection.add(
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[record],
                    ids=[f"evidence_{int(datetime.now().timestamp() * 1000)}"]
                )
            
            console.print(f"[green]✅ Recorded evidence: {evidence_info.get('rfi_code', 'N/A')}[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ Error recording evidence: {e}[/red]")
    
    def get_rfi_history(self, rfi_code: str) -> List[Dict]:
        """Get all historical evidence for a specific RFI"""
        return self.knowledge.get('rfi_history', {}).get(rfi_code, [])
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        return {
            'total_documents': len(self.knowledge.get('documents', [])),
            'evidence_records': len(self.knowledge.get('evidence_records', [])),
            'rfis_tracked': len(self.knowledge.get('rfi_history', {})),
            'vector_store_enabled': bool(self.vectorstore),
            'embeddings_enabled': bool(self.embeddings)
        }
