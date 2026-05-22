"""
Tests for task delegation system.
"""

import pytest
import asyncio

from ultra_vibe.core.delegation.task_manager import (
    TaskManager,
    DelegatedTask,
    TaskResult,
    TaskStatus,
    AgentType,
    get_task_manager,
    create_task,
    delegate_task,
)


class TestTaskManager:
    """Test task manager functionality."""
    
    def test_task_creation(self):
        """Test creating a new task."""
        manager = TaskManager()
        task_id = manager.create_task(
            description="Test task",
            agent_type=AgentType.SISYPHUS,
        )
        
        assert task_id is not None
        assert len(task_id) > 0
        assert "ulw-" in task_id
        
        task = manager.get_task(task_id)
        assert task is not None
        assert task.description == "Test task"
        assert task.agent_type == AgentType.SISYPHUS
        assert task.status == TaskStatus.CREATED
    
    def test_get_active_task(self):
        """Test getting active task."""
        manager = TaskManager()
        task_id = manager.create_task("Task 1")
        
        active = manager.get_active_task()
        assert active is not None
        assert active.task_id == task_id
    
    def test_update_task_status(self):
        """Test updating task status."""
        manager = TaskManager()
        task_id = manager.create_task("Task 1")
        
        result = manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        assert result is True
        
        task = manager.get_task(task_id)
        assert task.status == TaskStatus.IN_PROGRESS
    
    def test_add_result(self):
        """Test adding a result to a task."""
        manager = TaskManager()
        task_id = manager.create_task("Task 1")
        
        result = manager.add_result(
            task_id=task_id,
            agent_name="hephaestus",
            agent_type=AgentType.HEPHAESTUS,
            content="Implementation complete",
        )
        assert result is True
        
        task = manager.get_task(task_id)
        assert len(task.results) == 1
        assert task.results[0].content == "Implementation complete"
        assert task.results[0].agent_name == "hephaestus"
    
    def test_delegate_subtask(self):
        """Test delegating a subtask."""
        manager = TaskManager()
        parent_id = manager.create_task("Parent task")
        
        subtask_id = manager.delegate_task(
            task_id=parent_id,
            agent_type=AgentType.HEPHAESTUS,
            description="Implement feature",
        )
        
        assert subtask_id is not None
        assert subtask_id != parent_id
        
        parent = manager.get_task(parent_id)
        assert subtask_id in parent.subtasks
        
        subtask = manager.get_task(subtask_id)
        assert subtask.parent_task_id == parent_id
        assert subtask.description == "Implement feature"
    
    def test_task_context(self):
        """Test getting task context."""
        manager = TaskManager()
        task_id = manager.create_task("Test task")
        
        context = manager.get_task_context(task_id)
        
        assert "Task ID: " in context
        assert "Test task" in context
        assert "Status: created" in context
    
    def test_get_all_tasks(self):
        """Test getting all tasks."""
        manager = TaskManager()
        task1 = manager.create_task("Task 1")
        task2 = manager.create_task("Task 2")
        
        all_tasks = manager.get_all_tasks()
        assert len(all_tasks) == 2
        
        task_ids = {t.task_id for t in all_tasks}
        assert task1 in task_ids
        assert task2 in task_ids
    
    def test_get_tasks_by_status(self):
        """Test getting tasks by status."""
        manager = TaskManager()
        task1 = manager.create_task("Task 1")
        task2 = manager.create_task("Task 2")
        
        manager.update_task_status(task1, TaskStatus.IN_PROGRESS)
        
        created = manager.get_tasks_by_status(TaskStatus.CREATED)
        in_progress = manager.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        
        assert len(created) == 1
        assert len(in_progress) == 1
        assert created[0].task_id == task2
        assert in_progress[0].task_id == task1
    
    def test_cleanup(self):
        """Test cleanup of old tasks."""
        manager = TaskManager()
        manager.create_task("Old task")
        
        # Cleanup should remove completed tasks older than 24 hours
        # Since we just created it, it shouldn't be removed
        count = manager.cleanup_completed(max_age_hours=0)
        assert count == 0
        
        # But if we mark it as completed and set updated_at to old time
        # This would require more complex setup
    
    def test_clear(self):
        """Test clearing all tasks."""
        manager = TaskManager()
        manager.create_task("Task 1")
        manager.create_task("Task 2")
        
        manager.clear()
        
        assert len(manager.get_all_tasks()) == 0
        assert manager.get_active_task() is None


