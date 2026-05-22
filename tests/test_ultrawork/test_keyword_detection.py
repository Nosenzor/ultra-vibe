"""
Tests for keyword detection in Ultrawork Mode.
"""

import pytest

from ultra_vibe.core.hooks.keyword_detector import (
    detect_ultrawork,
    ULTRAWORK_PATTERNS,
    HYPERPLAN_ULTRAWORK_PATTERNS,
    KeywordDetectorHook,
)
from ultra_vibe.core.hooks.base import HookContext, HookType


class TestKeywordDetection:
    """Test keyword detection functionality."""
    
    def test_detect_ultrawork_keywords(self):
        """Test detection of basic ultrawork keywords."""
        # Should detect "ultrawork" keyword
        assert detect_ultrawork("use ultrawork mode") is True
        assert detect_ultrawork("please use ultrawork") is True
        assert detect_ultrawork("ULTRAWORK") is True
        
        # Should detect "ulw" keyword
        assert detect_ultrawork("ulw please") is True
        assert detect_ultrawork("use ulw") is True
        assert detect_ultrawork("ULW") is True
        
        # Should detect slash commands
        assert detect_ultrawork("/ultrawork") is True
        assert detect_ultrawork("/ulw") is True
        assert detect_ultrawork("/ULTRAWORK") is True
        
        # Should detect standalone words
        assert detect_ultrawork("ultrawork") is True
        assert detect_ultrawork("ulw") is True
    
    def test_detect_ultrawork_no_match(self):
        """Test that non-ultrawork messages don't trigger."""
        assert detect_ultrawork("normal prompt") is False
        assert detect_ultrawork("please help me") is False
        assert detect_ultrawork("what is the weather") is False
        # These should NOT match (no word boundaries)
        assert detect_ultrawork("myultrawork") is False
        assert detect_ultrawork("ultraworkmode") is False
    
    def test_detect_hyperplan_ultrawork_combo(self):
        """Test detection of hyperplan + ultrawork combo."""
        # Should detect various combo patterns
        assert detect_ultrawork("hpp ulw") is True
        assert detect_ultrawork("ulw hyperplan") is True
        assert detect_ultrawork("hyperplan ulw") is True
        
        # With slash commands
        assert detect_ultrawork("/hpp /ulw") is True
        assert detect_ultrawork("/ulw /hpp") is True
    
    def test_planner_agent_exclusion(self):
        """Test that planner agents don't trigger ultrawork."""
        # Planner agents should not trigger ultrawork
        assert detect_ultrawork("ultrawork", agent_name="plan") is False
        assert detect_ultrawork("ulw", agent_name="prometheus") is False
        
        # But should work for other agents
        assert detect_ultrawork("ultrawork", agent_name="default") is True
    
    def test_session_metadata_ultrawork(self):
        """Test detection from session metadata."""
        # Should detect if ultrawork is enabled in session
        session_meta = {'ultrawork_enabled': True}
        assert detect_ultrawork("any message", session_metadata=session_meta) is True
        
        # Should not detect if not enabled
        session_meta = {'ultrawork_enabled': False}
        assert detect_ultrawork("any message", session_metadata=session_meta) is False


class TestKeywordDetectorHook:
    """Test the KeywordDetectorHook class."""
    
    def test_hook_initialization(self):
        """Test hook initialization."""
        hook = KeywordDetectorHook()
        assert hook.name == "keyword_detector"
        assert hook.hook_type == HookType.PRE_PROMPT
        assert hook.priority == 10
        assert hook.enabled is True
    
    def test_detect_from_message(self):
        """Test detect_from_message method."""
        hook = KeywordDetectorHook()
        
        assert hook.detect_from_message("use ultrawork") is True
        assert hook.detect_from_message("ulw mode") is True
        assert hook.detect_from_message("normal text") is False
    
    def test_detect_hyperplan_ultrawork(self):
        """Test detect_hyperplan_ultrawork method."""
        hook = KeywordDetectorHook()
        
        assert hook.detect_hyperplan_ultrawork("hpp ulw") is True
        assert hook.detect_hyperplan_ultrawork("normal text") is False
    
    def test_hook_execution_detects_ultrawork(self):
        """Test that hook execution detects ultrawork and updates context."""
        hook = KeywordDetectorHook()
        
        context = HookContext(
            session_id="test-session",
            message="use ultrawork mode",
            agent_name="default",
        )
        
        # Execute the hook
        result = hook(context, "some system prompt")
        
        # Check that context was updated
        assert context.metadata.get('ultrawork_detected') is True
        assert context.metadata.get('ultrawork_enabled') is True
    
    def test_hook_execution_hyperplan_combo(self):
        """Test hook execution with hyperplan combo."""
        hook = KeywordDetectorHook()
        
        context = HookContext(
            session_id="test-session",
            message="hpp ulw",
            agent_name="default",
        )
        
        result = hook(context, "some system prompt")
        
        assert context.metadata.get('ultrawork_detected') is True
        assert context.metadata.get('hyperplan_ultrawork_detected') is True
        assert context.metadata.get('hyperplan_ultrawork_enabled') is True
    
    def test_hook_execution_planner_exclusion(self):
        """Test that hook doesn't trigger for planner agents."""
        hook = KeywordDetectorHook()
        
        context = HookContext(
            session_id="test-session",
            message="ultrawork",
            agent_name="plan",
        )
        
        result = hook(context, "some system prompt")
        
        # Should not enable ultrawork for planner
        assert context.metadata.get('ultrawork_enabled') is not True


class TestPatterns:
    """Test pattern constants."""
    
    def test_ultrawork_patterns_exist(self):
        """Test that ultrawork patterns are defined."""
        assert len(ULTRAWORK_PATTERNS) > 0
        assert isinstance(ULTRAWORK_PATTERNS, list)
    
    def test_hyperplan_patterns_exist(self):
        """Test that hyperplan patterns are defined."""
        assert len(HYPERPLAN_ULTRAWORK_PATTERNS) > 0
        assert isinstance(HYPERPLAN_ULTRAWORK_PATTERNS, list)
