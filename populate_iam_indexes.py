#!/usr/bin/env python3
"""
Script to populate IAM policy indexes with content from the AWS IAM User Guide PDF.
This implements the dual-chunking strategy: fine-grained and contextual chunks.
"""

import os
import json
import requests
import asyncio
from typing import List, Dict, Any
from pathlib import Path
import PyPDF2
from sentence_transformers import SentenceTransformer
import hashlib
import re
from datetime import datetime

class IAMPolicyIndexPopulator:
    def __init__(self, 
                 pdf_path: str = "/Users/zeitgeist/Downloads/iam-ug.pdf",
                 api_base_url: str = "http://localhost:8000"):
        self.pdf_path = pdf_path
        self.api_base_url = api_base_url
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Index configurations following our dual-chunking strategy
        self.fine_index_config = {
            "name": "iam-policy-guide-fine",
            "namespace": "aws-iam-detailed",
            "chunk_size": 400,
            "overlap": 80,
            "purpose": "term_discovery"
        }
        
        self.context_index_config = {
            "name": "iam-policy-guide-context", 
            "namespace": "aws-iam-examples",
            "chunk_size": 1200,
            "overlap": 200,
            "purpose": "context_examples"
        }
        
    def extract_text_from_pdf(self) -> str:
        """Extract text from the IAM User Guide PDF."""
        print(f"📖 Extracting text from {self.pdf_path}")
        
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        
        text = ""
        with open(self.pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"📄 PDF has {len(pdf_reader.pages)} pages")
            
            for i, page in enumerate(pdf_reader.pages):
                if i % 100 == 0:
                    print(f"   Processing page {i+1}/{len(pdf_reader.pages)}")
                
                page_text = page.extract_text()
                text += page_text + "\n"
        
        print(f"✅ Extracted {len(text)} characters from PDF")
        return text
    
    def chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Create chunks from text with specified size and overlap."""
        words = text.split()
        chunks = []
        
        start = 0
        chunk_id = 0
        
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            # Skip very short chunks
            if len(chunk_text.strip()) < 50:
                start = end - overlap
                continue
            
            # Create unique ID for chunk
            chunk_id += 1
            chunk_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:8]
            
            # Classify content type for metadata
            content_type = self.classify_content_type(chunk_text)
            
            chunks.append({
                "id": f"iam_chunk_{chunk_id}_{chunk_hash}",
                "text": chunk_text,
                "metadata": {
                    "source": "aws-iam-user-guide",
                    "content_type": content_type,
                    "chunk_size": len(chunk_words),
                    "chunk_id": chunk_id,
                    "timestamp": datetime.now().isoformat(),
                    "word_count": len(chunk_words),
                    "char_count": len(chunk_text)
                }
            })
            
            # Move to next chunk with overlap
            start = end - overlap
            if start >= len(words):
                break
        
        return chunks
    
    def classify_content_type(self, text: str) -> str:
        """Classify content type based on text patterns."""
        text_lower = text.lower()
        
        # Look for policy examples
        if any(keyword in text_lower for keyword in [
            '"version":', '"statement":', '"effect":', '"action":', '"resource":', 
            '"principal":', '"condition":', 'policy document', 'policy example'
        ]):
            return "policy_example"
        
        # Look for action lists
        if any(keyword in text_lower for keyword in [
            'actions:', 'permissions:', 'iam:', 's3:', 'ec2:', 'dynamodb:'
        ]):
            return "action_reference"
        
        # Look for condition keys
        if any(keyword in text_lower for keyword in [
            'condition key', 'condition element', 'aws:sourceip', 'aws:userid'
        ]):
            return "condition_reference"
        
        # Look for service documentation
        if any(keyword in text_lower for keyword in [
            'service-specific', 'service actions', 'resource types'
        ]):
            return "service_reference"
        
        # Look for best practices
        if any(keyword in text_lower for keyword in [
            'best practice', 'recommendation', 'security', 'least privilege'
        ]):
            return "best_practice"
        
        # Look for procedures/how-to
        if any(keyword in text_lower for keyword in [
            'to create', 'to attach', 'to modify', 'step 1', 'procedure'
        ]):
            return "procedure"
        
        return "general"
    
    def create_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create embeddings for chunks."""
        print(f"🔢 Creating embeddings for {len(chunks)} chunks")
        
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i].tolist()
        
        return chunks
    
    def upload_chunks_to_index(self, index_name: str, namespace: str, chunks: List[Dict[str, Any]]) -> bool:
        """Upload chunks to a specific index."""
        print(f"📤 Uploading {len(chunks)} chunks to {index_name} (namespace: {namespace})")
        
        try:
            # Upload in batches to avoid overwhelming the API
            batch_size = 50
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                print(f"   Uploading batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
                
                response = requests.post(
                    f"{self.api_base_url}/indexes/{index_name}/documents",
                    params={"namespace": namespace} if namespace else {},
                    json=batch,
                    timeout=60
                )
                
                if response.status_code != 200:
                    print(f"❌ Error uploading batch: {response.status_code}")
                    print(response.text)
                    return False
            
            print(f"✅ Successfully uploaded all chunks to {index_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading chunks: {e}")
            return False
    
    def populate_indexes(self):
        """Main method to populate both indexes with IAM content."""
        print("🚀 Starting IAM policy index population")
        print("=" * 60)
        
        # Extract text from PDF
        full_text = self.extract_text_from_pdf()
        
        # Create fine-grained chunks
        print("\n📋 Creating fine-grained chunks...")
        fine_chunks = self.chunk_text(
            full_text,
            self.fine_index_config["chunk_size"],
            self.fine_index_config["overlap"]
        )
        print(f"✅ Created {len(fine_chunks)} fine-grained chunks")
        
        # Create contextual chunks
        print("\n📋 Creating contextual chunks...")
        context_chunks = self.chunk_text(
            full_text,
            self.context_index_config["chunk_size"], 
            self.context_index_config["overlap"]
        )
        print(f"✅ Created {len(context_chunks)} contextual chunks")
        
        # Create embeddings for both sets
        fine_chunks_with_embeddings = self.create_embeddings(fine_chunks)
        context_chunks_with_embeddings = self.create_embeddings(context_chunks)
        
        # Upload to respective indexes
        print("\n📤 Uploading to indexes...")
        
        success_fine = self.upload_chunks_to_index(
            self.fine_index_config["name"],
            self.fine_index_config["namespace"],
            fine_chunks_with_embeddings
        )
        
        success_context = self.upload_chunks_to_index(
            self.context_index_config["name"],
            self.context_index_config["namespace"],
            context_chunks_with_embeddings
        )
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 POPULATION SUMMARY")
        print("=" * 60)
        print(f"Fine-grained index ({self.fine_index_config['name']}):")
        print(f"  ✅ Status: {'Success' if success_fine else 'Failed'}")
        print(f"  📊 Chunks: {len(fine_chunks_with_embeddings)}")
        print(f"  🎯 Purpose: Term discovery and prompt enhancement")
        print()
        print(f"Contextual index ({self.context_index_config['name']}):")
        print(f"  ✅ Status: {'Success' if success_context else 'Failed'}")
        print(f"  📊 Chunks: {len(context_chunks_with_embeddings)}")
        print(f"  🎯 Purpose: Policy examples and comprehensive guidance")
        print()
        
        if success_fine and success_context:
            print("🎉 IAM policy research agent is ready for use!")
            print("   The dual-index strategy has been successfully implemented.")
            print("   You can now run the IAM policy agent to enhance vague prompts.")
        else:
            print("❌ Some uploads failed. Please check the logs and retry.")
        
        return success_fine and success_context

def main():
    """Main function to run the population script."""
    populator = IAMPolicyIndexPopulator()
    
    # Check if PDF exists
    if not os.path.exists(populator.pdf_path):
        print(f"❌ PDF file not found: {populator.pdf_path}")
        print("Please ensure the AWS IAM User Guide PDF is at the specified path.")
        return
    
    # Check if API is accessible
    try:
        response = requests.get(f"{populator.api_base_url}/health")
        if response.status_code != 200:
            print(f"❌ API not accessible: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Run the population
    success = populator.populate_indexes()
    
    if success:
        print("\n🔍 Testing the populated indexes...")
        # Quick test search
        test_query = "create IAM policy for S3 access"
        print(f"   Query: '{test_query}'")
        
        try:
            response = requests.post(
                f"{populator.api_base_url}/indexes/iam-policy-guide-fine/search/semantic",
                json={"query": test_query, "top_k": 3}
            )
            if response.status_code == 200:
                results = response.json().get("results", [])
                print(f"   ✅ Found {len(results)} results in fine-grained index")
            else:
                print(f"   ⚠️  Search test failed: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Search test error: {e}")

if __name__ == "__main__":
    main() 