#!/usr/bin/env python3
"""
Canonizer: Deterministically convert SpecDSL to baseline IAM policy.

This module takes a validated SpecDSL and produces a safe, idiomatic IAM policy
using well-defined transformation rules.
"""

from typing import Dict, Any, List, Optional
import uuid
try:
    from .policy_types import SpecDSL, Capability, Condition, MustNever, SERVICE_MODE_ACTIONS
except ImportError:
    from policy_types import SpecDSL, Capability, Condition, MustNever, SERVICE_MODE_ACTIONS


class Canonizer:
    """Converts SpecDSL to deterministic baseline IAM policy."""
    
    @staticmethod
    def canonize(spec: SpecDSL) -> Dict[str, Any]:
        """Convert SpecDSL to IAM policy JSON."""
        canonizer = Canonizer()
        return canonizer._build_policy(spec)
    
    def _build_policy(self, spec: SpecDSL) -> Dict[str, Any]:
        """Build complete IAM policy from SpecDSL."""
        statements = []
        
        # Process capabilities into Allow statements
        for capability in spec.capabilities:
            capability_statements = self._process_capability(capability)
            statements.extend(capability_statements)
        
        # Process must_never into Deny statements
        if spec.must_never:
            for must_never in spec.must_never:
                deny_statement = self._process_must_never(must_never)
                statements.append(deny_statement)
        
        # Build final policy
        policy = {
            "Version": "2012-10-17",
            "Statement": statements
        }
        
        return policy
    
    def _process_capability(self, capability: Capability) -> List[Dict[str, Any]]:
        """Convert a capability to one or more IAM statements."""
        # Get actions for this capability
        actions = self._get_capability_actions(capability)
        
        # Group by resource patterns for S3 optimization
        if capability.service == "s3":
            return self._process_s3_capability(capability, actions)
        else:
            return self._process_generic_capability(capability, actions)
    
    def _get_capability_actions(self, capability: Capability) -> List[str]:
        """Get the list of actions for a capability."""
        if capability.actions:
            return capability.actions
        elif capability.mode and capability.service in SERVICE_MODE_ACTIONS:
            return SERVICE_MODE_ACTIONS[capability.service].get(capability.mode, [])
        else:
            raise ValueError(f"Cannot determine actions for capability: {capability.name}")
    
    def _process_s3_capability(self, capability: Capability, actions: List[str]) -> List[Dict[str, Any]]:
        """Process S3 capability with bucket/object resource optimization."""
        statements = []
        
        # Separate bucket-level and object-level resources
        bucket_resources = [r for r in capability.resources if not r.endswith("/*")]
        object_resources = [r for r in capability.resources if r.endswith("/*")]
        
        # Bucket-level actions
        bucket_actions = [a for a in actions if self._is_bucket_level_action(a)]
        if bucket_actions and bucket_resources:
            stmt = {
                "Sid": f"Allow{capability.name.replace('_', '')}BucketLevel",
                "Effect": "Allow",
                "Action": bucket_actions,
                "Resource": bucket_resources
            }
            if capability.conditions:
                stmt["Condition"] = self._build_conditions_block(capability.conditions)
            statements.append(stmt)
        
        # Object-level actions
        object_actions = [a for a in actions if self._is_object_level_action(a)]
        if object_actions and object_resources:
            stmt = {
                "Sid": f"Allow{capability.name.replace('_', '')}ObjectLevel",
                "Effect": "Allow",
                "Action": object_actions,
                "Resource": object_resources
            }
            if capability.conditions:
                stmt["Condition"] = self._build_conditions_block(capability.conditions)
            statements.append(stmt)
        
        # Both bucket and object actions on same resources
        both_actions = [a for a in actions if not self._is_bucket_level_action(a) and not self._is_object_level_action(a)]
        if both_actions:
            stmt = {
                "Sid": f"Allow{capability.name.replace('_', '')}General",
                "Effect": "Allow",
                "Action": both_actions,
                "Resource": capability.resources
            }
            if capability.conditions:
                stmt["Condition"] = self._build_conditions_block(capability.conditions)
            statements.append(stmt)
        
        return statements
    
    def _process_generic_capability(self, capability: Capability, actions: List[str]) -> List[Dict[str, Any]]:
        """Process non-S3 capability as a single statement."""
        stmt = {
            "Sid": f"Allow{capability.name.replace('_', '')}",
            "Effect": "Allow",
            "Action": actions,
            "Resource": capability.resources
        }
        
        if capability.conditions:
            stmt["Condition"] = self._build_conditions_block(capability.conditions)
        
        return [stmt]
    
    def _is_bucket_level_action(self, action: str) -> bool:
        """Check if S3 action operates on bucket level."""
        bucket_actions = [
            "s3:ListBucket", "s3:GetBucketLocation", "s3:GetBucketVersioning",
            "s3:GetBucketAcl", "s3:GetBucketPolicy", "s3:GetBucketTagging",
            "s3:ListBucketVersions", "s3:ListBucketMultipartUploads"
        ]
        return action in bucket_actions
    
    def _is_object_level_action(self, action: str) -> bool:
        """Check if S3 action operates on object level."""
        object_actions = [
            "s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectVersion",
            "s3:DeleteObjectVersion", "s3:GetObjectAcl", "s3:PutObjectAcl",
            "s3:GetObjectTagging", "s3:PutObjectTagging", "s3:DeleteObjectTagging"
        ]
        return action in object_actions
    
    def _build_conditions_block(self, conditions: List[Condition]) -> Dict[str, Any]:
        """Build IAM Condition block from list of Condition objects."""
        condition_block = {}
        
        for condition in conditions:
            if condition.op not in condition_block:
                condition_block[condition.op] = {}
            
            condition_block[condition.op][condition.key] = condition.value
        
        return condition_block
    
    def _process_must_never(self, must_never: MustNever) -> Dict[str, Any]:
        """Convert MustNever to Deny statement."""
        return {
            "Sid": f"Deny{must_never.name.replace('_', '').replace(' ', '')}",
            "Effect": "Deny",
            "Action": must_never.actions,
            "Resource": must_never.resources
        }


