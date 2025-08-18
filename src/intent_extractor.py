#!/usr/bin/env python3
"""
Intent Extractor: Convert NL prompt + RAG context to SpecDSL + ReadBack.

This module replaces the "enhanced prompt" approach with structured intent extraction
that produces machine-readable SpecDSL with evidence and human-readable summaries.
"""

from typing import List, Dict, Any, Tuple, Optional
import re
import json
import os
from datetime import datetime
import openai

try:
    from .policy_types import (
        SpecDSL, ReadBack, Evidence, Capability, Condition, MustNever,
        IntentExtractionResult, create_evidence, SERVICE_ALLOWED_CONDITIONS,
        DSLValidator
    )
except ImportError:
    from policy_types import (
        SpecDSL, ReadBack, Evidence, Capability, Condition, MustNever,
        IntentExtractionResult, create_evidence, SERVICE_ALLOWED_CONDITIONS,
        DSLValidator
    )


class IntentExtractor:
    """Extracts structured intent from natural language with RAG context."""
    
    def __init__(self, openai_client: Optional[openai.OpenAI] = None):
        self.openai_client = openai_client
        self.guardrails_verbose = bool(os.getenv("INTENT_GUARDRAILS_VERBOSE", "1") != "0")
        
        # Common AWS services and their typical components
        self.service_patterns = {
            "s3": {
                "keywords": ["s3", "bucket", "object", "storage"],
                "components": ["bucket", "objects"],
                "modes": {
                    "read": ["read", "get", "download", "list", "view", "access"],
                    "write": ["write", "put", "upload", "create", "modify"],
                    "admin": ["admin", "manage", "full", "all"]
                }
            },
            "kms": {
                "keywords": ["kms", "encrypt", "decrypt", "key", "cipher"],
                "components": ["key"],
                "modes": {
                    "read": ["decrypt"],
                    "write": ["encrypt", "decrypt", "generate"],
                    "admin": ["manage", "admin", "full"]
                }
            },
            "ec2": {
                "keywords": ["ec2", "instance", "virtual machine", "vm", "compute"],
                "components": ["instances"],
                "modes": {
                    "read": ["read", "describe", "list", "view"],
                    "write": ["start", "stop", "create", "terminate", "launch"],
                    "admin": ["manage", "admin", "full"]
                }
            }
        }
    
    def extract_intent(self, nl_prompt: str, rag_context: List[Dict[str, Any]]) -> IntentExtractionResult:
        """
        Extract structured intent from natural language prompt using RAG context.
        
        Args:
            nl_prompt: Natural language prompt from user
            rag_context: Vector search results from documentation
            
        Returns:
            IntentExtractionResult with ReadBack and SpecDSL
        """
        # Parse basic intent from NL
        basic_intent = self._parse_basic_intent(nl_prompt)
        
        # Generate evidence from RAG context
        evidence_map = self._generate_evidence_from_rag(rag_context)
        
        # Use LLM for enhanced extraction if available
        if self.openai_client:
            return self._llm_enhanced_extraction(nl_prompt, rag_context, basic_intent, evidence_map)
        else:
            return self._rule_based_extraction(nl_prompt, basic_intent, evidence_map)
    
    def _parse_basic_intent(self, nl_prompt: str) -> Dict[str, Any]:
        """Parse basic intent using rule-based NLP."""
        intent = {
            "services": [],
            "actions": [],
            "mode": "read_only",  # default to safe mode
            "resources": [],
            "conditions": [],
            "confidence": 0.3
        }
        
        prompt_lower = nl_prompt.lower()
        
        # Detect services
        for service, patterns in self.service_patterns.items():
            if any(keyword in prompt_lower for keyword in patterns["keywords"]):
                intent["services"].append(service)
        
        # Detect mode based on action words
        for service in intent["services"]:
            if service in self.service_patterns:
                patterns = self.service_patterns[service]["modes"]
                
                # Check for admin/write first (more specific)
                if any(word in prompt_lower for word in patterns.get("admin", [])):
                    intent["mode"] = "admin"
                elif any(word in prompt_lower for word in patterns.get("write", [])):
                    intent["mode"] = "write"
                elif any(word in prompt_lower for word in patterns.get("read", [])):
                    intent["mode"] = "read_only"
        
        # Extract resource hints (bucket names, etc.)
        bucket_match = re.search(r'bucket[:\s]+([a-z0-9\-\.]+)', prompt_lower)
        if bucket_match:
            intent["resources"].append(f"s3_bucket:{bucket_match.group(1)}")
        
        # Detect security requirements
        if any(word in prompt_lower for word in ["secure", "https", "ssl", "tls"]):
            intent["conditions"].append("secure_transport")
        
        if any(word in prompt_lower for word in ["vpc", "vpce", "endpoint"]):
            intent["conditions"].append("vpc_restriction")
        
        if "ip" in prompt_lower or "network" in prompt_lower:
            intent["conditions"].append("ip_restriction")
        
        return intent
    
    def _generate_evidence_from_rag(self, rag_context: List[Dict[str, Any]]) -> Dict[str, List[Evidence]]:
        """Generate evidence objects from RAG search results."""
        evidence_map = {}
        
        for i, result in enumerate(rag_context):
            text = result.get("text", "")
            metadata = result.get("metadata", {})
            score = result.get("score", 0.0)
            
            # Extract actionable evidence
            evidence_items = []
            
            # Look for action mappings
            if "s3:ListBucket" in text:
                evidence_items.append(create_evidence(
                    doc_url=f"aws-iam-docs-chunk-{i}",
                    confidence=int(score * 100),
                    rationale="ListBucket required for bucket enumeration",
                    quote=text[:200]
                ))
            
            if "s3:GetObject" in text:
                evidence_items.append(create_evidence(
                    doc_url=f"aws-iam-docs-chunk-{i}",
                    confidence=int(score * 100),
                    rationale="GetObject required for object access",
                    quote=text[:200]
                ))
            
            # Look for condition evidence
            if "aws:SecureTransport" in text:
                evidence_items.append(create_evidence(
                    doc_url=f"aws-iam-docs-chunk-{i}",
                    confidence=int(score * 100),
                    rationale="SecureTransport enforces HTTPS",
                    quote=text[:200]
                ))
            
            # Look for security patterns
            if any(word in text.lower() for word in ["least privilege", "minimal", "read-only"]):
                evidence_items.append(create_evidence(
                    doc_url=f"aws-iam-docs-chunk-{i}",
                    confidence=int(score * 100),
                    rationale="Security best practice guidance",
                    quote=text[:200]
                ))
            
            # Store evidence by type
            for evidence in evidence_items:
                category = self._categorize_evidence(evidence.rationale)
                if category not in evidence_map:
                    evidence_map[category] = []
                evidence_map[category].append(evidence)
        
        return evidence_map
    
    def _categorize_evidence(self, rationale: str) -> str:
        """Categorize evidence by type."""
        rationale_lower = rationale.lower()
        
        if "listbucket" in rationale_lower:
            return "s3_list"
        elif "getobject" in rationale_lower:
            return "s3_get"
        elif "securetransport" in rationale_lower:
            return "secure_transport"
        elif "best practice" in rationale_lower:
            return "security"
        else:
            return "general"

    def _evidence_for_condition_key(self, key: str, evidence_map: Dict[str, List[Evidence]]) -> List[Evidence]:
        """Map an IAM condition key to the most relevant evidence bucket."""
        lk = key.lower()
        if "securetransport" in lk:
            return evidence_map.get("secure_transport", [])
        if "sourceip" in lk:
            # You create this category in _parse_basic_intent; fall back to general if empty
            return evidence_map.get("ip_restriction", []) or evidence_map.get("security", []) or evidence_map.get("general", [])
        if "sourcevpce" in lk or "sourcevpc" in lk:
            return evidence_map.get("vpc_restriction", []) or evidence_map.get("security", []) or evidence_map.get("general", [])
        return evidence_map.get("general", [])

    def _evidence_for_service(self, service: str, evidence_map: Dict[str, List[Evidence]]) -> List[Evidence]:
        """Attach service-specific evidence if available, with sensible fallbacks."""
        if service == "s3":
            evid = (evidence_map.get("s3_list", []) or []) + (evidence_map.get("s3_get", []) or [])
            return evid or evidence_map.get("security", []) or evidence_map.get("general", [])
        return evidence_map.get(service, []) or evidence_map.get("security", []) or evidence_map.get("general", [])
    
    def _llm_enhanced_extraction(
        self, 
        nl_prompt: str, 
        rag_context: List[Dict[str, Any]], 
        basic_intent: Dict[str, Any],
        evidence_map: Dict[str, List[Evidence]]
    ) -> IntentExtractionResult:
        """Use LLM for enhanced intent extraction."""
        
        # Prepare context for LLM
        context_text = self._prepare_rag_context_for_llm(rag_context)
        
        system_prompt = """You are an AWS IAM expert that extracts structured intent from natural language requests.

Your task is to analyze a user's IAM policy request and produce:
1. A structured representation of their intent (capabilities, conditions, restrictions)
2. A human-readable summary for review

Extract the following from the user's request:
- Which AWS services are involved (s3, kms, ec2, etc.)
- What mode of access (read_only, write, admin)
- Specific resources (bucket names, key ARNs, etc.)
- Security conditions (IP restrictions, VPC endpoints, HTTPS)
- What should be explicitly denied

Output your response as JSON with this structure:
{
  "capabilities": [
    {
      "name": "capability_name",
      "service": "s3|kms|ec2",
      "mode": "read_only|write|admin",
      "resources": ["arn:aws:..."],
      "conditions": [
        {"key": "aws:SecureTransport", "op": "Bool", "value": "true"}
      ]
    }
  ],
  "must_never": [
    {
      "name": "restriction_name", 
      "actions": ["s3:PutObject"],
      "resources": ["arn:aws:s3:::bucket/*"],
      "rationale": "reason"
    }
  ],
  "assumptions": ["placeholder values that need to be provided"],
  "confidence": 0.85
}"""

        user_prompt = f"""
USER REQUEST: "{nl_prompt}"

AWS DOCUMENTATION CONTEXT:
{context_text}

BASIC PARSED INTENT:
{json.dumps(basic_intent, indent=2)}

Extract structured intent from this IAM policy request. Focus on:
1. Specific AWS services and resources
2. Access patterns (read/write/admin)
3. Security constraints
4. What should be explicitly forbidden

Be conservative - default to read_only unless write access is clearly requested.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            # Parse LLM response
            llm_output = json.loads(response.choices[0].message.content)
            
            # Build SpecDSL from LLM output
            spec_dsl = self._build_spec_dsl_from_llm(llm_output, evidence_map)
            
            # Build ReadBack
            read_back = self._build_read_back_from_llm(llm_output, nl_prompt)
            
            # Apply guardrails
            read_back = self._augment_read_back_with_guardrails(read_back, spec_dsl, evidence_map, nl_prompt)
            
            return IntentExtractionResult(
                read_back=read_back,
                spec_dsl=spec_dsl,
                confidence_score=llm_output.get("confidence", 0.8)
            )
            
        except Exception as e:
            print(f"⚠️  LLM extraction failed: {e}")
            # Fallback to rule-based
            return self._rule_based_extraction(nl_prompt, basic_intent, evidence_map)
    
    def _rule_based_extraction(
        self, 
        nl_prompt: str, 
        basic_intent: Dict[str, Any],
        evidence_map: Dict[str, List[Evidence]]
    ) -> IntentExtractionResult:
        """Fallback rule-based extraction."""
        
        capabilities = []
        must_never = []
        assumptions = []
        
        # Build capabilities from basic intent
        for service in basic_intent.get("services", []):
            if service == "s3":
                # Default S3 read capability
                cap_name = f"s3_{basic_intent['mode']}"
                resources = ["arn:aws:s3:::BUCKET_NAME", "arn:aws:s3:::BUCKET_NAME/*"]
                
                # Extract bucket name if found
                for resource_hint in basic_intent.get("resources", []):
                    if resource_hint.startswith("s3_bucket:"):
                        bucket_name = resource_hint.split(":")[1]
                        resources = [f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"]
                        break
                else:
                    assumptions.append("S3 bucket name not specified")
                
                # Build conditions
                conditions = []
                if "secure_transport" in basic_intent.get("conditions", []):
                    conditions.append(Condition(
                        key="aws:SecureTransport",
                        op="Bool",
                        value="true",
                        evidence=evidence_map.get("secure_transport", [])
                    ))
                
                capabilities.append(Capability(
                    name=cap_name,
                    service="s3",
                    mode=basic_intent["mode"],
                    resources=resources,
                    conditions=conditions,
                    evidence=evidence_map.get("s3_list", []) + evidence_map.get("s3_get", [])
                ))
                
                # Add explicit denials for read-only
                if basic_intent["mode"] == "read_only":
                    must_never.append(MustNever(
                        name="no_s3_writes",
                        actions=["s3:PutObject", "s3:DeleteObject", "s3:PutBucketPolicy"],
                        resources=resources,
                        rationale="Read-only access - prevent write operations"
                    ))
        
        # Build assumptions
        if not basic_intent.get("services"):
            assumptions.append("No AWS services clearly identified")
        
        # Build ReadBack
        read_back = ReadBack(
            summary=f"Rule-based extraction identified {len(capabilities)} capabilities for {basic_intent.get('mode', 'unknown')} access to {', '.join(basic_intent.get('services', []))}.",
            bullets=[
                f"Service: {cap.service} ({cap.mode})" for cap in capabilities
            ] + [
                f"Restriction: {mn.name}" for mn in must_never
            ],
            assumptions=assumptions,
            risk_callouts=["Rule-based extraction has limited accuracy", "Manual review recommended"]
        )
        
        # Build SpecDSL
        spec_dsl = SpecDSL(
            who={"principal_ref": "PRINCIPAL_ARN"},
            scope={"accounts": ["ACCOUNT_ID"], "regions": ["us-east-1"]},
            capabilities=capabilities,
            must_never=must_never if must_never else None,
            notes=[f"Generated from: {nl_prompt}"]
        )
        
        # Apply guardrails
        read_back = self._augment_read_back_with_guardrails(read_back, spec_dsl, evidence_map, nl_prompt)
        
        return IntentExtractionResult(
            read_back=read_back,
            spec_dsl=spec_dsl,
            confidence_score=basic_intent.get("confidence", 0.3)
        )
    
    def _prepare_rag_context_for_llm(self, rag_context: List[Dict[str, Any]]) -> str:
        """Prepare RAG context for LLM consumption."""
        context_parts = []
        
        for i, result in enumerate(rag_context[:8], 1):  # Top 8 results
            text = result.get("text", "")
            score = result.get("score", 0)
            metadata = result.get("metadata", {})
            content_type = metadata.get("content_type", "")
            
            context_parts.append(f"--- Document {i} (Score: {score:.3f}, Type: {content_type}) ---")
            context_parts.append(text[:600])  # Limit length
        
        return "\n".join(context_parts)
    
    def _build_spec_dsl_from_llm(
        self, 
        llm_output: Dict[str, Any], 
        evidence_map: Dict[str, List[Evidence]]
    ) -> SpecDSL:
        """Build SpecDSL from LLM output with guardrails for missing fields."""
        
        capabilities: List[Capability] = []
        saw_s3_read_only = False
        s3_resources_for_deny: List[str] = []

        for cap_data in llm_output.get("capabilities", []):
            service = cap_data.get("service")
            mode = cap_data.get("mode") or "read_only"  # conservative default

            # Normalize resources with safe placeholders if missing/empty
            resources = cap_data.get("resources") or []
            if service == "s3" and (not resources or len(resources) == 0):
                resources = ["arn:aws:s3:::<BUCKET>", "arn:aws:s3:::<BUCKET>/*"]

            # Map condition evidence correctly
            conditions = []
            for cond_data in cap_data.get("conditions", []):
                conditions.append(Condition(
                    key=cond_data["key"],
                    op=cond_data["op"],
                    value=cond_data["value"],
                    evidence=self._evidence_for_condition_key(cond_data["key"], evidence_map),
                ))

            capabilities.append(Capability(
                name=cap_data.get("name", f"{service}_{mode}"),
                service=service,
                mode=mode,
                actions=cap_data.get("actions"),
                resources=resources,
                conditions=conditions,
                evidence=self._evidence_for_service(service, evidence_map),
            ))

            if service == "s3" and mode == "read_only":
                saw_s3_read_only = True
                s3_resources_for_deny = resources

        # Must-never: copy from LLM if present
        must_never: List[MustNever] = []
        for mn_data in llm_output.get("must_never", []):
            must_never.append(MustNever(
                name=mn_data["name"],
                actions=mn_data["actions"],
                resources=mn_data["resources"],
                rationale=mn_data["rationale"]
            ))

        # If LLM didn't provide denies but we have S3 read-only, synthesize a safe block
        if saw_s3_read_only and not must_never:
            must_never.append(MustNever(
                name="no_s3_writes_deletes",
                actions=[
                    "s3:PutObject", "s3:PutObjectAcl", "s3:DeleteObject",
                    "s3:DeleteObjectVersion", "s3:PutBucketAcl", "s3:DeleteBucket",
                    "s3:DeleteBucketPolicy", "s3:PutBucketPolicy"
                ],
                resources=s3_resources_for_deny,
                rationale="Read-only scope - block all write and delete operations"
            ))

        return SpecDSL(
            who={"principal_ref": "PRINCIPAL_ARN"},
            scope={"accounts": ["ACCOUNT_ID"], "regions": ["us-east-1"]},
            capabilities=capabilities,
            must_never=must_never if must_never else None
        )
    
    def _build_read_back_from_llm(self, llm_output: Dict[str, Any], nl_prompt: str) -> ReadBack:
        """Build ReadBack from LLM output."""
        
        capabilities = llm_output.get("capabilities", [])
        must_never = llm_output.get("must_never", [])
        assumptions = llm_output.get("assumptions", [])
        
        # Generate summary
        services = list(set(cap.get("service", "") for cap in capabilities))
        modes = list(set(cap.get("mode", "") for cap in capabilities))
        
        summary = f"Intent extracted: {', '.join(modes)} access to {', '.join(services)} services. "
        summary += f"Found {len(capabilities)} capabilities and {len(must_never)} restrictions."
        
        # Generate bullets
        bullets = []
        for cap in capabilities:
            mode_desc = cap.get("mode", "custom")
            service = cap.get("service", "unknown")
            bullets.append(f"{mode_desc.title()} access to {service}")
        
        for mn in must_never:
            bullets.append(f"Deny: {mn.get('rationale', mn.get('name', 'unnamed restriction'))}")
        
        # Risk callouts
        risk_callouts = []
        if any("*" in cap.get("resources", []) for cap in capabilities):
            risk_callouts.append("Wildcard resources detected - scope may be too broad")
        
        if not must_never:
            risk_callouts.append("No explicit restrictions - consider adding deny statements")
        
        confidence = llm_output.get("confidence", 0.5)
        if confidence < 0.9:
            risk_callouts.append(f"Extraction confidence {confidence:.0%} - manual review recommended")
        
        return ReadBack(
            summary=summary,
            bullets=bullets,
            assumptions=assumptions,
            risk_callouts=risk_callouts
        )
    
    def _augment_read_back_with_guardrails(
        self, 
        read_back: ReadBack, 
        spec_dsl: SpecDSL, 
        evidence_map: Dict[str, List[Evidence]], 
        nl_prompt: str
    ) -> ReadBack:
        """
        Augment ReadBack with comprehensive guardrails analysis.
        
        Detects missing placeholders, security issues, and evidence problems.
        """
        new_assumptions = list(read_back.assumptions) if read_back.assumptions else []
        new_risk_callouts = list(read_back.risk_callouts) if read_back.risk_callouts else []
        
        # A. Detect missing placeholders and add "Assumptions"
        if not spec_dsl.who.get("principal_ref") or "PRINCIPAL_ARN" in str(spec_dsl.who.get("principal_ref", "")):
            new_assumptions.append("Provide the exact principal ARN (who principal_ref).")
        
        if not spec_dsl.scope.get("accounts") or "ACCOUNT_ID" in str(spec_dsl.scope.get("accounts", [])):
            new_assumptions.append("Provide target AWS account ID(s).")
        
        if not spec_dsl.scope.get("regions"):
            new_assumptions.append("Confirm allowed AWS region(s).")
        
        # Check service-specific placeholders
        for cap in spec_dsl.capabilities:
            if cap.service == "s3":
                has_bucket_placeholder = any(
                    "BUCKET_NAME" in str(resource) or "<BUCKET>" in str(resource) 
                    for resource in cap.resources
                )
                if has_bucket_placeholder or not cap.resources:
                    new_assumptions.append("Provide the exact S3 bucket name(s) and object ARN(s).")
            
            elif cap.service == "kms":
                has_kms_placeholder = any(
                    "KMS_KEY_ARN" in str(resource) or "<KEY>" in str(resource)
                    for resource in cap.resources
                )
                if has_kms_placeholder:
                    new_assumptions.append("Provide the exact KMS key ARN(s).")
        
        # B. Lift validator warnings into assumptions/risk callouts
        try:
            validation_errors = DSLValidator.validate(spec_dsl)
            
            for msg in validation_errors:
                if "missing" in msg.lower() or "must have" in msg.lower():
                    new_assumptions.append(f"Validation: {msg}")
                elif "wildcard" in msg.lower() or "confidence < 80%" in msg.lower():
                    new_risk_callouts.append(f"Validation: {msg}")
                else:
                    new_risk_callouts.append(f"Validation: {msg}")
        except Exception as e:
            if self.guardrails_verbose:
                new_risk_callouts.append(f"Validation check failed: {e}")
        
        # C. Check security hardening and add "Risk Callouts"
        for cap in spec_dsl.capabilities:
            if cap.service == "s3" and cap.mode == "read_only":
                # Check for HTTPS enforcement
                has_secure_transport = any(
                    cond.key == "aws:SecureTransport" and cond.value == "true"
                    for cond in cap.conditions
                )
                if not has_secure_transport:
                    new_risk_callouts.append("HTTPS enforcement missing (aws:SecureTransport=true).")
                
                # Check for network restrictions
                has_network_restriction = any(
                    cond.key in ["aws:SourceIp", "aws:SourceVpc", "aws:SourceVpce"]
                    for cond in cap.conditions
                )
                if not has_network_restriction:
                    new_risk_callouts.append("No network restriction (IP/VPC) — consider narrowing blast radius.")
            
            # Check for wildcard resources
            has_wildcards = any(
                "*" in str(resource) and not self._is_reasonable_wildcard(resource)
                for resource in cap.resources
            )
            if has_wildcards:
                new_risk_callouts.append("Over-broad resource scope (wildcard).")
        
        # Check for missing deny statements
        s3_read_only_caps = [cap for cap in spec_dsl.capabilities if cap.service == "s3" and cap.mode == "read_only"]
        if s3_read_only_caps and (not spec_dsl.must_never or len(spec_dsl.must_never) == 0):
            new_risk_callouts.append("No explicit deny statements for write/delete.")
        
        # D. Evidence guardrails
        for cap in spec_dsl.capabilities:
            if not cap.evidence:
                new_risk_callouts.append(f"No evidence citations attached for {cap.name} — results may rely on heuristics.")
            else:
                min_confidence = min(e.confidence for e in cap.evidence)
                if min_confidence < 80:
                    new_risk_callouts.append(f"Evidence confidence below 80% for {cap.name}.")
        
        # Check for missing S3 action evidence
        has_s3_caps = any(cap.service == "s3" for cap in spec_dsl.capabilities)
        if has_s3_caps:
            s3_evidence_categories = ["s3_list", "s3_get"]
            missing_s3_evidence = all(
                not evidence_map.get(category) for category in s3_evidence_categories
            )
            if missing_s3_evidence:
                new_risk_callouts.append(
                    "RAG coverage for action-to-policy mappings looks thin — "
                    "ingest the Service Authorization Reference: Actions, resources and condition keys."
                )
        
        # E. S3 resource form sanity
        for cap in spec_dsl.capabilities:
            if cap.service == "s3" and cap.mode == "read_only":
                bucket_arns = [r for r in cap.resources if r.endswith(":::*") is False and "/*" not in r]
                object_arns = [r for r in cap.resources if "/*" in r]
                
                if not bucket_arns or not object_arns:
                    new_risk_callouts.append(
                        "S3 read requires both bucket ARN (arn:aws:s3:::bucket) and object ARN (arn:aws:s3:::bucket/*)."
                    )
        
        # F. Deduplicate and sort
        new_assumptions = sorted(list(set(new_assumptions)))
        new_risk_callouts = sorted(list(set(new_risk_callouts)))
        
        return ReadBack(
            summary=read_back.summary,
            bullets=read_back.bullets,
            assumptions=new_assumptions,
            risk_callouts=new_risk_callouts
        )
    
    def _is_reasonable_wildcard(self, resource: str) -> bool:
        """Check if a wildcard is reasonable (e.g., bucket/* is OK, * is not)."""
        if resource == "*":
            return False
        # Bucket-level wildcards for objects are reasonable
        if "arn:aws:s3:::" in resource and resource.endswith("/*"):
            return True
        return False
