"""
Tests for model override functionality in Ultrawork Mode.
"""

import pytest

from ultra_vibe.core.hooks.model_override import (
    resolve_ultrawork_override,
    validate_variant_support,
    ULTRAWORK_MODEL_MAP,
    ULTRAWORK_VARIANT_MAP,
    SUPPORTED_VARIANTS,
    ModelOverrideHook,
)
from ultra_vibe.core.hooks.base import HookContext, HookType


class TestModelOverride:
    """Test model override resolution."""
    
    def test_resolve_ultrawork_override_default(self):
        """Test default model override without config."""
        # Mistral medium should upgrade to mistral large
        model, variant = resolve_ultrawork_override(
            current_model="mistral-medium-3.5",
            current_variant="medium",
        )
        assert model == "mistral-large-2407"
        assert variant == "max"
    
    def test_resolve_ultrawork_override_config(self):
        """Test model override with agent config."""
        config = {
            'agents': {
                'sisyphus': {
                    'ultrawork': {
                        'enabled': True,
                        'model': 'anthropic/claude-3-5-sonnet',
                        'variant': 'max',
                    }
                }
            }
        }
        
        model, variant = resolve_ultrawork_override(
            current_model="mistral-medium-3.5",
            current_variant="medium",
            config=config,
            agent_name="sisyphus",
        )
        assert model == "anthropic/claude-3-5-sonnet"
        assert variant == "max"
    
    def test_resolve_ultrawork_override_no_mapping(self):
        """Test model override when no mapping exists."""
        model, variant = resolve_ultrawork_override(
            current_model="unknown-model",
            current_variant="medium",
        )
        assert model == "unknown-model"
        assert variant == "max"  # Default variant
    
    def test_resolve_ultrawork_override_disabled(self):
        """Test that disabled ultrawork doesn't override."""
        config = {
            'agents': {
                'sisyphus': {
                    'ultrawork': {
                        'enabled': False,
                    }
                }
            }
        }
        
        model, variant = resolve_ultrawork_override(
            current_model="mistral-medium-3.5",
            current_variant="medium",
            config=config,
            agent_name="sisyphus",
        )
        # Should use default mapping since ultrawork is disabled for this agent
        assert model == "mistral-large-2407"


class TestVariantValidation:
    """Test variant support validation."""
    
    def test_validate_supported_variant(self):
        """Test validation of supported variants."""
        assert validate_variant_support("mistral-large-2407", "max") == "max"
        assert validate_variant_support("mistral-large-2407", "high") == "high"
        assert validate_variant_support("anthropic/claude-3-5-sonnet", "max") == "max"
    
    def test_validate_unsupported_variant(self):
        """Test fallback for unsupported variants."""
        # Model doesn't exist in map, should fall back
        result = validate_variant_support("unknown-model", "max")
        assert result == "medium"  # First in default list
    
    def test_validate_variant_not_in_list(self):
        """Test fallback when variant not in supported list."""
        # mistral-large-2407 supports max, high, medium, low
        result = validate_variant_support("mistral-large-2407", "super-max")
        assert result == "max"  # Falls back to first supported


class TestModelOverrideHook:
    """Test the ModelOverrideHook class."""
    
    def test_hook_initialization(self):
        """Test hook initialization."""
        hook = ModelOverrideHook()
        assert hook.name == "model_override"
        assert hook.hook_type == HookType.MODEL_SELECTION
        assert hook.priority == 20
        assert hook.enabled is True
    
    def test_hook_execution_no_ultrawork(self):
        """Test hook doesn't override when ultrawork not enabled."""
        hook = ModelOverrideHook()
        
        context = HookContext(
            session_id="test-session",
            message="normal prompt",
            agent_name="default",
            current_model="mistral-medium-3.5",
            current_variant="medium",
            metadata={'ultrawork_enabled': False},
        )
        
        result = hook(context, ("mistral-medium-3.5", "medium"))
        assert result == ("mistral-medium-3.5", "medium")
    
    def test_hook_execution_with_ultrawork(self):
        """Test hook overrides when ultrawork is enabled."""
        hook = ModelOverrideHook()
        
        context = HookContext(
            session_id="test-session",
            message="ultrawork",
            agent_name="default",
            current_model="mistral-medium-3.5",
            current_variant="medium",
            metadata={'ultrawork_enabled': True},
        )
        
        result = hook(context, ("mistral-medium-3.5", "medium"))
        assert result[0] == "mistral-large-2407"
        assert result[1] == "max"


class TestMappings:
    """Test model and variant mappings."""
    
    def test_model_map_exists(self):
        """Test that model map has entries."""
        assert len(ULTRAWORK_MODEL_MAP) > 0
        assert "mistral-medium-3.5" in ULTRAWORK_MODEL_MAP
    
    def test_variant_map_exists(self):
        """Test that variant map has entries."""
        assert len(ULTRAWORK_VARIANT_MAP) > 0
        assert "mistral-large-2407" in ULTRAWORK_VARIANT_MAP
    
    def test_supported_variants_exists(self):
        """Test that supported variants has entries."""
        assert len(SUPPORTED_VARIANTS) > 0
        assert "mistral-large-2407" in SUPPORTED_VARIANTS
