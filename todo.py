# todo.py

import json
import datetime
import argparse
from rich.console import Console
from rich.table import Table
from dateutil.relativedelta import relativedelta

console = Console()
DATA_FILE = "tasks.json"

# --- Data Handling ---
def load_data():
    """Loads the entire data structure, providing a default if not found."""
    try:
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default structure if file is new or corrupted
        return {"last_task_id": 0, "groups": []}

def save_data(data):
    """Saves the entire data structure to the JSON file."""
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def search_all(data, keyword):
    """Searches for a keyword across all groups, tasks, and sub-tasks."""
    results = []
    keyword_lower = keyword.lower()

    for group in data.get('groups', []):
        # Search in parent tasks (active)
        for task in group.get('tasks', []):
            if (keyword_lower in task['name'].lower() or 
                (task.get('details') and keyword_lower in task['details'].lower())):
                results.append({"type": "Active Task", "id": task['id'], "match": task['name'], "location": f"Group '{group['name']}'"})
            
            # Search in sub-tasks of active tasks
            for i, sub_task in enumerate(task.get('sub_tasks', [])):
                if keyword_lower in sub_task['description'].lower():
                    results.append({"type": "Sub-task", "id": f"{task['id']}.{i+1}", "match": sub_task['description'], "location": f"Task #{task['id']}"})
        
        # Search in completed tasks
        for task in group.get('completed_tasks', []):
            if (keyword_lower in task['name'].lower() or 
                (task.get('details') and keyword_lower in task['details'].lower())):
                results.append({"type": "Completed Task", "id": task['id'], "match": task['name'], "location": f"Group '{group['name']}'"})

    return results

def display_search_results(results):
    """Displays search results in a table."""
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(title="Search Results")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Match", style="white")
    table.add_column("Location", style="green")

    for result in results:
        table.add_row(
            str(result['id']),
            result['type'],
            result['match'],
            result['location']
        )
    
    console.print(table)

# --- Helper Function ---
def find_task_by_id(data, task_id):
    """Finds a task and its parent group by its permanent ID."""
    for group in data['groups']:
        for task in group['tasks']:
            if task['id'] == task_id:
                return group, task
        # Also check completed tasks, as we might want to operate on them later
        for task in group.get('completed_tasks', []):
            if task['id'] == task_id:
                return group, task
    return None, None

def parse_tags(tags_string):
    """Parses a comma-separated string of tags into a list."""
    if not tags_string:
        return []
    # Clean up tags: remove whitespace and ensure they start with #
    tags = [f"#{tag.strip().lstrip('#')}" for tag in tags_string.split(',')]
    return tags

# --- Group Management ---
def add_group(data, group_name):
    """Adds a new, empty task group."""
    for group in data['groups']:
        if group['name'].lower() == group_name.lower():
            console.print(f"[bold red]Error: Group '{group_name}' already exists.[/bold red]")
            return
    new_group = {
        "name": group_name, 
        "tasks": [],
        "completed_tasks": [] # Add the new archive list
    }
    data['groups'].append(new_group)
    console.print(f"[green]Added new group: '{group_name}'[/green]")

def list_groups(data):
    """Lists all existing task groups."""
    if not data['groups']:
        console.print("[yellow]No groups found. Add one with 'group-add <name>'.[/yellow]")
        return
    console.print("\n[bold cyan]--- Task Groups ---[/bold cyan]")
    for group in data['groups']:
        console.print(f"- {group['name']}")
    console.print("")

def edit_task(data, task_id, new_name=None, new_details=None, new_priority=None, new_due_date=None, new_tags_string=None):
    """Edits any property of an existing task using its permanent ID."""
    group, task = find_task_by_id(data, task_id)

    if not task:
        console.print("[bold red]Error: Task ID not found.[/bold red]")
        return

    # Update only the fields that were provided by the user
    if new_name is not None:
        task['name'] = new_name
    if new_details is not None:
        task['details'] = new_details
    if new_priority is not None:
        if new_priority in ['low', 'medium', 'high']:
            task['priority'] = new_priority
        else:
            console.print("[bold red]Error: Invalid priority. No changes saved.[/bold red]")
            return
    if new_due_date is not None:
        try:
            due_date_obj = datetime.datetime.strptime(new_due_date, "%Y-%m-%d %H:%M")
            task['due_date'] = due_date_obj.isoformat()
        except ValueError:
            console.print("[bold red]Error: Invalid due date format. No changes saved.[/bold red]")
            return
    if new_tags_string is not None:
        task['tags'] = parse_tags(new_tags_string)

    console.print(f"[green]Successfully updated task #{task_id}.[/green]")

