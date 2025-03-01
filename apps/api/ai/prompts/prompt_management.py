"""
Comprehensive prompt management system with versioning, templates, and analytics.
"""
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from datetime import datetime
from enum import Enum
import re
import json
import structlog
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from jinja2 import Template, Environment, meta, TemplateSyntaxError
import hashlib
import uuid

from ...database.transaction import transaction, transactional
from ...cache.tiered_cache_service import TieredCacheService, CacheTier
from ...monitoring.performance_metrics import PerformanceMetricsService, MetricType
from ...errors.maily_error import ResourceNotFoundError, ValidationError

logger = structlog.get_logger("maily.ai.prompts")

class PromptCategory(str, Enum):
    """Categories of prompts."""
    CONTENT_GENERATION = "content_generation"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    CONVERSATION = "conversation"
    EMAIL = "email"
    ANALYSIS = "analysis"
    CUSTOM = "custom"

class PromptVersion(BaseModel):
    """Model for a prompt template version."""
    version: str
    template: str
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    variables: List[str] = Field(default_factory=list)
    is_active: bool = True

class PromptTemplate(BaseModel):
    """Model for a versioned prompt template."""
    id: str
    name: str
    description: str
    category: PromptCategory
    task_type: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    versions: Dict[str, PromptVersion] = Field(default_factory=dict)
    default_version: str = "v1"

    class Config:
        orm_mode = True

    def add_version(
        self,
        template: str,
        version: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        set_as_default: bool = False
    ) -> str:
        """Add a new version to the prompt template.

        Args:
            template: The template string
            version: Optional version string or auto-generated
            description: Optional version description
            created_by: Optional creator identifier
            metadata: Optional metadata dictionary
            set_as_default: Whether to set this as default version

        Returns:
            Version string
        """
        # Generate version if not provided
        if not version:
            existing_versions = list(self.versions.keys())
            if not existing_versions:
                version = "v1"
            else:
                # Find highest numeric version
                numeric_versions = []
                for v in existing_versions:
                    if v.startswith("v") and v[1:].isdigit():
                        numeric_versions.append(int(v[1:]))

                if numeric_versions:
                    version = f"v{max(numeric_versions) + 1}"
                else:
                    version = f"v{len(existing_versions) + 1}"

        # Extract variables from template
        variables = self._extract_variables(template)

        # Create version
        prompt_version = PromptVersion(
            version=version,
            template=template,
            description=description or f"Version {version}",
            created_at=datetime.now(),
            created_by=created_by,
            metadata=metadata or {},
            variables=variables,
            is_active=True
        )

        # Add to versions
        self.versions[version] = prompt_version

        # Update prompt
        self.updated_at = datetime.now()

        # Set as default if requested or first version
        if set_as_default or len(self.versions) == 1:
            self.default_version = version

        return version

    def get_version(self, version: Optional[str] = None) -> PromptVersion:
        """Get a specific version or the default.

        Args:
            version: Optional version string or default

        Returns:
            PromptVersion

        Raises:
            ValueError: If version not found
        """
        version_key = version or self.default_version

        if version_key not in self.versions:
            raise ValueError(f"Version '{version_key}' not found")

        return self.versions[version_key]

    def render(
        self,
        variables: Dict[str, Any],
        version: Optional[str] = None
    ) -> str:
        """Render the prompt with variables.

        Args:
            variables: Dictionary of variables
            version: Optional version string or default

        Returns:
            Rendered prompt

        Raises:
            ValueError: If missing required variables or rendering fails
        """
        # Get version
        prompt_version = self.get_version(version)

        # Check required variables
        missing_vars = []
        for var in prompt_version.variables:
            if var not in variables:
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")

        # Render template
        try:
            template = Template(prompt_version.template)
            return template.render(**variables)
        except Exception as e:
            raise ValueError(f"Error rendering template: {str(e)}")

    def _extract_variables(self, template_str: str) -> List[str]:
        """Extract variables from a template string.

        Args:
            template_str: The template string

        Returns:
            List of variable names
        """
        try:
            env = Environment()
            ast = env.parse(template_str)
            variables = meta.find_undeclared_variables(ast)
            return sorted(list(variables))
        except TemplateSyntaxError as e:
            logger.error(
                "Template syntax error when extracting variables",
                error=str(e),
                template=template_str
            )
            # Try regex fallback
            return self._extract_variables_regex(template_str)

    def _extract_variables_regex(self, template_str: str) -> List[str]:
        """Extract variables using regex fallback.

        Args:
            template_str: The template string

        Returns:
            List of variable names
        """
        # This is a fallback that might not catch all jinja2 syntax
        # but should handle basic {{ variable }} syntax
        matches = re.findall(r'{{\s*(\w+)\s*}}', template_str)
        return sorted(list(set(matches)))

