#!/usr/bin/env python3
"""
Shared data contracts for IAM policy generation system.

This module defines the core types for:
- Evidence and provenance tracking
- Spec DSL for intent representation
- Read-back summaries for human review
"""

from typing import List, Dict, Any, Optional, Union, Literal
from dataclasses import dataclass, field
from datetime import datetime
import json
from enum import Enum


@dataclass
class Evidence:
    """One doc citation backing a single mapping decision."""
    doc_url: str                    # canonical URL (section anchor if possible)
    confidence: int                 # 0..100
    rationale: str                  # one line: "List objects requires ListBucket"
    retrieved_at: str               # ISO timestamp
    quote: Optional[str] = None     # <= 200 chars excerpt if allowed
    content_hash: Optional[str] = None  # optional


# Only safe, whitelisted condition operations
ConditionOp = Literal[
    "StringEquals", "StringLike", "IpAddress", 
    "DateEquals", "DateGreaterThan", "DateLessThan",
    "Bool", "NumericEquals", "NumericLessThan", "NumericGreaterThan"
]

@dataclass
class Condition:
    """Condition template (only safe, whitelisted ops)."""
    key: str                        # e.g., "aws:SourceIp", "ec2:ResourceTag/Project"
    op: ConditionOp
    value: Union[str, List[str]]    # scalar or list
    evidence: List[Evidence]


# Service capability modes
CapabilityMode = Literal["read_only", "write", "admin"]

@dataclass
class Capability:
    """A capability represents a logical permission grant."""
    name: str                       # human label, e.g., "s3_read_bucket"
    service: str                    # "s3", "ec2", ...
    resources: List[str]            # explicit ARNs or "*" (discourage "*")
    evidence: List[Evidence]        # why this capability exists
    
    # Either a coarse "mode" that compiler expands to a known action set, OR explicit actions
    mode: Optional[CapabilityMode] = None
    actions: Optional[List[str]] = None     # explicit AWS actions (use sparingly in v1)
    components: Optional[List[str]] = None  # service-specific coarse targets, e.g., ["objects","bucket"]
    conditions: Optional[List[Condition]] = None


@dataclass
class MustNever:
    """Explicit denials for security."""
    name: str
    actions: List[str]
    resources: List[str]
    rationale: str
    evidence: Optional[List[Evidence]] = None


@dataclass
class SpecDSL:
    """Limited spec DSL (intent baseline with provenance)."""
    version: str = "0.1"
    who: Dict[str, str] = field(default_factory=lambda: {"principal_ref": ""})  # bind at deploy time
    scope: Dict[str, List[str]] = field(default_factory=lambda: {"accounts": [], "regions": []})
    capabilities: List[Capability] = field(default_factory=list)
    must_never: Optional[List[MustNever]] = None
    notes: Optional[List[str]] = None


@dataclass
class ReadBack:
    """Human-readable summary of extracted intent."""
    summary: str                    # 2–5 sentences
    bullets: List[str]              # 5–10 concise bullets
    assumptions: List[str]          # unresolved placeholders, asks
    risk_callouts: List[str]        # things a reviewer should notice


@dataclass
class IntentExtractionResult:
    """Result of intent extraction process."""
    read_back: ReadBack
    spec_dsl: SpecDSL
    confidence_score: float         # overall confidence 0.0-1.0


@dataclass
class PolicyArtifacts:
    """Complete set of generated policy artifacts."""
    read_back: ReadBack
    spec_dsl: SpecDSL
    baseline_policy: Dict[str, Any]  # IAM policy JSON from canonizer
    candidate_policy: Dict[str, Any] # IAM policy JSON from LLM
    extraction_confidence: float
    generation_confidence: float


# Service-specific whitelisted condition keys
SERVICE_ALLOWED_CONDITIONS = {
    "s3": [
        "aws:SourceIp", "aws:SourceVpc", "aws:SourceVpce", "aws:SecureTransport",
        "aws:userid", "aws:username", "aws:PrincipalTag/*", "aws:RequestTag/*",
        "s3:prefix", "s3:delimiter", "s3:max-keys", "s3:ExistingObjectTag/*",
        "s3:x-amz-server-side-encryption", "s3:x-amz-server-side-encryption-aws-kms-key-id"
    ],
    "kms": [
        "aws:SourceIp", "aws:SourceVpc", "aws:SecureTransport", "aws:userid",
        "kms:ViaService", "kms:EncryptionContext:*", "kms:CallerAccount"
    ],
    "ec2": [
        "aws:SourceIp", "aws:SourceVpc", "aws:SecureTransport", "aws:userid",
        "ec2:Region", "ec2:ResourceTag/*", "ec2:Tenancy", "ec2:InstanceType"
    ]
}