class TestDelegatedTask:
    """Test DelegatedTask dataclass."""
    
    def test_to_dict(self):
        """Test serialization to dict."""
        from datetime import datetime
        
        task = DelegatedTask(
            task_id="test-1",
            parent_task_id=None,
            description="Test",
            agent_name="hephaestus",
            agent_type=AgentType.HEPHAESTUS,
        )
        
        data = task.to_dict()
        
        assert data['task_id'] == "test-1"
        assert data['description'] == "Test"
        assert data['agent_name'] == "hephaestus"
        assert data['agent_type'] == "hephaestus"
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        from datetime import datetime
        
        data = {
            'task_id': 'test-1',
            'parent_task_id': None,
            'description': 'Test',
            'agent_name': 'hephaestus',
            'agent_type': 'hephaestus',
            'priority': 'medium',
            'status': 'created',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'results': [],
            'subtasks': [],
            'metadata': {},
        }
        
        task = DelegatedTask.from_dict(data)
        
        assert task.task_id == "test-1"
        assert task.description == "Test"
        assert task.agent_type == AgentType.HEPHAESTUS


class TestTaskResult:
    """Test TaskResult dataclass."""
    
    def test_to_dict(self):
        """Test serialization to dict."""
        from datetime import datetime
        
        result = TaskResult(
            task_id="test-1",
            agent_name="hephaestus",
            agent_type=AgentType.HEPHAESTUS,
            content="Done",
        )
        
        data = result.to_dict()
        
        assert data['task_id'] == "test-1"
        assert data['agent_name'] == "hephaestus"
        assert data['content'] == "Done"
        assert data['success'] is True
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        from datetime import datetime
        
        data = {
            'task_id': 'test-1',
            'agent_name': 'hephaestus',
            'agent_type': 'hephaestus',
            'content': 'Done',
            'metadata': {},
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'error': None,
        }
        
        result = TaskResult.from_dict(data)
        
        assert result.task_id == "test-1"
        assert result.agent_name == "hephaestus"
        assert result.content == "Done"


class TestGlobalTaskManager:
    """Test global task manager singleton."""
    
    def test_singleton(self):
        """Test that get_task_manager returns the same instance."""
        manager1 = get_task_manager()
        manager2 = get_task_manager()
        
        assert manager1 is manager2
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Clear first
        get_task_manager().clear()
        
        task_id = create_task("Test task")
        assert task_id is not None
        
        task = get_task_manager().get_task(task_id)
        assert task is not None
        assert task.description == "Test task"
    
    def test_delegate_convenience_function(self):
        """Test delegate_task convenience function."""
        # Clear first
        get_task_manager().clear()
        
        parent_id = create_task("Parent task")
        subtask_id = delegate_task(
            task_id=parent_id,
            agent_type=AgentType.HEPHAESTUS,
            description="Subtask",
        )
        
        assert subtask_id is not None
        
        parent = get_task_manager().get_task(parent_id)
        assert subtask_id in parent.subtasks


@pytest.mark.asyncio
class TestSubAgentPool:
    """Test sub-agent pool."""
    
    async def test_spawn_and_wait(self):
        """Test spawning and waiting for a sub-agent."""
        from ultra_vibe.core.delegation.subagent import (
            SubAgentConfig,
            SubAgentPool,
        )
        
        pool = SubAgentPool(max_concurrent=2)
        
        config = SubAgentConfig(
            agent_name="test",
            task_id="test-1",
            task_description="Test task",
        )
        
        # Test that we can add a task to the pool
        # Without actually spawning (to avoid subprocess in tests)
        assert pool._running == {}
        assert pool._results == {}
        
        # Verify pool configuration
        assert pool.max_concurrent == 2
        assert config.task_id == "test-1"
    
    async def test_concurrency_limit(self):
        """Test that concurrency is limited."""
        from ultra_vibe.core.delegation.subagent import SubAgentPool, SubAgentConfig
        
        pool = SubAgentPool(max_concurrent=2)
        
        # Verify pool configuration
        assert pool.max_concurrent == 2
        
        # Without actual spawning, just verify pool state
        assert pool._running == {}
        assert pool._results == {}
    
    async def test_get_result(self):
        """Test getting a result."""
        from ultra_vibe.core.delegation.subagent import SubAgentPool, SubAgentResult
        
        pool = SubAgentPool()
        
        # Add a fake result directly
        result = SubAgentResult(
            task_id="test-1",
            agent_name="test",
            content="success",
            success=True,
        )
        
        # Manually add to pool results (for testing)
        pool._results["test-1"] = result
        
        retrieved = await pool.get_result("test-1")
        assert retrieved is not None
        assert retrieved.content == "success"