# --- Task & Sub-task Management ---
def add_task(data, group_name, name, details=None, priority='medium', due_date=None, recurring=None, tags_string=None):
    """Adds a new task to a specified group."""
    target_group = next((g for g in data['groups'] if g['name'].lower() == group_name.lower()), None)
    if not target_group:
        console.print(f"[bold red]Error: Group '{group_name}' not found.[/bold red]")
        return
    
    # Validation
    if priority not in ['low', 'medium', 'high']:
        console.print("[bold red]Error: Priority must be 'low', 'medium', or 'high'.[/bold red]")
        return
    if due_date:
        try:
            due_date_obj = datetime.datetime.strptime(due_date, "%Y-%m-%d %H:%M")
            due_date = due_date_obj.isoformat()
        except ValueError:
            console.print("[bold red]Error: Invalid due date format. Please use 'YYYY-MM-DD HH:MM'.[/bold red]")
            return

    # Duplicate check within the group
    for task in target_group['tasks']:
        if task['name'].lower() == name.lower():
            console.print(f"[bold red]Error: Task '{name}' already exists in group '{target_group['name']}'.[/bold red]")
            return

    # --- ID Generation ---
    data['last_task_id'] += 1
    new_id = data['last_task_id']

    new_task = { "id": new_id,
                "name": name,
                "details": details,
                "status": "pending",
                "created_at": datetime.datetime.now().isoformat(),
                "priority": priority,
                "due_date": due_date,
                "sub_tasks": [],
                "starred": False,
                "recurring": recurring,
                "tags": parse_tags(tags_string)
                }
    
    target_group['tasks'].append(new_task)
    console.print(f"[green]Added task '{name}' (ID: {new_id}) to group '{target_group['name']}'.[/green]")

def add_sub_task(data, parent_id, description):
    """Adds a sub-task to a parent task using its global ID."""
    _, task = find_task_by_id(data, parent_id)
    if task:
        sub_task = {"description": description, "status": "pending"}
        task['sub_tasks'].append(sub_task)
        console.print(f"[green]Added sub-task to '{task['name']}'.[/green]")
    else:
        console.print("[bold red]Error: Invalid parent task ID.[/bold red]")

def mark_task_done(data, task_id):
    """Handles task completion: resets recurring tasks or archives normal ones."""
    group, task = find_task_by_id(data, task_id)

    if not task:
        console.print("[bold red]Error: Task ID not found.[/bold red]")
        return
    
    # --- New Recurring Logic ---
    if task.get('recurring') and task.get('due_date'):
        recurrence = task['recurring']
        current_due_date = datetime.datetime.fromisoformat(task['due_date'])
        next_due_date = None

        if recurrence == 'daily':
            next_due_date = current_due_date + datetime.timedelta(days=1)
        elif recurrence == 'weekly':
            next_due_date = current_due_date + datetime.timedelta(weeks=1)
        elif recurrence == 'monthly':
            next_due_date = current_due_date + relativedelta(months=1)
        
        task['due_date'] = next_due_date.isoformat()
        # You can optionally reset sub-task statuses here if needed
        console.print(f"[green]Recurring task '{task['name']}' completed and rescheduled for {next_due_date.strftime('%Y-%m-%d %H:%M')}.[/green]")

    # --- Existing Archiving Logic ---
    else:
        if task in group.get('completed_tasks', []):
            console.print(f"[yellow]Task '{task['name']}' is already completed.[/yellow]")
            return
            
        task['status'] = 'done'
        task['completed_at'] = datetime.datetime.now().isoformat()
        group['tasks'].remove(task)
        group['completed_tasks'].append(task)
        console.print(f"[green]Completed and archived task '{task['name']}' in group '{group['name']}'.[/green]")