# Service capability mode mappings
SERVICE_MODE_ACTIONS = {
    "s3": {
        "read_only": ["s3:ListBucket", "s3:GetObject", "s3:GetBucketLocation"],
        "write": ["s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
        "admin": ["s3:*"]
    },
    "kms": {
        "read_only": ["kms:Decrypt"],
        "write": ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey"],
        "admin": ["kms:*"]
    },
    "ec2": {
        "read_only": ["ec2:Describe*", "ec2:List*"],
        "write": ["ec2:Describe*", "ec2:List*", "ec2:RunInstances", "ec2:TerminateInstances"],
        "admin": ["ec2:*"]
    }
}


class DSLValidator:
    """Validates SpecDSL according to security rules."""
    
    @staticmethod
    def validate(spec: SpecDSL) -> List[str]:
        """Validate SpecDSL and return list of errors."""
        errors = []
        
        # Check version
        if spec.version != "0.1":
            errors.append(f"Unsupported DSL version: {spec.version}")
        
        # Validate capabilities
        for cap in spec.capabilities:
            # Check service is known
            if cap.service not in SERVICE_ALLOWED_CONDITIONS:
                errors.append(f"Unknown service in capability '{cap.name}': {cap.service}")
                continue
            
            # Either mode OR actions, not both
            if cap.mode and cap.actions:
                errors.append(f"Capability '{cap.name}' cannot have both mode and explicit actions")
            
            if not cap.mode and not cap.actions:
                errors.append(f"Capability '{cap.name}' must have either mode or explicit actions")
            
            # Check mode is valid
            if cap.mode and cap.mode not in ["read_only", "write", "admin"]:
                errors.append(f"Invalid mode in capability '{cap.name}': {cap.mode}")
            
            # Check resources not all wildcards (unless explicitly allowed)
            if all(r == "*" for r in cap.resources):
                errors.append(f"Capability '{cap.name}' uses wildcard resources - explicit ARNs required")
            
            # Validate conditions
            if cap.conditions:
                allowed_keys = SERVICE_ALLOWED_CONDITIONS[cap.service]
                for cond in cap.conditions:
                    # Check if condition key is allowed for this service
                    key_allowed = any(
                        cond.key == allowed_key or 
                        (allowed_key.endswith("/*") and cond.key.startswith(allowed_key[:-1]))
                        for allowed_key in allowed_keys
                    )
                    if not key_allowed:
                        errors.append(f"Condition key '{cond.key}' not allowed for service '{cap.service}'")
            
            # Check evidence confidence
            min_confidence = min((e.confidence for e in cap.evidence), default=0)
            if min_confidence < 80:
                errors.append(f"Capability '{cap.name}' has evidence with confidence < 80%")
        
        # Validate S3-specific rules
        for cap in spec.capabilities:
            if cap.service == "s3" and cap.mode == "read_only":
                # Require both bucket and object ARNs
                bucket_arns = [r for r in cap.resources if not r.endswith("/*")]
                object_arns = [r for r in cap.resources if r.endswith("/*")]
                
                if not bucket_arns:
                    errors.append(f"S3 read_only capability '{cap.name}' missing bucket-level ARN")
                if not object_arns:
                    errors.append(f"S3 read_only capability '{cap.name}' missing object-level ARN")
        
        return errors
    
    @staticmethod
    def is_valid(spec: SpecDSL) -> bool:
        """Check if SpecDSL is valid."""
        return len(DSLValidator.validate(spec)) == 0


def create_evidence(doc_url: str, confidence: int, rationale: str, quote: Optional[str] = None) -> Evidence:
    """Helper to create Evidence with current timestamp."""
    return Evidence(
        doc_url=doc_url,
        confidence=confidence,
        rationale=rationale,
        retrieved_at=datetime.now().isoformat(),
        quote=quote
    )


def spec_dsl_to_json(spec: SpecDSL) -> str:
    """Convert SpecDSL to JSON string."""
    def _convert_dataclass(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return {k: _convert_dataclass(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [_convert_dataclass(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: _convert_dataclass(v) for k, v in obj.items()}
        else:
            return obj
    
    return json.dumps(_convert_dataclass(spec), indent=2)


def json_to_spec_dsl(json_str: str) -> SpecDSL:
    """Convert JSON string to SpecDSL."""
    data = json.loads(json_str)
    
    def _build_evidence(evidence_data):
        return Evidence(**evidence_data)
    
    def _build_condition(cond_data):
        return Condition(
            key=cond_data["key"],
            op=cond_data["op"],
            value=cond_data["value"],
            evidence=[_build_evidence(e) for e in cond_data.get("evidence", [])]
        )
    
    def _build_capability(cap_data):
        return Capability(
            name=cap_data["name"],
            service=cap_data["service"],
            resources=cap_data["resources"],
            evidence=[_build_evidence(e) for e in cap_data["evidence"]],
            mode=cap_data.get("mode"),
            actions=cap_data.get("actions"),
            components=cap_data.get("components"),
            conditions=[_build_condition(c) for c in cap_data.get("conditions", [])]
        )
    
    def _build_must_never(mn_data):
        return MustNever(
            name=mn_data["name"],
            actions=mn_data["actions"],
            resources=mn_data["resources"],
            rationale=mn_data["rationale"],
            evidence=[_build_evidence(e) for e in mn_data.get("evidence", [])]
        )
    
    return SpecDSL(
        version=data.get("version", "0.1"),
        who=data.get("who", {"principal_ref": ""}),
        scope=data.get("scope", {"accounts": [], "regions": []}),
        capabilities=[_build_capability(c) for c in data.get("capabilities", [])],
        must_never=[_build_must_never(mn) for mn in data.get("must_never", [])] if data.get("must_never") else None,
        notes=data.get("notes")
    )
