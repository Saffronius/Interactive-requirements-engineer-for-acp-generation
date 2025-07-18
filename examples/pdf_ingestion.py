#!/usr/bin/env python3
"""
PDF Ingestion Tool for Vector Search
Extracts text from PDF documents, chunks it intelligently, and ingests into Pinecone.
"""

import os
import sys
import requests
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

try:
    import PyPDF2
except ImportError:
    print("❌ PyPDF2 not installed. Installing...")
    os.system("pip install PyPDF2")
    import PyPDF2

try:
    from sentence_transformers import SentenceTransformer
    import tiktoken
except ImportError:
    print("❌ Required packages not found. Installing...")
    os.system("pip install sentence-transformers tiktoken")
    from sentence_transformers import SentenceTransformer
    import tiktoken

class PDFProcessor:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        # Initialize tokenizer for chunking
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except:
            self.encoding = None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                print(f"📄 Processing {len(pdf_reader.pages)} pages...")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text += f"\n--- Page {page_num} ---\n{page_text}\n"
                        print(f"   ✅ Extracted page {page_num}")
                    except Exception as e:
                        print(f"   ⚠️  Error on page {page_num}: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
            return ""
        
        return text.strip()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks."""
        if not text.strip():
            return []
        
        # Split by paragraphs first, then by sentences if needed
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        current_size = 0
        chunk_id = 0
        
        for paragraph in paragraphs:
            paragraph_size = self.count_tokens(paragraph)
            
            # If paragraph is too long, split it further
            if paragraph_size > chunk_size:
                # If we have content in current chunk, save it
                if current_chunk.strip():
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": current_chunk.strip(),
                        "token_count": current_size
                    })
                    chunk_id += 1
                    current_chunk = ""
                    current_size = 0
                
                # Split long paragraph by sentences
                sentences = [s.strip() + '.' for s in paragraph.split('.') if s.strip()]
                
                for sentence in sentences:
                    sentence_size = self.count_tokens(sentence)
                    
                    if current_size + sentence_size > chunk_size and current_chunk.strip():
                        # Save current chunk
                        chunks.append({
                            "chunk_id": chunk_id,
                            "text": current_chunk.strip(),
                            "token_count": current_size
                        })
                        chunk_id += 1
                        
                        # Start new chunk with overlap
                        if overlap > 0 and chunks:
                            # Take last few sentences for overlap
                            overlap_text = ' '.join(current_chunk.split()[-overlap//4:])
                            current_chunk = overlap_text + ' ' + sentence
                            current_size = self.count_tokens(current_chunk)
                        else:
                            current_chunk = sentence
                            current_size = sentence_size
                    else:
                        current_chunk += ' ' + sentence
                        current_size += sentence_size
            
            # Normal paragraph processing
            elif current_size + paragraph_size > chunk_size and current_chunk.strip():
                # Save current chunk
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": current_chunk.strip(),
                    "token_count": current_size
                })
                chunk_id += 1
                
                # Start new chunk with overlap
                if overlap > 0 and chunks:
                    overlap_text = ' '.join(current_chunk.split()[-overlap//4:])
                    current_chunk = overlap_text + '\n\n' + paragraph
                    current_size = self.count_tokens(current_chunk)
                else:
                    current_chunk = paragraph
                    current_size = paragraph_size
            else:
                if current_chunk:
                    current_chunk += '\n\n' + paragraph
                else:
                    current_chunk = paragraph
                current_size += paragraph_size
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                "chunk_id": chunk_id,
                "text": current_chunk.strip(),
                "token_count": current_size
            })
        
        return chunks
    
    def prepare_documents(self, chunks: List[Dict], pdf_filename: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Prepare document objects for ingestion."""
        if metadata is None:
            metadata = {}
        
        documents = []
        file_hash = hashlib.md5(pdf_filename.encode()).hexdigest()[:8]
        
        for chunk in chunks:
            doc_id = f"{file_hash}_chunk_{chunk['chunk_id']}"
            
            doc_metadata = {
                "source_file": pdf_filename,
                "chunk_id": chunk['chunk_id'],
                "token_count": chunk['token_count'],
                "document_type": "pdf",
                **metadata
            }
            
            document = {
                "id": doc_id,
                "text": chunk['text'],
                "metadata": doc_metadata
            }
            
            documents.append(document)
        
        return documents
    
    def create_index_if_not_exists(self, index_name: str) -> bool:
        """Create index if it doesn't exist."""
        try:
            # Check if index exists
            response = requests.get(f"{self.api_base_url}/indexes")
            if response.status_code == 200:
                indexes = response.json().get('indexes', [])
                if index_name in indexes:
                    print(f"✅ Index '{index_name}' already exists")
                    return True
            
            # Create index
            print(f"🔨 Creating index '{index_name}'...")
            create_data = {
                "name": index_name,
                "metric": "cosine"
            }
            
            response = requests.post(
                f"{self.api_base_url}/indexes",
                json=create_data
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully created index '{index_name}'")
                return True
            else:
                print(f"❌ Error creating index: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Error checking/creating index: {e}")
            return False
    
    def ingest_documents(self, index_name: str, documents: List[Dict], namespace: str = "default") -> bool:
        """Ingest documents into the vector store."""
        try:
            print(f"📤 Uploading {len(documents)} documents to '{index_name}/{namespace}'...")
            
            # Use batch endpoint for better performance
            batch_data = {
                "index_name": index_name,
                "documents": documents,
                "batch_size": 50,
                "namespace": namespace
            }
            
            response = requests.post(
                f"{self.api_base_url}/indexes/{index_name}/documents/batch",
                json=batch_data
            )
            
            if response.status_code == 200:
                print("✅ Successfully started batch ingestion")
                return True
            else:
                # Try regular endpoint
                print("⚠️  Batch endpoint failed, trying regular upload...")
                response = requests.post(
                    f"{self.api_base_url}/indexes/{index_name}/documents?namespace={namespace}",
                    json=documents
                )
                
                if response.status_code == 200:
                    print("✅ Successfully uploaded documents")
                    return True
                else:
                    print(f"❌ Error uploading documents: {response.status_code}")
                    print(response.text)
                    return False
                    
        except Exception as e:
            print(f"❌ Error ingesting documents: {e}")
            return False
    
    def test_search(self, index_name: str, namespace: str = "default") -> bool:
        """Test search functionality with the uploaded documents."""
        try:
            print(f"\n🔍 Testing search in '{index_name}/{namespace}'...")
            
            search_data = {
                "query": "main topic summary",
                "top_k": 3,
                "namespace": namespace
            }
            
            response = requests.post(
                f"{self.api_base_url}/indexes/{index_name}/search/semantic",
                json=search_data
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                print(f"✅ Search successful! Found {len(results)} results")
                
                for i, result in enumerate(results[:2], 1):
                    print(f"\n   Result {i} (Score: {result.get('score', 0):.3f}):")
                    print(f"   {result.get('text', '')[:200]}...")
                
                return True
            else:
                print(f"❌ Search failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing search: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Ingest PDF documents into Pinecone vector database")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--index", default="documents", help="Index name (default: documents)")
    parser.add_argument("--namespace", default="default", help="Namespace (default: default)")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size in tokens (default: 1000)")
    parser.add_argument("--overlap", type=int, default=200, help="Chunk overlap in tokens (default: 200)")
    parser.add_argument("--metadata", help="Additional metadata as JSON string")
    
    args = parser.parse_args()
    
    # Validate PDF file
    if not os.path.exists(args.pdf_path):
        print(f"❌ PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    # Parse metadata
    metadata = {}
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            print("❌ Invalid metadata JSON format")
            sys.exit(1)
    
    print("📚 PDF Ingestion Tool")
    print("=" * 40)
    print(f"📄 PDF: {args.pdf_path}")
    print(f"🎯 Index: {args.index}")
    print(f"📂 Namespace: {args.namespace}")
    print(f"✂️  Chunk size: {args.chunk_size} tokens")
    print(f"🔄 Overlap: {args.overlap} tokens")
    
    processor = PDFProcessor()
    
    # Step 1: Extract text
    print(f"\n1️⃣ Extracting text from PDF...")
    text = processor.extract_text_from_pdf(args.pdf_path)
    
    if not text:
        print("❌ No text extracted from PDF")
        sys.exit(1)
    
    print(f"✅ Extracted {len(text)} characters")
    
    # Step 2: Chunk text
    print(f"\n2️⃣ Chunking text...")
    chunks = processor.chunk_text(text, args.chunk_size, args.overlap)
    print(f"✅ Created {len(chunks)} chunks")
    
    # Step 3: Prepare documents
    print(f"\n3️⃣ Preparing documents...")
    pdf_filename = os.path.basename(args.pdf_path)
    documents = processor.prepare_documents(chunks, pdf_filename, metadata)
    print(f"✅ Prepared {len(documents)} documents")
    
    # Step 4: Create index
    print(f"\n4️⃣ Setting up index...")
    if not processor.create_index_if_not_exists(args.index):
        print("❌ Failed to create/verify index")
        sys.exit(1)
    
    # Step 5: Ingest documents
    print(f"\n5️⃣ Ingesting documents...")
    if not processor.ingest_documents(args.index, documents, args.namespace):
        print("❌ Failed to ingest documents")
        sys.exit(1)
    
    # Step 6: Test search
    processor.test_search(args.index, args.namespace)
    
    print(f"\n🎉 PDF ingestion complete!")
    print(f"📋 Summary:")
    print(f"   📄 File: {pdf_filename}")
    print(f"   📊 Chunks: {len(chunks)}")
    print(f"   🎯 Index: {args.index}")
    print(f"   📂 Namespace: {args.namespace}")
    print(f"\n🔍 You can now search your PDF content using:")
    print(f"   curl -X POST 'http://localhost:8000/indexes/{args.index}/search/semantic' \\")
    print(f"     -H 'Content-Type: application/json' \\")
    print(f"     -d '{{\"query\": \"your search query\", \"top_k\": 5, \"namespace\": \"{args.namespace}\"}}'")

if __name__ == "__main__":
    main() 