def mark_sub_task_done(data, parent_id, sub_task_id):
    """Marks a sub-task as 'done'."""
    _, task = find_task_by_id(data, parent_id)
    if not task:
        console.print("[bold red]Error: Invalid parent task ID.[/bold red]")
        return
    try:
        sub_task_index = int(sub_task_id) - 1
        if 0 <= sub_task_index < len(task['sub_tasks']):
            task['sub_tasks'][sub_task_index]['status'] = 'done'
            console.print(f"[green]Completed sub-task for '{task['name']}'.[/green]")
        else:
            console.print("[bold red]Error: Invalid sub-task number.[/bold red]")
    except (ValueError, IndexError):
        console.print("[bold red]Error: Invalid sub-task number.[/bold red]")

def delete_task(data, task_id):
    """Deletes a parent task using its global ID."""
    group, task_to_delete = find_task_by_id(data, task_id)
    if task_to_delete:
        group['tasks'].remove(task_to_delete)
        console.print(f"[yellow]Deleted task: '{task_to_delete['name']}' from group '{group['name']}'.[/yellow]")
    else:
        console.print("[bold red]Error: Invalid task ID.[/bold red]")

def view_completed_tasks(data, group_name):
    """Displays a table of completed tasks for a specific group."""
    target_group = next((g for g in data['groups'] if g['name'].lower() == group_name.lower()), None)
    if not target_group:
        console.print(f"[bold red]Error: Group '{group_name}' not found.[/bold red]")
        return

    completed_tasks = target_group.get('completed_tasks', [])
    if not completed_tasks:
        console.print(f"[yellow]No completed tasks found in group '{group_name}'.[/yellow]")
        return

    table = Table(title=f"Completed Tasks in Group: {group_name}")
    table.add_column("Name", style="dim white")
    table.add_column("Completed At", style="dim green")

    # Sort by completion date
    completed_tasks.sort(key=lambda t: t.get('completed_at'), reverse=True)

    for task in completed_tasks:
        completed_dt = datetime.datetime.fromisoformat(task['completed_at'])
        completed_display = completed_dt.strftime("%Y-%m-%d %H:%M")
        table.add_row(task['name'], completed_display)
    
    console.print(table)