# Predefined common policy patterns for quick canonization
class PolicyPatterns:
    """Common policy patterns for baseline generation."""
    
    @staticmethod
    def s3_read_only_pattern(bucket_name: str, include_kms: bool = False, 
                           kms_key_arn: Optional[str] = None,
                           vpc_endpoint: Optional[str] = None,
                           source_ip: Optional[str] = None) -> SpecDSL:
        """Generate SpecDSL for S3 read-only pattern."""
        try:
            from .policy_types import SpecDSL, Capability, Condition, MustNever, create_evidence
        except ImportError:
            from policy_types import SpecDSL, Capability, Condition, MustNever, create_evidence
        
        # Common conditions
        conditions = []
        
        # Always require HTTPS
        conditions.append(Condition(
            key="aws:SecureTransport",
            op="Bool",
            value="true",
            evidence=[create_evidence(
                doc_url="https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-securetransport",
                confidence=99,
                rationale="Enforce HTTPS for all requests"
            )]
        ))
        
        if source_ip:
            conditions.append(Condition(
                key="aws:SourceIp",
                op="IpAddress",
                value=source_ip,
                evidence=[create_evidence(
                    doc_url="https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-sourceip",
                    confidence=95,
                    rationale="Restrict access to specific IP range"
                )]
            ))
        
        if vpc_endpoint:
            conditions.append(Condition(
                key="aws:SourceVpce",
                op="StringEquals",
                value=vpc_endpoint,
                evidence=[create_evidence(
                    doc_url="https://docs.aws.amazon.com/vpc/latest/userguide/vpce-policy.html",
                    confidence=96,
                    rationale="Restrict access via VPC endpoint"
                )]
            ))
        
        # S3 read capability
        capabilities = [
            Capability(
                name="s3_read_bucket",
                service="s3",
                mode="read_only",
                resources=[
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                conditions=conditions,
                evidence=[
                    create_evidence(
                        doc_url="https://docs.aws.amazon.com/s3/latest/API/API_ListBucket.html",
                        confidence=100,
                        rationale="ListBucket needed to enumerate objects"
                    ),
                    create_evidence(
                        doc_url="https://docs.aws.amazon.com/s3/latest/API/API_GetObject.html",
                        confidence=100,
                        rationale="GetObject needed to fetch content"
                    )
                ]
            )
        ]
        
        # KMS capability if needed
        if include_kms and kms_key_arn:
            capabilities.append(
                Capability(
                    name="s3_kms_decrypt",
                    service="kms",
                    actions=["kms:Decrypt"],
                    resources=[kms_key_arn],
                    evidence=[create_evidence(
                        doc_url="https://docs.aws.amazon.com/kms/latest/developerguide/services-s3.html",
                        confidence=95,
                        rationale="Decrypt required for SSE-KMS objects"
                    )]
                )
            )
        
        # Explicit denials
        must_never = [
            MustNever(
                name="no_writes_deletes",
                actions=[
                    "s3:PutObject", "s3:PutObjectAcl", "s3:DeleteObject",
                    "s3:DeleteObjectVersion", "s3:PutBucketAcl", "s3:DeleteBucket",
                    "s3:DeleteBucketPolicy", "s3:PutBucketPolicy"
                ],
                resources=[
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                rationale="Read-only scope - block all write and delete operations"
            )
        ]
        
        return SpecDSL(
            who={"principal_ref": "<PRINCIPAL_ARN>"},
            scope={"accounts": ["<ACCOUNT>"], "regions": ["us-east-1"]},
            capabilities=capabilities,
            must_never=must_never,
            notes=[f"Read-only access to S3 bucket: {bucket_name}"]
        )


def validate_and_canonize(spec: SpecDSL) -> Dict[str, Any]:
    """Validate SpecDSL and canonize to IAM policy, raising errors if invalid."""
    try:
        from .policy_types import DSLValidator
    except ImportError:
        from policy_types import DSLValidator
    
    # Validate first
    errors = DSLValidator.validate(spec)
    if errors:
        raise ValueError(f"SpecDSL validation failed: {'; '.join(errors)}")
    
    # Canonize if valid
    return Canonizer.canonize(spec)
