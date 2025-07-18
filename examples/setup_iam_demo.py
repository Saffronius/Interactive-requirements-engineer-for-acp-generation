#!/usr/bin/env python3
"""
Setup script to add sample IAM content to demo-index for testing the agent
"""

import requests
import json

API_BASE = "http://localhost:8000"

# Sample IAM-related documents for testing
SAMPLE_DOCS = [
    {
        "id": "iam-s3-policy-1",
        "text": "IAM S3 policies require specific actions like s3:GetObject, s3:PutObject, s3:DeleteObject. Resources should be specified as ARNs like arn:aws:s3:::bucket-name/* for bucket objects. Conditions can restrict access based on IP address using aws:SourceIp.",
        "metadata": {
            "service": "S3",
            "policy_type": "resource_based",
            "concepts": ["actions", "resources", "conditions"],
            "chunk_type": "fine_grained"
        }
    },
    {
        "id": "iam-s3-example-1", 
        "text": """Here's a complete S3 policy example for read-only access:
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-app-bucket",
        "arn:aws:s3:::my-app-bucket/*"
      ],
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": "203.0.113.0/24"
        }
      }
    }
  ]
}
This policy follows the principle of least privilege by only allowing read operations.""",
        "metadata": {
            "service": "S3",
            "policy_type": "complete_example",
            "actions": ["s3:GetObject", "s3:ListBucket"],
            "chunk_type": "contextual"
        }
    },
    {
        "id": "iam-ec2-policy-1",
        "text": "EC2 IAM policies commonly use actions like ec2:DescribeInstances, ec2:StartInstances, ec2:StopInstances. For production environments, restrict by region using aws:RequestedRegion condition and by instance tags using ec2:ResourceTag.",
        "metadata": {
            "service": "EC2",
            "policy_type": "resource_based", 
            "concepts": ["actions", "conditions", "tags"],
            "chunk_type": "fine_grained"
        }
    },
    {
        "id": "iam-policy-best-practices-1",
        "text": "IAM policy best practices: Use least privilege principle, specify explicit resources instead of wildcards, use conditions to restrict access, regularly review and rotate credentials, use IAM roles instead of users for applications.",
        "metadata": {
            "category": "best_practices",
            "topics": ["security", "least_privilege", "conditions"],
            "chunk_type": "fine_grained"
        }
    },
    {
        "id": "iam-missing-elements-guide-1", 
        "text": "Common missing elements in IAM policy requests: Specific AWS service actions (what operations?), Resource ARNs (which resources?), Conditions (when/where/who?), Principal (who has access?), Effect (Allow or Deny?). Vague requests like 'database access' need clarification on specific database service (RDS, DynamoDB), operations (read/write), and resources.",
        "metadata": {
            "category": "prompt_enhancement",
            "use_case": "policy_analysis",
            "chunk_type": "fine_grained"
        }
    }
]

def main():
    print("🚀 Setting up IAM demo content in demo-index...")
    
    # Check API status
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code != 200:
            print("❌ API not available. Please start the server first with: uvicorn src.api:app --reload")
            return
        print("✅ API is running")
    except:
        print("❌ Cannot connect to API. Please start the server first with: uvicorn src.api:app --reload")
        return
    
    # Ensure we're using Pinecone MCP for advanced features
    try:
        response = requests.post(f"{API_BASE}/config/switch-store?store_type=pinecone_mcp")
        if response.status_code == 200:
            print("✅ Using Pinecone MCP backend")
        else:
            print("⚠️  Warning: Could not switch to MCP backend")
    except:
        print("⚠️  Warning: Backend switch failed")
    
    # Upload documents to demo-index
    print(f"\n📤 Uploading {len(SAMPLE_DOCS)} IAM-related documents...")
    
    try:
        # Send documents as a direct list with namespace as query parameter
        response = requests.post(
            f"{API_BASE}/indexes/demo-index/documents?namespace=iam-demo", 
            json=SAMPLE_DOCS
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully uploaded documents")
            print(f"   Message: {result.get('message', 'Documents uploaded')}")
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return
    
    # Test search functionality
    print(f"\n🔍 Testing search functionality...")
    
    test_queries = [
        "S3 access policy",
        "EC2 permissions",
        "IAM best practices"
    ]
    
    for query in test_queries:
        try:
            search_data = {
                "query": query,
                "top_k": 2,
                "namespace": "iam-demo"
            }
            response = requests.post(f"{API_BASE}/indexes/demo-index/search/semantic", json=search_data)
            if response.status_code == 200:
                results = response.json().get("results", [])
                print(f"✅ Query '{query}': Found {len(results)} results")
                if results:
                    print(f"   Top result: {results[0].get('metadata', {}).get('text', '')[:80]}...")
            else:
                print(f"❌ Search failed for '{query}'")
        except Exception as e:
            print(f"❌ Search error for '{query}': {e}")
    
    print(f"\n🎉 Setup complete! You can now test the IAM Policy Agent:")
    print(f"   python examples/iam_policy_agent.py \"I need S3 access\"")

if __name__ == "__main__":
    main() 