def view_tasks(data, show_group=None, sort_by=None, filter_priority=None, filter_status=None, show_starred=False, filter_tag=None):
    """Displays tasks using their permanent IDs, organized by group."""
    if not data.get('groups'):
        console.print("[yellow]No groups found. Add one with 'group-add <name>'.[/yellow]")
        return

    # Check if any group matches the filter, if a filter is applied
    if show_group and not any(g['name'].lower() == show_group.lower() for g in data['groups']):
        console.print(f"[bold red]Error: Group '{show_group}' not found.[/bold red]")
        return

    for group in data['groups']:
        # If filtering by a specific group, skip groups that don't match
        if show_group and show_group.lower() != group['name'].lower():
            continue

        console.print(f"\n[bold cyan]-- Group: {group['name']} --[/bold cyan]")

        # Handle case where the group has no active tasks
        if not group['tasks']:
            console.print("[yellow]  This group has no active tasks.[/yellow]")
            continue

        # --- Filtering and Sorting ---
        tasks_to_display = group['tasks'][:]
        if show_starred:
            tasks_to_display = [t for t in tasks_to_display if t.get('starred', False)]
        if filter_priority:
            tasks_to_display = [t for t in tasks_to_display if t.get('priority') == filter_priority]
        if filter_status:
            tasks_to_display = [t for t in tasks_to_display if t.get('status') == filter_status]
        if filter_tag:
            clean_filter_tag = f"#{filter_tag.strip().lstrip('#')}"
            tasks_to_display = [t for t in tasks_to_display if clean_filter_tag in t.get('tags', [])]

        if sort_by:
            if sort_by == 'priority':
                priority_map = {'high': 1, 'medium': 2, 'low': 3}
                tasks_to_display.sort(key=lambda t: priority_map.get(t.get('priority'), 4))
            elif sort_by == 'due_date':
                tasks_to_display.sort(key=lambda t: t.get('due_date') or '9999-99-99T99:99:99')

        # Handle case where no tasks match the filters
        if not tasks_to_display:
            console.print("[yellow]  No tasks match the current filters.[/yellow]")
            continue

        # --- Display Table ---
        table = Table(show_header=True, header_style="bold magenta", border_style="dim")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Status")
        table.add_column("Name / Sub-task")
        table.add_column("Details", no_wrap=False, max_width=40)
        table.add_column("Priority", justify="center")
        table.add_column("Due", style="green")
        table.add_column("Tags", style="blue")

        for task in tasks_to_display:
            # Get the permanent ID directly from the task object
            parent_id = task['id'] 
            
            status_symbol = "✅" if task['status'] == 'done' else "⏳"
            star_symbol = "⭐ " if task.get('starred', False) else ""
            task_name_display = f"[bold]{star_symbol}{task['name']}[/bold]"
            priority_color = {'high': 'red', 'medium': 'yellow', 'low': 'cyan'}.get(task.get('priority'), 'white')
            
            due_display = "N/A"
            if task.get('due_date'):
                due_dt = datetime.datetime.fromisoformat(task['due_date'])
                due_display = due_dt.strftime("%Y-%m-%d %H:%M")

            # Format tags for display
            tags_display = ", ".join(task.get('tags', []))

            table.add_row(
                str(parent_id), 
                status_symbol, 
                task_name_display, 
                task.get('details', ''), 
                f"[{priority_color}]{task.get('priority', 'N/A').capitalize()}[/]", 
                due_display,
                tags_display # Add tags to the row
            )

            # Display sub-tasks, if any
            if task.get('sub_tasks'):
                for idx, sub_task in enumerate(task.get('sub_tasks', [])):
                    sub_status_symbol = "✅" if sub_task['status'] == 'done' else "⏳"
                    table.add_row(
                        f"{parent_id}.{idx + 1}", 
                        sub_status_symbol, 
                        f"  └── {sub_task['description']}", 
                        "", "", ""
                    )
        
        console.print(table)

def toggle_star(data, task_id, star_status: bool):
    """Stars or unstars a task by its global ID."""
    group, task = find_task_by_id(data, task_id)
    if task:
        task['starred'] = star_status
        status_text = "Starred" if star_status else "Unstarred"
        console.print(f"[green]{status_text} task '{task['name']}' in group '{group['name']}'.[/green]")
    else:
        console.print("[bold red]Error: Invalid task ID.[/bold red]")