class PromptPerformance(BaseModel):
    """Model for tracking prompt performance metrics."""
    prompt_id: str
    version: str
    task_type: str
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_latency: float = 0
    average_latency: float = 0
    last_used: Optional[datetime] = None
    success_rate: float = 0

    def update(
        self,
        success: bool,
        tokens_in: int,
        tokens_out: int,
        latency: float
    ) -> None:
        """Update performance with a new usage.

        Args:
            success: Whether the prompt usage succeeded
            tokens_in: Input tokens used
            tokens_out: Output tokens generated
            latency: Latency in seconds
        """
        self.usage_count += 1

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
        self.total_latency += latency
        self.last_used = datetime.now()

        # Update derived metrics
        if self.usage_count > 0:
            self.success_rate = self.success_count / self.usage_count
            self.average_latency = self.total_latency / self.usage_count

class PromptService:
    """Service for managing and rendering prompts."""

    def __init__(
        self,
        db: Session,
        cache_service: Optional[TieredCacheService] = None,
        metrics_service: Optional[PerformanceMetricsService] = None
    ):
        """Initialize the prompt service.

        Args:
            db: SQLAlchemy database session
            cache_service: Optional cache service
            metrics_service: Optional metrics service
        """
        self.db = db
        self.cache = cache_service
        self.metrics = metrics_service

        # In-memory storage for templates (fallback if db not available)
        self._templates: Dict[str, PromptTemplate] = {}

        # Performance tracking
        self._performance: Dict[str, Dict[str, PromptPerformance]] = {}

    @transactional
    def create_template(
        self,
        name: str,
        template: str,
        description: str,
        category: PromptCategory,
        task_type: str,
        tags: List[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version_description: Optional[str] = None
    ) -> PromptTemplate:
        """Create a new prompt template.

        Args:
            name: Template name
            template: Initial template string
            description: Template description
            category: Template category
            task_type: Associated task type
            tags: Optional tags
            created_by: Optional creator identifier
            metadata: Optional metadata dictionary
            version_description: Optional description for initial version

        Returns:
            Created PromptTemplate
        """
        # Generate ID
        template_id = str(uuid.uuid4())

        # Create template
        prompt_template = PromptTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            task_type=task_type,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=created_by,
            tags=tags or [],
            metadata=metadata or {}
        )

        # Add initial version
        prompt_template.add_version(
            template=template,
            version="v1",
            description=version_description or "Initial version",
            created_by=created_by,
            set_as_default=True
        )

        # Store in DB (placeholder - actual DB operation depends on model)
        # In a real implementation, this would use the appropriate ORM method
        self._templates[template_id] = prompt_template

        # Invalidate cache
        if self.cache:
            self.cache.invalidate(f"prompt:*")

        # Log creation
        logger.info(
            "Prompt template created",
            template_id=template_id,
            name=name,
            task_type=task_type,
            created_by=created_by
        )

        return prompt_template

    def get_template(
        self,
        template_id: str,
        version: Optional[str] = None
    ) -> PromptTemplate:
        """Get a prompt template by ID.

        Args:
            template_id: Template ID
            version: Optional version string or default

        Returns:
            PromptTemplate

        Raises:
            ResourceNotFoundError: If template not found
        """
        # Try cache first
        if self.cache:
            cache_key = f"prompt:{template_id}"
            cached = self.cache.get(cache_key)
            if cached:
                template = PromptTemplate(**cached)
                return template

        # Try memory cache
        if template_id in self._templates:
            template = self._templates[template_id]

            # Update cache
            if self.cache:
                self.cache.set(
                    key=f"prompt:{template_id}",
                    value=template.dict(),
                    data_type="prompt_template",
                    tier=CacheTier.NORMAL
                )

            return template

        # In a real implementation, this would query the database
        # something like: template = db.query(PromptTemplateModel).filter_by(id=template_id).first()

        # Not found
        raise ResourceNotFoundError(f"Prompt template {template_id} not found")

    def get_templates(
        self,
        category: Optional[PromptCategory] = None,
        task_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[PromptTemplate]:
        """Get prompt templates with filtering.

        Args:
            category: Optional category filter
            task_type: Optional task type filter
            tags: Optional tags filter

        Returns:
            List of PromptTemplate objects
        """
        # Start with all templates
        templates = list(self._templates.values())

        # Apply filters
        if category:
            templates = [t for t in templates if t.category == category]

        if task_type:
            templates = [t for t in templates if t.task_type == task_type]

        if tags:
            templates = [t for t in templates if all(tag in t.tags for tag in tags)]

        return templates

    @transactional
    def add_template_version(
        self,
        template_id: str,
        template: str,
        version: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        set_as_default: bool = False
    ) -> str:
        """Add a new version to an existing template.

        Args:
            template_id: Template ID
            template: Template string
            version: Optional version string or auto-generated
            description: Optional version description
            created_by: Optional creator identifier
            metadata: Optional metadata dictionary
            set_as_default: Whether to set this as default version

        Returns:
            Version string

        Raises:
            ResourceNotFoundError: If template not found
        """
        # Get template
        prompt_template = self.get_template(template_id)

        # Add version
        new_version = prompt_template.add_version(
            template=template,
            version=version,
            description=description,
            created_by=created_by,
            metadata=metadata,
            set_as_default=set_as_default
        )

        # Update in storage
        self._templates[template_id] = prompt_template

        # Invalidate cache
        if self.cache:
            self.cache.invalidate(f"prompt:{template_id}")

        # Log version addition
        logger.info(
            "Prompt template version added",
            template_id=template_id,
            version=new_version,
            set_as_default=set_as_default,
            created_by=created_by
        )

        return new_version

    @transactional
    def set_default_version(self, template_id: str, version: str) -> None:
        """Set the default version for a template.

        Args:
            template_id: Template ID
            version: Version string

        Raises:
            ResourceNotFoundError: If template not found
            ValueError: If version not found
        """
        # Get template
        prompt_template = self.get_template(template_id)

        # Check version exists
        if version not in prompt_template.versions:
            raise ValueError(f"Version '{version}' not found")

        # Set default
        old_default = prompt_template.default_version
        prompt_template.default_version = version
        prompt_template.updated_at = datetime.now()

        # Update in storage
        self._templates[template_id] = prompt_template

        # Invalidate cache
        if self.cache:
            self.cache.invalidate(f"prompt:{template_id}")

        # Log version change
        logger.info(
            "Prompt template default version changed",
            template_id=template_id,
            old_version=old_default,
            new_version=version
        )

    def render_prompt(
        self,
        template_id: str,
        variables: Dict[str, Any],
        version: Optional[str] = None
    ) -> str:
        """Render a prompt with variables.

        Args:
            template_id: Template ID
            variables: Dictionary of variables
            version: Optional version string or default

        Returns:
            Rendered prompt

        Raises:
            ResourceNotFoundError: If template not found
            ValidationError: If missing required variables or rendering fails
        """
        start_time = time.time()
        rendered_prompt = None
        success = False

        try:
            # Get template
            prompt_template = self.get_template(template_id, version)

            # Record metric start
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.AI,
                    name="prompt_render_start",
                    duration_ms=0,
                    metadata={
                        "template_id": template_id,
                        "version": version or prompt_template.default_version,
                        "task_type": prompt_template.task_type
                    }
                )

            # Render template
            try:
                rendered_prompt = prompt_template.render(variables, version)
                success = True
            except ValueError as e:
                # Convert to validation error
                raise ValidationError(f"Error rendering prompt: {str(e)}")

            # Record performance
            self._record_usage(
                prompt_id=template_id,
                version=version or prompt_template.default_version,
                task_type=prompt_template.task_type,
                success=True,
                tokens_in=len(rendered_prompt) // 4,  # Rough estimate
                tokens_out=0,
                latency=time.time() - start_time
            )

            return rendered_prompt

        except Exception as e:
            # Record performance
            if template_id in self._templates:
                task_type = self._templates[template_id].task_type
                version_used = version or self._templates[template_id].default_version
            else:
                task_type = "unknown"
                version_used = version or "unknown"

            self._record_usage(
                prompt_id=template_id,
                version=version_used,
                task_type=task_type,
                success=False,
                tokens_in=0,
                tokens_out=0,
                latency=time.time() - start_time
            )

            # Re-raise
            raise

        finally:
            # Record metric completion
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.AI,
                    name="prompt_render_complete",
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={
                        "template_id": template_id,
                        "version": version_used if 'version_used' in locals() else "unknown",
                        "task_type": task_type if 'task_type' in locals() else "unknown",
                        "success": success
                    },
                    success=success,
                    error=None if success else "Rendering failed"
                )

    def get_prompt_performance(
        self,
        template_id: Optional[str] = None,
        version: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for prompts.

        Args:
            template_id: Optional template ID filter
            version: Optional version filter
            task_type: Optional task type filter

        Returns:
            Dictionary of performance metrics
        """
        results = {
            "prompts": {},
            "summary": {
                "total_usage": 0,
                "success_rate": 0,
                "average_latency": 0,
                "total_tokens_in": 0,
                "total_tokens_out": 0
            }
        }

        # Collect all performance data
        all_usage = 0
        all_success = 0
        all_latency = 0
        all_tokens_in = 0
        all_tokens_out = 0

        # Filter by template ID if provided
        prompt_ids = [template_id] if template_id else list(self._performance.keys())

        for prompt_id in prompt_ids:
            if prompt_id not in self._performance:
                continue

            # Get all versions for this prompt
            versions = self._performance[prompt_id]

            # Filter versions if specified
            if version:
                if version in versions:
                    version_items = [(version, versions[version])]
                else:
                    version_items = []
            else:
                version_items = list(versions.items())

            # Skip if no versions match
            if not version_items:
                continue

            # Add prompt to results
            if prompt_id not in results["prompts"]:
                results["prompts"][prompt_id] = {
                    "versions": {},
                    "total_usage": 0,
                    "success_rate": 0,
                    "average_latency": 0,
                    "total_tokens_in": 0,
                    "total_tokens_out": 0
                }

            prompt_usage = 0
            prompt_success = 0
            prompt_latency = 0
            prompt_tokens_in = 0
            prompt_tokens_out = 0

            # Process each version
            for ver, perf in version_items:
                # Skip if task type doesn't match
                if task_type and perf.task_type != task_type:
                    continue

                # Add version performance
                results["prompts"][prompt_id]["versions"][ver] = {
                    "usage_count": perf.usage_count,
                    "success_rate": perf.success_rate,
                    "average_latency": perf.average_latency,
                    "total_tokens_in": perf.total_tokens_in,
                    "total_tokens_out": perf.total_tokens_out,
                    "last_used": perf.last_used.isoformat() if perf.last_used else None
                }

                # Update prompt totals
                prompt_usage += perf.usage_count
                prompt_success += perf.success_count
                prompt_latency += perf.total_latency
                prompt_tokens_in += perf.total_tokens_in
                prompt_tokens_out += perf.total_tokens_out

                # Update overall totals
                all_usage += perf.usage_count
                all_success += perf.success_count
                all_latency += perf.total_latency
                all_tokens_in += perf.total_tokens_in
                all_tokens_out += perf.total_tokens_out

            # Update prompt summary
            if prompt_usage > 0:
                results["prompts"][prompt_id]["total_usage"] = prompt_usage
                results["prompts"][prompt_id]["success_rate"] = prompt_success / prompt_usage
                results["prompts"][prompt_id]["average_latency"] = prompt_latency / prompt_usage
                results["prompts"][prompt_id]["total_tokens_in"] = prompt_tokens_in
                results["prompts"][prompt_id]["total_tokens_out"] = prompt_tokens_out

                # Add template info if available
                if prompt_id in self._templates:
                    template = self._templates[prompt_id]
                    results["prompts"][prompt_id]["name"] = template.name
                    results["prompts"][prompt_id]["task_type"] = template.task_type
                    results["prompts"][prompt_id]["category"] = template.category

        # Update overall summary
        if all_usage > 0:
            results["summary"]["total_usage"] = all_usage
            results["summary"]["success_rate"] = all_success / all_usage
            results["summary"]["average_latency"] = all_latency / all_usage
            results["summary"]["total_tokens_in"] = all_tokens_in
            results["summary"]["total_tokens_out"] = all_tokens_out

        return results

    def _record_usage(
        self,
        prompt_id: str,
        version: str,
        task_type: str,
        success: bool,
        tokens_in: int,
        tokens_out: int,
        latency: float
    ) -> None:
        """Record usage for a prompt.

        Args:
            prompt_id: Template ID
            version: Version string
            task_type: Task type
            success: Whether the usage succeeded
            tokens_in: Input tokens used
            tokens_out: Output tokens generated
            latency: Latency in seconds
        """
        # Initialize if needed
        if prompt_id not in self._performance:
            self._performance[prompt_id] = {}

        if version not in self._performance[prompt_id]:
            self._performance[prompt_id][version] = PromptPerformance(
                prompt_id=prompt_id,
                version=version,
                task_type=task_type
            )

        # Update performance
        self._performance[prompt_id][version].update(
            success=success,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency=latency
        )

    def get_prompt_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for optimizing prompts.

        Returns:
            Dictionary of recommendations
        """
        recommendations = {
            "optimization_opportunities": [],
            "performance_warnings": [],
            "version_recommendations": []
        }

        # Analyze performance data
        for prompt_id, versions in self._performance.items():
            if prompt_id not in self._templates:
                continue

            template = self._templates[prompt_id]
            default_version = template.default_version

            # Compare version performance
            if len(versions) > 1 and default_version in versions:
                default_perf = versions[default_version]

                # Find best performing version
                best_version = None
                best_success_rate = 0

                for ver, perf in versions.items():
                    # Need minimum usage for comparison
                    if perf.usage_count < 10:
                        continue

                    if perf.success_rate > best_success_rate:
                        best_success_rate = perf.success_rate
                        best_version = ver

                # If best is not default and significantly better
                if (best_version and best_version != default_version and
                    versions[best_version].success_rate > default_perf.success_rate * 1.1):
                    # At least 10% better
                    recommendations["version_recommendations"].append({
                        "prompt_id": prompt_id,
                        "name": template.name,
                        "current_default": default_version,
                        "recommended_version": best_version,
                        "current_success_rate": default_perf.success_rate,
                        "recommended_success_rate": versions[best_version].success_rate,
                        "improvement": versions[best_version].success_rate - default_perf.success_rate
                    })

            # Check for poor performance
            for ver, perf in versions.items():
                if perf.usage_count < 10:
                    continue

                if perf.success_rate < 0.7:
                    recommendations["performance_warnings"].append({
                        "prompt_id": prompt_id,
                        "name": template.name,
                        "version": ver,
                        "success_rate": perf.success_rate,
                        "usage_count": perf.usage_count,
                        "task_type": perf.task_type
                    })

                # Check for token efficiency
                if perf.total_tokens_out > 0:
                    ratio = perf.total_tokens_in / perf.total_tokens_out
                    if ratio > 5:  # Input is 5x larger than output
                        recommendations["optimization_opportunities"].append({
                            "prompt_id": prompt_id,
                            "name": template.name,
                            "version": ver,
                            "issue": "high_input_ratio",
                            "input_output_ratio": ratio,
                            "suggestion": "The prompt may be unnecessarily verbose. Consider refining for better token efficiency."
                        })

        return recommendations

# Initialize jinja2 environment with safety features
def create_jinja2_env():
    """Create a secure Jinja2 environment.

    Returns:
        Jinja2 Environment
    """
    env = Environment(
        autoescape=True,  # HTML escaping
        trim_blocks=True,
        lstrip_blocks=True
    )
    return env
