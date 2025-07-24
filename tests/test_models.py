# tests/test_models.py
# A comprehensive test suite for the TodoList class in models.py

import os
import pytest
from kairu.models import ToDoList, Task

# --- Test Setup & Fixtures ---

TEST_DATA_FILE = "test_data.json"

@pytest.fixture
def todo_list():
    """
    A pytest fixture that creates a clean, empty TodoList instance
    for each test function that uses it. It also handles cleanup.
    """
    # ARRANGE: Ensure no old test file exists
    if os.path.exists(TEST_DATA_FILE):
        os.remove(TEST_DATA_FILE)
    
    # Provide the object to the test
    yield ToDoList(TEST_DATA_FILE)
    
    # CLEANUP: Remove the test file after the test is done
    if os.path.exists(TEST_DATA_FILE):
        os.remove(TEST_DATA_FILE)

# --- Test Cases ---

def test_add_group_successfully(todo_list):
    """Tests that a new group can be added."""
    # ACT
    success, message = todo_list.add_group("Work")
    
    # ASSERT
    assert success is True
    assert len(todo_list.data['groups']) == 1
    assert todo_list.data['groups'][0]['name'] == "Work"

def test_add_duplicate_group_fails(todo_list):
    """Tests that adding a duplicate group fails."""
    # ARRANGE
    todo_list.add_group("Work") # Add the first group
    
    # ACT
    success, message = todo_list.add_group("Work") # Try to add it again
    
    # ASSERT
    assert success is False
    assert len(todo_list.data['groups']) == 1 # Ensure no new group was added

def test_add_task_successfully(todo_list):
    """Tests that a new task can be added to a group."""
    # ARRANGE
    todo_list.add_group("Personal")
    
    # ACT
    success, message = todo_list.add_task(group_name="Personal", name="Buy groceries")
    
    # ASSERT
    assert success is True
    personal_group = todo_list.data['groups'][0]
    assert len(personal_group['tasks']) == 1
    assert isinstance(personal_group['tasks'][0], Task) # Verify it's a Task object
    assert personal_group['tasks'][0].name == "Buy groceries"
    assert todo_list.data['last_task_id'] == 1

def test_add_task_to_invalid_group_fails(todo_list):
    """Tests that adding a task to a non-existent group fails."""
    # ACT
    success, message = todo_list.add_task(group_name="Invalid Group", name="This will fail")
    
    # ASSERT
    assert success is False
    assert todo_list.data['last_task_id'] == 0 # Ensure ID was not incremented

def test_find_task_by_id(todo_list):
    """Tests that we can find a task by its permanent ID."""
    # ARRANGE
    todo_list.add_group("Work")
    todo_list.add_task(group_name="Work", name="My Task") # This will be ID 1
    
    # ACT
    group, task = todo_list.find_task_by_id(1)
    
    # ASSERT
    assert group is not None
    assert task is not None
    assert task.id == 1
    assert task.name == "My Task"

def test_edit_task_successfully(todo_list):
    """Tests that a task's properties can be edited."""
    # ARRANGE
    todo_list.add_group("Work")
    todo_list.add_task(group_name="Work", name="Initial Name") # ID 1
    
    # ACT
    success, message = todo_list.edit_task(task_id=1, new_name="Updated Name", new_priority="high")
    
    # ASSERT
    assert success is True
    _, task = todo_list.find_task_by_id(1)
    assert task.name == "Updated Name"
    assert task.priority == "high"

def test_mark_task_done_archives_and_awards_points(todo_list):
    """Tests that completing a task moves it and updates stats."""
    # ARRANGE
    todo_list.add_group("Work")
    todo_list.add_task(group_name="Work", name="My Task", priority="high") # ID 1
    
    # ACT
    success, (message, _, _) = todo_list.mark_task_done(1)
    
    # ASSERT
    assert success is True
    work_group = todo_list.data['groups'][0]
    assert len(work_group['tasks']) == 0 # Task removed from active list
    assert len(work_group['completed_tasks']) == 1 # Task added to completed list
    assert work_group['completed_tasks'][0].id == 1
    assert todo_list.data['user_stats']['points'] == 20 # 10 base + 10 high priority

def test_mark_recurring_task_done_reschedules(todo_list):
    """Tests that a recurring task is rescheduled instead of archived."""
    # ARRANGE
    todo_list.add_group("Work")
    due_date = "2025-07-25 10:00"
    todo_list.add_task(group_name="Work", name="Weekly Report", recurring="weekly", due_date=due_date) # ID 1
    
    # ACT
    success, (message, _, _) = todo_list.mark_task_done(1)
    
    # ASSERT
    assert success is True
    work_group = todo_list.data['groups'][0]
    assert len(work_group['tasks']) == 1 # Task is still in the active list
    assert len(work_group['completed_tasks']) == 0 # Task was not archived
    _, task = todo_list.find_task_by_id(1)
    assert task.due_date != due_date # The due date has changed

def test_delete_task_successfully(todo_list):
    """Tests that a task can be permanently deleted."""
    # ARRANGE
    todo_list.add_group("Work")
    todo_list.add_task(group_name="Work", name="Task to Delete") # ID 1
    
    # ACT
    success, message = todo_list.delete_task(1)
    
    # ASSERT
    assert success is True
    _, task = todo_list.find_task_by_id(1)
    assert task is None # The task can no longer be found

def test_save_and_load_data_preserves_objects(todo_list):
    """
    Tests the full serialization/deserialization bridge to ensure
    Task objects are correctly saved as dicts and reloaded as objects.
    """
    # ARRANGE
    todo_list.add_group("Work")
    todo_list.add_task(group_name="Work", name="Test Task")
    
    # ACT
    todo_list.save_data() # Save the data (with Task objects)
    new_todo_list = ToDoList(TEST_DATA_FILE) # Create a new instance, loading from the file
    
    # ASSERT
    assert len(new_todo_list.data['groups']) == 1
    work_group = new_todo_list.data['groups'][0]
    assert len(work_group['tasks']) == 1
    # The most important check: Is the item reloaded from the file a true Task object?
    assert isinstance(work_group['tasks'][0], Task)
    assert work_group['tasks'][0].name == "Test Task"