def main():
    parser = argparse.ArgumentParser(description="Kairu: A CLI To-Do List Manager with Groups.", prog="kairu")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    # Group commands
    parser_group_add = subparsers.add_parser('group-add', help='Add a new task group')
    parser_group_add.add_argument('name', type=str, help='The name of the new group')
    parser_group_list = subparsers.add_parser('group-list', help='List all task groups')

    # Task commands
    parser_add = subparsers.add_parser('add', help='Add a new task to a group')
    parser_add.add_argument('name', type=str, help='The name/title of the task')
    parser_add.add_argument('-g', '--group', type=str, required=True, help='The group to add the task to')
    parser_add.add_argument('--details', type=str, help='Optional details about the task')
    parser_add.add_argument('-p', '--priority', type=str, default='medium', choices=['low', 'medium', 'high'], help='Priority of the task')
    parser_add.add_argument('-d', '--due', type=str, help="Set a due date using 'YYYY-MM-DD HH:MM' format")
    parser_add.add_argument('-r', '--recurring', type=str, choices=['daily', 'weekly', 'monthly'], help='Set a recurrence for the task')
    parser_add.add_argument('--tags', type=str, help='Comma-separated tags (e.g., "#urgent,#client-a")')
    
    parser_view = subparsers.add_parser('view', help='View tasks')
    parser_view.add_argument('--starred', action='store_true', help='Show only starred tasks')
    parser_view.add_argument('-g', '--group', type=str, help='Filter to show only a specific group')
    parser_view.add_argument('-s', '--sort', type=str, choices=['priority', 'due_date'], help='Sort tasks by a field')
    parser_view.add_argument('--filter-priority', type=str, choices=['low', 'medium', 'high'], help='Filter tasks by priority')
    parser_view.add_argument('--filter-status', type=str, choices=['pending', 'done'], help='Filter tasks by status')
    parser_view.add_argument('--filter-tag', type=str, help='Filter tasks by a specific tag')

    parser_done = subparsers.add_parser('done', help='Mark a parent task as done by its global ID')
    parser_done.add_argument('id', type=int, help='The global ID of the task')
    
    parser_delete = subparsers.add_parser('delete', help='Delete a parent task by its global ID')
    parser_delete.add_argument('id', type=int, help='The global ID of the task')

    # Sub-task commands
    parser_sub_add = subparsers.add_parser('sub-add', help='Add a sub-task to a parent task')
    parser_sub_add.add_argument('parent_id', type=int, help='The global ID of the parent task')
    parser_sub_add.add_argument('description', type=str, help='The description of the sub-task')
    
    parser_sub_done = subparsers.add_parser('sub-done', help='Mark a sub-task as done')
    parser_sub_done.add_argument('parent_id', type=int, help='The global ID of the parent task')
    parser_sub_done.add_argument('sub_task_id', type=int, help='The ID of the sub-task (e.g., 1 for 3.1)')

    # --- STAR/UNSTAR commands ---
    parser_star = subparsers.add_parser('star', help='Star an important task')
    parser_star.add_argument('id', type=int, help='The global ID of the task to star')
    
    parser_unstar = subparsers.add_parser('unstar', help='Unstar a task')
    parser_unstar.add_argument('id', type=int, help='The global ID of the task to unstar')
    
    parser_view_completed = subparsers.add_parser('view-completed', help='View completed/archived tasks for a group')
    parser_view_completed.add_argument('-g', '--group', type=str, required=True, help='The group whose completed tasks you want to see')

    parser_search = subparsers.add_parser('search', help='Search for a keyword across all tasks')
    parser_search.add_argument('keyword', type=str, help='The text to search for')

    # --- EDIT command ---
    parser_edit = subparsers.add_parser('edit', help='Edit an existing task')
    parser_edit.add_argument('id', type=int, help='The ID of the task to edit')
    parser_edit.add_argument('--name', type=str, help='The new name for the task')
    parser_edit.add_argument('--details', type=str, help='The new details for the task')
    parser_edit.add_argument('--priority', type=str, choices=['low', 'medium', 'high'], help='The new priority for the task')
    parser_edit.add_argument('--due', type=str, help="The new due date in 'YYYY-MM-DD HH:MM' format")
    parser_edit.add_argument('--tags', type=str, help='Set a new comma-separated list of tags')

    args = parser.parse_args()
    data = load_data()

    if args.command == 'edit':
        edit_task(data, args.id, args.name, args.details, args.priority, args.due, args.tags)
        save_data(data)
    elif args.command == 'search':
        results = search_all(data, args.keyword)
        display_search_results(results)
    elif args.command == 'view-completed':
        view_completed_tasks(data, args.group)
    elif args.command == 'view':
        view_tasks(data, args.group, args.sort, args.filter_priority, args.filter_status, args.starred, args.filter_tag)
    elif args.command == 'star':
        toggle_star(data, args.id, star_status=True)
        save_data(data)
    elif args.command == 'unstar':
        toggle_star(data, args.id, star_status=False)
        save_data(data)
    elif args.command == 'group-add':
        add_group(data, args.name)
    elif args.command == 'group-list':
        list_groups(data)
    elif args.command == 'add':
        add_task(data, args.group, args.name, args.details, args.priority, args.due, args.recurring, args.tags)
        save_data(data)
    elif args.command == 'done':
        mark_task_done(data, args.id)
    elif args.command == 'delete':
        delete_task(data, args.id)
    elif args.command == 'sub-add':
        add_sub_task(data, args.parent_id, args.description)
    elif args.command == 'sub-done':
        mark_sub_task_done(data, args.parent_id, args.sub_task_id)

    save_data(data)

if __name__ == "__main__":
    main()