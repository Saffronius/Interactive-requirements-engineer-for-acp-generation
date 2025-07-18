#!/usr/bin/env python3
"""
Cleanup utility to remove test data from Pinecone indexes.
This script helps you clean up test documents before adding your real content.
"""

import requests
import json
from typing import List, Optional

class PineconeCleanup:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
    
    def get_current_status(self):
        """Get current backend and index information."""
        try:
            response = requests.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting status: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to API: {e}")
            return None
    
    def list_indexes(self):
        """List all available indexes."""
        try:
            response = requests.get(f"{self.api_base_url}/indexes")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error listing indexes: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to API: {e}")
            return None
    
    def delete_index(self, index_name: str):
        """Delete an entire index."""
        try:
            response = requests.delete(f"{self.api_base_url}/indexes/{index_name}")
            if response.status_code == 200:
                print(f"✅ Successfully deleted index: {index_name}")
                return True
            else:
                print(f"❌ Error deleting index {index_name}: {response.status_code}")
                print(response.text)
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error deleting index: {e}")
            return False
    
    def switch_backend(self, backend: str):
        """Switch to a specific backend."""
        try:
            response = requests.post(f"{self.api_base_url}/config/switch-store?store_type={backend}")
            if response.status_code == 200:
                print(f"✅ Switched to {backend} backend")
                return True
            else:
                print(f"❌ Error switching to {backend}: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error switching backend: {e}")
            return False

def main():
    print("🧹 Pinecone Data Cleanup Tool")
    print("=" * 40)
    
    cleanup = PineconeCleanup()
    
    # Check current status
    print("📊 Current Status:")
    status = cleanup.get_current_status()
    if status:
        print(f"   Backend: {status.get('store_type', 'unknown')}")
        print(f"   Indexes: {status.get('indexes', [])}")
    else:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   python -m src.api")
        return
    
    print("\n📋 Available Indexes:")
    indexes = cleanup.list_indexes()
    if indexes and 'indexes' in indexes:
        for idx in indexes['indexes']:
            print(f"   - {idx}")
    
    print("\n🎯 Cleanup Options:")
    print("1. Delete specific test indexes")
    print("2. Switch backends and clean each one")
    print("3. Exit")
    
    choice = input("\nChoose an option (1-3): ").strip()
    
    if choice == "1":
        # Delete specific indexes
        if indexes and 'indexes' in indexes:
            print("\nSelect indexes to delete:")
            for i, idx in enumerate(indexes['indexes'], 1):
                print(f"{i}. {idx}")
            
            selections = input("Enter index numbers to delete (comma-separated): ").strip()
            if selections:
                try:
                    selected_indices = [int(x.strip()) - 1 for x in selections.split(",")]
                    for idx_num in selected_indices:
                        if 0 <= idx_num < len(indexes['indexes']):
                            index_name = indexes['indexes'][idx_num]
                            confirm = input(f"Delete '{index_name}'? (y/N): ").strip().lower()
                            if confirm == 'y':
                                cleanup.delete_index(index_name)
                except ValueError:
                    print("Invalid selection format")
    
    elif choice == "2":
        # Clean all backends
        backends = ["pinecone", "pinecone_mcp"]
        
        for backend in backends:
            print(f"\n🔄 Switching to {backend} backend...")
            if cleanup.switch_backend(backend):
                status = cleanup.get_current_status()
                if status and status.get('indexes'):
                    print(f"Found indexes: {status['indexes']}")
                    for index_name in status['indexes']:
                        if 'test' in index_name.lower():
                            confirm = input(f"Delete test index '{index_name}'? (y/N): ").strip().lower()
                            if confirm == 'y':
                                cleanup.delete_index(index_name)
    
    elif choice == "3":
        print("👋 Goodbye!")
        return
    
    print("\n✨ Cleanup complete!")

if __name__ == "__main__":
    main() 