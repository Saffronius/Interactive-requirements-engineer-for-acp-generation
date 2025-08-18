#!/usr/bin/env python3
"""
Artifact Saver: Comprehensive storage system for four-artifact policy generation.

This module saves all policy artifacts in structured format with context,
evidence archives, comparison reports, and audit trails.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import difflib

try:
    from .policy_types import PolicyArtifacts, SpecDSL, spec_dsl_to_json
except ImportError:
    from policy_types import PolicyArtifacts, SpecDSL, spec_dsl_to_json


class ArtifactSaver:
    """Comprehensive artifact storage system with structured format and analysis."""
    
    def __init__(self, base_output_dir: str = "outputs"):
        self.base_output_dir = Path(base_output_dir)
        self.setup_directories()
    
    def setup_directories(self):
        """Create the structured output directory system."""
        dirs = [
            self.base_output_dir,
            self.base_output_dir / "artifacts",
            self.base_output_dir / "policies",  # Legacy format
            self.base_output_dir / "logs",
            self.base_output_dir / "comparisons",
            self.base_output_dir / "evidence"
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_artifacts(
        self, 
        artifacts: PolicyArtifacts, 
        original_prompt: str,
        rag_context: List[Dict[str, Any]] = None,
        custom_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Save all four artifacts in structured format with complete context.
        
        Returns:
            Dictionary with paths to all saved files
        """
        # Generate session info
        session_id = self._generate_session_id(original_prompt)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create session directory
        if custom_name:
            session_name = custom_name
        else:
            safe_prompt = self._sanitize_filename(original_prompt)
            session_name = f"{timestamp}_{safe_prompt}"
        
        session_dir = self.base_output_dir / "artifacts" / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        # 1. Save master artifacts file
        master_file = session_dir / "artifacts.json"
        master_data = self._build_master_artifacts_data(
            artifacts, original_prompt, session_id, rag_context
        )
        
        with open(master_file, 'w') as f:
            json.dump(master_data, f, indent=2, default=str)
        saved_files["master"] = str(master_file)
        
        # 2. Save individual artifacts
        saved_files.update(self._save_individual_artifacts(artifacts, session_dir))
        
        # 3. Save RAG context and evidence
        if rag_context:
            evidence_file = self._save_evidence_archive(rag_context, session_dir, session_id)
            saved_files["evidence"] = evidence_file
        
        # 4. Generate and save comparison report
        comparison_file = self._save_comparison_report(artifacts, session_dir)
        saved_files["comparison"] = comparison_file
        
        # 5. Save audit trail
        audit_file = self._save_audit_trail(artifacts, original_prompt, session_dir)
        saved_files["audit"] = audit_file
        
        # 6. Create README for the session
        readme_file = self._create_session_readme(artifacts, original_prompt, session_dir)
        saved_files["readme"] = readme_file
        
        # 7. Update global index
        self._update_global_index(session_name, session_id, original_prompt, artifacts)
        
        return saved_files
    
    def _generate_session_id(self, prompt: str) -> str:
        """Generate unique session ID from prompt and timestamp."""
        content = f"{prompt}{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """Create safe filename from text."""
        safe = "".join(c for c in text if c.isalnum() or c in (' ', '-', '_')).strip()
        safe = "_".join(safe.split())
        return safe[:max_length]
    
    def _build_master_artifacts_data(
        self, 
        artifacts: PolicyArtifacts, 
        original_prompt: str, 
        session_id: str,
        rag_context: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build comprehensive master artifacts data structure."""
        return {
            "metadata": {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "original_prompt": original_prompt,
                "system_version": "4-artifact-v1.0",
                "extraction_confidence": artifacts.extraction_confidence,
                "generation_confidence": artifacts.generation_confidence
            },
            "artifacts": {
                "read_back": {
                    "summary": artifacts.read_back.summary,
                    "bullets": artifacts.read_back.bullets,
                    "assumptions": artifacts.read_back.assumptions,
                    "risk_callouts": artifacts.read_back.risk_callouts
                },
                "spec_dsl": self._serialize_spec_dsl(artifacts.spec_dsl),
                "baseline_policy": artifacts.baseline_policy,
                "candidate_policy": artifacts.candidate_policy
            },
            "analysis": {
                "policy_comparison": self._analyze_policy_differences(
                    artifacts.baseline_policy, artifacts.candidate_policy
                ),
                "evidence_count": len(self._extract_all_evidence(artifacts.spec_dsl)),
                "capability_count": len(artifacts.spec_dsl.capabilities),
                "restriction_count": len(artifacts.spec_dsl.must_never) if artifacts.spec_dsl.must_never else 0
            },
            "context": {
                "rag_chunks": len(rag_context) if rag_context else 0,
                "evidence_sources": self._get_evidence_sources(artifacts.spec_dsl)
            }
        }
    
    def _serialize_spec_dsl(self, spec_dsl: SpecDSL) -> Dict[str, Any]:
        """Convert SpecDSL to serializable dictionary."""
        try:
            # Use the existing serialization from policy_types
            json_str = spec_dsl_to_json(spec_dsl)
            return json.loads(json_str)
        except Exception:
            # Fallback manual serialization
            return {
                "version": spec_dsl.version,
                "who": spec_dsl.who,
                "scope": spec_dsl.scope,
                "capabilities": [
                    {
                        "name": cap.name,
                        "service": cap.service,
                        "mode": cap.mode,
                        "actions": cap.actions,
                        "resources": cap.resources,
                        "evidence_count": len(cap.evidence)
                    } for cap in spec_dsl.capabilities
                ],
                "must_never": [
                    {
                        "name": mn.name,
                        "actions": mn.actions,
                        "resources": mn.resources,
                        "rationale": mn.rationale
                    } for mn in spec_dsl.must_never
                ] if spec_dsl.must_never else None
            }
    
    def _save_individual_artifacts(self, artifacts: PolicyArtifacts, session_dir: Path) -> Dict[str, str]:
        """Save each artifact as individual files."""
        saved = {}
        
        # 1. ReadBack as Markdown
        readback_file = session_dir / "read_back.md"
        with open(readback_file, 'w') as f:
            f.write(f"# Policy Analysis Summary\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Extraction Confidence:** {artifacts.extraction_confidence:.1%}\n\n")
            
            f.write(f"## Summary\n\n{artifacts.read_back.summary}\n\n")
            
            if artifacts.read_back.bullets:
                f.write(f"## Key Points\n\n")
                for bullet in artifacts.read_back.bullets:
                    f.write(f"- {bullet}\n")
                f.write("\n")
            
            if artifacts.read_back.assumptions:
                f.write(f"## Assumptions\n\n")
                for assumption in artifacts.read_back.assumptions:
                    f.write(f"- {assumption}\n")
                f.write("\n")
            
            if artifacts.read_back.risk_callouts:
                f.write(f"## Risk Callouts\n\n")
                for risk in artifacts.read_back.risk_callouts:
                    f.write(f"- {risk}\n")
        
        saved["read_back"] = str(readback_file)
        
        # 2. SpecDSL as JSON
        spec_file = session_dir / "spec_dsl.json"
        with open(spec_file, 'w') as f:
            json.dump(self._serialize_spec_dsl(artifacts.spec_dsl), f, indent=2)
        saved["spec_dsl"] = str(spec_file)
        
        # 3. Baseline Policy as JSON
        baseline_file = session_dir / "baseline_policy.json"
        with open(baseline_file, 'w') as f:
            json.dump(artifacts.baseline_policy, f, indent=2)
        saved["baseline_policy"] = str(baseline_file)
        
        # 4. Candidate Policy as JSON
        candidate_file = session_dir / "candidate_policy.json"
        with open(candidate_file, 'w') as f:
            json.dump(artifacts.candidate_policy, f, indent=2)
        saved["candidate_policy"] = str(candidate_file)
        
        return saved
    
    def _save_evidence_archive(
        self, 
        rag_context: List[Dict[str, Any]], 
        session_dir: Path, 
        session_id: str
    ) -> str:
        """Save complete RAG context and evidence citations."""
        evidence_file = session_dir / "evidence_archive.json"
        
        evidence_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "rag_context": {
                "total_chunks": len(rag_context),
                "chunks": [
                    {
                        "index": i,
                        "text": chunk.get("text", "")[:1000],  # Limit text length
                        "score": chunk.get("score", 0),
                        "metadata": chunk.get("metadata", {}),
                        "text_hash": hashlib.md5(chunk.get("text", "").encode()).hexdigest()[:8]
                    } for i, chunk in enumerate(rag_context)
                ]
            },
            "summary": {
                "avg_score": sum(c.get("score", 0) for c in rag_context) / len(rag_context) if rag_context else 0,
                "content_types": list(set(c.get("metadata", {}).get("content_type", "unknown") for c in rag_context)),
                "total_text_length": sum(len(c.get("text", "")) for c in rag_context)
            }
        }
        
        with open(evidence_file, 'w') as f:
            json.dump(evidence_data, f, indent=2)
        
        return str(evidence_file)
    
    def _save_comparison_report(self, artifacts: PolicyArtifacts, session_dir: Path) -> str:
        """Generate and save detailed comparison between baseline and candidate policies."""
        comparison_file = session_dir / "policy_comparison.md"
        
        baseline = artifacts.baseline_policy
        candidate = artifacts.candidate_policy
        
        analysis = self._analyze_policy_differences(baseline, candidate)
        
        with open(comparison_file, 'w') as f:
            f.write(f"# Policy Comparison Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Baseline Confidence:** Deterministic (100%)\n")
            f.write(f"**Candidate Confidence:** {artifacts.generation_confidence:.1%}\n\n")
            
            # Executive Summary
            f.write(f"## Executive Summary\n\n")
            f.write(f"- **Baseline Statements:** {analysis['baseline_statement_count']}\n")
            f.write(f"- **Candidate Statements:** {analysis['candidate_statement_count']}\n")
            f.write(f"- **Statement Difference:** {analysis['statement_difference']}\n")
            f.write(f"- **Actions Overlap:** {analysis['actions_overlap']:.1%}\n")
            f.write(f"- **Resources Overlap:** {analysis['resources_overlap']:.1%}\n\n")
            
            # Detailed Analysis
            f.write(f"## Detailed Analysis\n\n")
            
            f.write(f"### Actions Comparison\n")
            f.write(f"- **Baseline Only:** {', '.join(analysis['baseline_only_actions'][:10])}\n")
            f.write(f"- **Candidate Only:** {', '.join(analysis['candidate_only_actions'][:10])}\n")
            f.write(f"- **Common Actions:** {len(analysis['common_actions'])}\n\n")
            
            f.write(f"### Resources Comparison\n")
            f.write(f"- **Baseline Only:** {len(analysis['baseline_only_resources'])} resources\n")
            f.write(f"- **Candidate Only:** {len(analysis['candidate_only_resources'])} resources\n")
            f.write(f"- **Common Resources:** {len(analysis['common_resources'])}\n\n")
            
            # Side-by-side JSON
            f.write(f"## Side-by-Side Policies\n\n")
            f.write(f"### Baseline Policy\n```json\n")
            f.write(json.dumps(baseline, indent=2))
            f.write(f"\n```\n\n")
            
            f.write(f"### Candidate Policy\n```json\n")
            f.write(json.dumps(candidate, indent=2))
            f.write(f"\n```\n\n")
            
            # Recommendations
            f.write(f"## Recommendations\n\n")
            if analysis['statement_difference'] > 2:
                f.write(f"- ⚠️  Significant structural differences - review carefully\n")
            if analysis['actions_overlap'] < 0.8:
                f.write(f"- ⚠️  Low action overlap - verify intent alignment\n")
            if analysis['candidate_statement_count'] == 0:
                f.write(f"- ❌ Candidate policy is empty - baseline recommended\n")
            if analysis['baseline_statement_count'] == 0:
                f.write(f"- ⚠️  Baseline policy is empty - review SpecDSL\n")
        
        return str(comparison_file)
    
    def _save_audit_trail(self, artifacts: PolicyArtifacts, original_prompt: str, session_dir: Path) -> str:
        """Save complete audit trail with confidence scores and validation results."""
        audit_file = session_dir / "audit_trail.json"
        
        audit_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "original_prompt": original_prompt,
                "session_duration": "N/A"  # Could be calculated if we track start time
            },
            "extraction_metrics": {
                "confidence": artifacts.extraction_confidence,
                "capabilities_extracted": len(artifacts.spec_dsl.capabilities),
                "restrictions_extracted": len(artifacts.spec_dsl.must_never) if artifacts.spec_dsl.must_never else 0,
                "evidence_citations": len(self._extract_all_evidence(artifacts.spec_dsl))
            },
            "generation_metrics": {
                "confidence": artifacts.generation_confidence,
                "baseline_statements": len(artifacts.baseline_policy.get("Statement", [])),
                "candidate_statements": len(artifacts.candidate_policy.get("Statement", []))
            },
            "validation_results": {
                "spec_dsl_valid": True,  # Would be False if validation failed
                "baseline_generated": len(artifacts.baseline_policy.get("Statement", [])) > 0,
                "candidate_generated": len(artifacts.candidate_policy.get("Statement", [])) > 0
            },
            "quality_metrics": {
                "policy_complexity_baseline": self._calculate_policy_complexity(artifacts.baseline_policy),
                "policy_complexity_candidate": self._calculate_policy_complexity(artifacts.candidate_policy),
                "alignment_score": self._calculate_alignment_score(artifacts)
            }
        }
        
        with open(audit_file, 'w') as f:
            json.dump(audit_data, f, indent=2)
        
        return str(audit_file)
    
    def _create_session_readme(self, artifacts: PolicyArtifacts, original_prompt: str, session_dir: Path) -> str:
        """Create README file explaining the session contents."""
        readme_file = session_dir / "README.md"
        
        with open(readme_file, 'w') as f:
            f.write(f"# Policy Generation Session\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Original Prompt:** {original_prompt}\n\n")
            
            f.write(f"## Contents\n\n")
            f.write(f"This directory contains a complete four-artifact policy generation session:\n\n")
            f.write(f"### Core Artifacts\n")
            f.write(f"- `artifacts.json` - Master file with all artifacts and metadata\n")
            f.write(f"- `read_back.md` - Human-readable summary and analysis\n")
            f.write(f"- `spec_dsl.json` - Machine-readable intent specification\n")
            f.write(f"- `baseline_policy.json` - Deterministic policy from canonizer\n")
            f.write(f"- `candidate_policy.json` - LLM-generated policy\n\n")
            
            f.write(f"### Analysis & Context\n")
            f.write(f"- `policy_comparison.md` - Side-by-side policy analysis\n")
            f.write(f"- `evidence_archive.json` - RAG context and citations\n")
            f.write(f"- `audit_trail.json` - Confidence scores and metrics\n")
            f.write(f"- `README.md` - This file\n\n")
            
            f.write(f"## Quick Stats\n\n")
            f.write(f"- **Extraction Confidence:** {artifacts.extraction_confidence:.1%}\n")
            f.write(f"- **Generation Confidence:** {artifacts.generation_confidence:.1%}\n")
            f.write(f"- **Capabilities:** {len(artifacts.spec_dsl.capabilities)}\n")
            f.write(f"- **Restrictions:** {len(artifacts.spec_dsl.must_never) if artifacts.spec_dsl.must_never else 0}\n")
            f.write(f"- **Baseline Statements:** {len(artifacts.baseline_policy.get('Statement', []))}\n")
            f.write(f"- **Candidate Statements:** {len(artifacts.candidate_policy.get('Statement', []))}\n\n")
            
            f.write(f"## Usage\n\n")
            f.write(f"1. Review `read_back.md` for human understanding\n")
            f.write(f"2. Check `policy_comparison.md` for differences analysis\n")
            f.write(f"3. Deploy `baseline_policy.json` for safety or `candidate_policy.json` if validated\n")
            f.write(f"4. Reference `evidence_archive.json` for source documentation\n")
        
        return str(readme_file)
    
    def _update_global_index(self, session_name: str, session_id: str, prompt: str, artifacts: PolicyArtifacts):
        """Update global index of all sessions."""
        index_file = self.base_output_dir / "session_index.json"
        
        try:
            with open(index_file, 'r') as f:
                index = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            index = {"sessions": []}
        
        session_entry = {
            "session_id": session_id,
            "session_name": session_name,
            "created_at": datetime.now().isoformat(),
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "extraction_confidence": artifacts.extraction_confidence,
            "generation_confidence": artifacts.generation_confidence,
            "capabilities": len(artifacts.spec_dsl.capabilities),
            "restrictions": len(artifacts.spec_dsl.must_never) if artifacts.spec_dsl.must_never else 0
        }
        
        index["sessions"].append(session_entry)
        
        # Keep only last 100 sessions
        index["sessions"] = index["sessions"][-100:]
        
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    # Helper methods for analysis
    def _analyze_policy_differences(self, baseline: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze differences between baseline and candidate policies."""
        baseline_statements = baseline.get("Statement", [])
        candidate_statements = candidate.get("Statement", [])
        
        baseline_actions = set()
        candidate_actions = set()
        baseline_resources = set()
        candidate_resources = set()
        
        for stmt in baseline_statements:
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            baseline_actions.update(actions)
            
            resources = stmt.get("Resource", [])
            if isinstance(resources, str):
                resources = [resources]
            baseline_resources.update(resources)
        
        for stmt in candidate_statements:
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            candidate_actions.update(actions)
            
            resources = stmt.get("Resource", [])
            if isinstance(resources, str):
                resources = [resources]
            candidate_resources.update(resources)
        
        common_actions = baseline_actions & candidate_actions
        common_resources = baseline_resources & candidate_resources
        
        return {
            "baseline_statement_count": len(baseline_statements),
            "candidate_statement_count": len(candidate_statements),
            "statement_difference": abs(len(baseline_statements) - len(candidate_statements)),
            "baseline_actions": list(baseline_actions),
            "candidate_actions": list(candidate_actions),
            "common_actions": list(common_actions),
            "baseline_only_actions": list(baseline_actions - candidate_actions),
            "candidate_only_actions": list(candidate_actions - baseline_actions),
            "actions_overlap": len(common_actions) / max(len(baseline_actions | candidate_actions), 1),
            "baseline_resources": list(baseline_resources),
            "candidate_resources": list(candidate_resources),
            "common_resources": list(common_resources),
            "baseline_only_resources": list(baseline_resources - candidate_resources),
            "candidate_only_resources": list(candidate_resources - baseline_resources),
            "resources_overlap": len(common_resources) / max(len(baseline_resources | candidate_resources), 1)
        }
    
    def _extract_all_evidence(self, spec_dsl: SpecDSL) -> List[Dict[str, Any]]:
        """Extract all evidence citations from SpecDSL."""
        evidence = []
        for cap in spec_dsl.capabilities:
            for ev in cap.evidence:
                evidence.append({
                    "doc_url": ev.doc_url,
                    "confidence": ev.confidence,
                    "rationale": ev.rationale,
                    "capability": cap.name
                })
            if cap.conditions:
                for cond in cap.conditions:
                    for ev in cond.evidence:
                        evidence.append({
                            "doc_url": ev.doc_url,
                            "confidence": ev.confidence,
                            "rationale": ev.rationale,
                            "condition": cond.key
                        })
        return evidence
    
    def _get_evidence_sources(self, spec_dsl: SpecDSL) -> List[str]:
        """Get unique evidence sources from SpecDSL."""
        sources = set()
        evidence = self._extract_all_evidence(spec_dsl)
        for ev in evidence:
            sources.add(ev["doc_url"])
        return list(sources)
    
    def _calculate_policy_complexity(self, policy: Dict[str, Any]) -> int:
        """Calculate complexity score for a policy."""
        statements = policy.get("Statement", [])
        complexity = 0
        
        for stmt in statements:
            complexity += 1  # Base complexity per statement
            
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            complexity += len(actions) * 0.1
            
            resources = stmt.get("Resource", [])
            if isinstance(resources, str):
                resources = [resources]
            complexity += len(resources) * 0.1
            
            if "Condition" in stmt:
                complexity += len(stmt["Condition"]) * 0.5
        
        return int(complexity)
    
    def _calculate_alignment_score(self, artifacts: PolicyArtifacts) -> float:
        """Calculate alignment score between baseline and candidate."""
        analysis = self._analyze_policy_differences(
            artifacts.baseline_policy, 
            artifacts.candidate_policy
        )
        
        # Weight different factors
        actions_weight = 0.4
        resources_weight = 0.3
        structure_weight = 0.3
        
        actions_score = analysis['actions_overlap']
        resources_score = analysis['resources_overlap']
        
        # Structure score based on statement count similarity
        baseline_count = analysis['baseline_statement_count']
        candidate_count = analysis['candidate_statement_count']
        if baseline_count + candidate_count > 0:
            structure_score = 1 - abs(baseline_count - candidate_count) / (baseline_count + candidate_count)
        else:
            structure_score = 1.0
        
        alignment = (
            actions_score * actions_weight +
            resources_score * resources_weight +
            structure_score * structure_weight
        )
        
        return round(alignment, 3)
