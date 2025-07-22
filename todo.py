# todo.py

import argparse
import datetime
import json
import sys
import time
from dateutil.relativedelta import relativedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:
    import msvcrt # For Windows
except ImportError:
    import tty, termios # For Unix-like systems (macOS, Linux)

console = Console()
DATA_FILE = "tasks.json"
THEMES = {
    "default": {"cyan": "cyan", "magenta": "magenta", "green": "green", "yellow": "yellow", "red": "red", "blue": "blue"},
    "forest": {"cyan": "green", "magenta": "bright_green", "green": "green", "yellow": "yellow", "red": "bold red", "blue": "bright_blue"},
    "ocean": {"cyan": "blue", "magenta": "bright_blue", "green": "cyan", "yellow": "bright_yellow", "red": "bold red", "blue": "blue"}
}

THEME_COST = 20 # Cost to unlock a new theme
STREAK_FREEZE_COST = 250
# --- Theme ---
def display_themes(data):
    stats = data['user_stats']
    console.print("\n[bold]--- Theme Shop ---[/bold]")
    for theme_name in THEMES:
        status = "✅ Unlocked" if theme_name in stats['unlocked_themes'] else f"🔒 ({THEME_COST} points)"
        active = " (Active)" if theme_name == stats['active_theme'] else ""
        console.print(f"- {theme_name.capitalize()}: {status}{active}")

def unlock_theme(data, theme_name):
    stats = data['user_stats']
    theme_name = theme_name.lower()

    if theme_name not in THEMES:
        console.print("[bold red]Error: Theme not found.[/bold red]")
        return
    if theme_name in stats['unlocked_themes']:
        console.print(f"[yellow]You have already unlocked the '{theme_name}' theme.[/yellow]")
        return
    if stats['points'] < THEME_COST:
        console.print(f"[bold red]Not enough points! You need {THEME_COST} points to unlock a theme.[/bold red]")
        return

    stats['points'] -= THEME_COST
    stats['unlocked_themes'].append(theme_name)
    console.print(f"[green]Congratulations! You have unlocked the '{theme_name}' theme.[/green]")

def set_theme(data, theme_name):
    stats = data['user_stats']
    theme_name = theme_name.lower()
    if theme_name not in stats['unlocked_themes']:
        console.print(f"[bold red]Error: You have not unlocked the '{theme_name}' theme yet.[/bold red]")
        return
    
    stats['active_theme'] = theme_name
    console.print(f"[green]Active theme set to '{theme_name}'.[/green]")

# --- Data Handling ---
def display_focus_view(tasks):
    """Displays a list of tasks in a special 'Focus' table."""
    if not tasks:
        console.print("[bold green]✅ Nothing to focus on right now. Great job![/bold green]")
        return

    table = Table(title="Today's Focus")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="bold white")
    table.add_column("Group", style="yellow")
    table.add_column("Due", style="green")

    for task in tasks:
        due_display = "N/A"
        if task.get('due_date'):
            due_dt = datetime.datetime.fromisoformat(task['due_date'])
            due_display = due_dt.strftime("%H:%M") # Only show time for today's tasks
        
        table.add_row(
            str(task['id']),
            f"{'⭐ ' if task.get('starred', False) else ''}{task['name']}",
            task['group_name'],
            due_display
        )
    
    console.print(table)

def buy_streak_freeze(data):
    stats = data['user_stats']
    if stats['points'] < STREAK_FREEZE_COST:
        console.print(f"[bold red]Not enough points! You need {STREAK_FREEZE_COST} to buy a freeze.[/bold red]")
        return
    
    stats['points'] -= STREAK_FREEZE_COST
    stats['streak_freezes'] += 1
    console.print(f"[green]Streak Freeze purchased! You now have {stats['streak_freezes']}.[/green]")

def get_focus_tasks(data, focus_group_name=None):
    """Gathers tasks for the focus view based on due date, starred status, and priority."""
    focus_list = []
    seen_ids = set()
    today = datetime.date.today()

    all_tasks = []
    for group in data.get('groups', []):
        for task in group.get('tasks', []):
            task['group_name'] = group['name']
            all_tasks.append(task)
    
    # 1. Gather tasks due today
    for task in all_tasks:
        if task.get('due_date'):
            due_date = datetime.datetime.fromisoformat(task['due_date']).date()
            if due_date == today and task['id'] not in seen_ids:
                focus_list.append(task)
                seen_ids.add(task['id'])

    # 2. Gather all starred tasks
    for task in all_tasks:
        if task.get('starred', False) and task['id'] not in seen_ids:
            focus_list.append(task)
            seen_ids.add(task['id'])

    # --- New Logic: Gather all high-priority tasks ---
    for task in all_tasks:
        if task.get('priority') == 'high' and task['id'] not in seen_ids:
            focus_list.append(task)
            seen_ids.add(task['id'])

    # 4. Gather next task from a specific group
    if focus_group_name:
        target_group = next((g for g in data['groups'] if g['name'].lower() == focus_group_name.lower()), None)
        if target_group and target_group['tasks']:
            priority_map = {'high': 1, 'medium': 2, 'low': 3}
            sorted_tasks = sorted(target_group['tasks'], key=lambda t: priority_map.get(t.get('priority'), 4))
            if sorted_tasks and sorted_tasks[0]['id'] not in seen_ids:
                focus_list.append(sorted_tasks[0])
                seen_ids.add(sorted_tasks[0]['id'])
    
    return focus_list

def get_level(points):
    """Determines the user's level based on their total points."""
    if points < 100:
        return "Novice"
    elif points < 250:
        return "Apprentice"
    elif points < 500:
        return "Task Master"
    elif points < 1000:
        return "Productivity Pro"
    else:
        return "Focus Guru"
    
def load_data():
    """Loads the entire data structure, safely adding new fields if they don't exist."""
    try:
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"last_task_id": 0, "groups": []}

    # Safely initialize the user_stats object and its new fields
    if 'user_stats' not in data:
        data['user_stats'] = {}
    
    if 'goals' not in data:
        data['goals'] = []

    stats = data['user_stats']
    stats.setdefault('points', 0)
    stats.setdefault('level', 'Novice')
    stats.setdefault('streak', 0)
    stats.setdefault('last_completed_date', None)
    stats.setdefault('streak_freezes', 0)
    stats.setdefault('active_theme', 'default')
    stats.setdefault('unlocked_themes', ['default'])
    stats.setdefault('achievements', {
        "planner": False,
        "on_a_roll": False, # For a 3-day streak
        "high_achiever": False, # For 10 high-priority tasks
        "delegator": False
    })

    # We also need a counter for high-priority tasks
    stats.setdefault('high_priority_completed', 0)

    return data

def save_data(data):
    """Saves the entire data structure to the JSON file."""
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def start_pomodoro(work_minutes=25, break_minutes=5):
    """Starts an interactive Pomodoro timer with pause, resume, and stop controls."""
    
    def get_char_non_blocking():
        """Gets a single character from the user without blocking."""
        if sys.platform == "win32":
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8')
        else:
            # Unix-like system logic
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                [i, o, e] = select.select([sys.stdin], [], [], 0.1)
                if i:
                    return sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return None

    def run_timer(duration_minutes, session_type):
        """Helper function to run a single timer session (work or break)."""
        duration_seconds = duration_minutes * 60
        state = 'running'

        while duration_seconds > 0 and state != 'stopped':
            char = get_char_non_blocking()
            
            # --- The Fix is Here ---
            if char == 'p' and state == 'running': # Only pause if running
                state = 'paused'
                console.print("\n[yellow]Timer paused. Press 'c' to continue or 's' to stop.[/yellow]")
            elif char == 'c' and state == 'paused': # Only continue if paused
                state = 'running'
                console.print("\n[green]Timer resumed.[/green]")
            elif char == 's':
                state = 'stopped'
                console.print("\n[bold red]Timer stopped.[/bold red]")
                break

            if state == 'running':
                mins, secs = divmod(duration_seconds, 60)
                timer_display = f"{session_type} session: {mins:02d}:{secs:02d}"
                print(timer_display, end="\r")
                time.sleep(1)
                duration_seconds -= 1
        
        return state

    # --- Main Pomodoro Logic ---
    console.print(f"[bold green]🍅 Pomodoro started! Press 'p' to pause, 's' to stop.[/bold green]")
    final_state = run_timer(work_minutes, "Work")
    if final_state != 'stopped':
        console.print("\n[bold yellow]🔔 Work session over! Time for a short break.[/bold yellow]")
        run_timer(break_minutes, "Break")
        console.print("\n[bold green]✅ Pomodoro complete! Ready for the next session.[/bold green]")

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

def display_single_task_view(data, task_id, show_log=False):
    """Displays a detailed panel for a single task."""
    group, task = find_task_by_id(data, task_id)
    if not task:
        console.print(f"[bold red]Error: Task ID {task_id} not found.[/bold red]")
        return
    
    # --- Build the main description ---
    star = "⭐ " if task.get('starred', False) else ""
    title = f"{star}{task['name']}"
    
    details_text = (
        f"ID: {task['id']}\n"
        f"Group: {group['name']}\n"
        f"Status: {task['status'].capitalize()}\n"
        f"Priority: {task.get('priority', 'N/A').capitalize()}\n"
        f"Due: {datetime.datetime.fromisoformat(task['due_date']).strftime('%Y-%m-%d %H:%M') if task.get('due_date') else 'N/A'}\n"
        f"Tags: {', '.join(task.get('tags', []))}\n"
        f"Details: {task.get('details', 'No details.')}"
    )
    
    console.print(Panel(details_text, title=title, border_style="green"))

    # --- Show the progress log if requested ---
    if show_log:
        log = task.get('log', [])
        if not log:
            console.print("[yellow]No progress log found for this task.[/yellow]")
            return
            
        log_table = Table(title="📝 Progress Log")
        log_table.add_column("Timestamp", style="dim")
        log_table.add_column("Note")

        for entry in log:
            ts = datetime.datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
            log_table.add_row(ts, entry['note'])
        
        console.print(log_table)

def display_stats(data):
    """Displays user's progress stats, level, streak, freezes, and achievements."""
    stats = data.get('user_stats', {})

    # --- Calculate Aggregate Stats ---
    # 1. Total completed tasks (all time)
    total_completed = 0
    for group in data.get('groups', []):
        total_completed += len(group.get('completed_tasks', []))

    # 2. Tasks completed today
    today = datetime.date.today()
    completed_today_count = 0
    for group in data.get('groups', []):
        for task in group.get('completed_tasks', []):
            completed_at_str = task.get('completed_at')
            if completed_at_str:
                completed_date = datetime.datetime.fromisoformat(completed_at_str).date()
                if completed_date == today:
                    completed_today_count += 1
    
    # --- Build the Display String ---
    stats_text = (
        f"🏆 Total Points: [bold cyan]{stats.get('points', 0)}[/bold cyan]\n"
        f"🏅 Current Level: [bold yellow]{stats.get('level', 'Novice')}[/bold yellow]\n"
        f"🔥 Current Streak: [bold red]{stats.get('streak', 0)} day(s)[/bold red]\n"
        f"🧊 Streak Freezes: [bold blue]{stats.get('streak_freezes', 0)} available[/bold blue]\n\n"
        f"✅ Tasks Completed (Today): [bold green]{completed_today_count}[/bold green]\n"
        f"✅ Tasks Completed (All Time): [bold green]{total_completed}[/bold green]"
    )
    
    # --- Add Achievements Section (if any) ---
    unlocked_achievements = []
    for name, unlocked in stats.get('achievements', {}).items():
        if unlocked:
            # Format the name for display, e.g., 'high_achiever' -> 'High Achiever'
            display_name = name.replace('_', ' ').title()
            unlocked_achievements.append(display_name)

    if unlocked_achievements:
        stats_text += "\n\n🎖️ Achievements: " + ", ".join(unlocked_achievements)
    
    # --- Create and Print the Panel ---
    panel = Panel(stats_text, title="📊 Your Kairu Stats", border_style="bright_blue", expand=False)
    console.print(panel)

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

def plan_day(data):
    """A guided routine to select top priorities from a smart-filtered list."""
    console.print("\n[bold green]☀️ Let's plan your day! Here are your top candidates:[/bold green]")
    
    # Get a smart list of tasks instead of all of them
    candidate_tasks = get_focus_tasks(data)

    if not candidate_tasks:
        console.print("[yellow]You have no urgent or starred tasks to plan. Feel free to add some![/yellow]")
        return
    
    # Display the curated list for selection
    view_table = Table(title="Top Candidates for Today")
    view_table.add_column("ID", style="cyan")
    view_table.add_column("Name")
    view_table.add_column("Group")
    for task in candidate_tasks:
        view_table.add_row(str(task['id']), task['name'], task['group_name'])
    console.print(view_table)

    # Clear existing stars (optional)
    if console.input("\n[bold]Clear all other stars first? (y/n): [/bold]").lower() == 'y':
        for group in data.get('groups', []):
            for task in group.get('tasks', []):
                task['starred'] = False
        console.print("[yellow]Cleared all stars.[/yellow]")

    # Get user's top priorities from the candidate list
    id_string = console.input("[bold]Enter the IDs of up to 3 tasks to star as today's priorities: [/bold]")
    try:
        priority_ids = [int(i.strip()) for i in id_string.split(',') if i.strip()]
        if not priority_ids: return

        for task_id in priority_ids:
            group, task = find_task_by_id(data, task_id)
            if task:
                task['starred'] = True
            else:
                console.print(f"[yellow]Warning: Task ID {task_id} not found.[/yellow]")
        
        # Award achievement if it's the first time
        if not data['user_stats']['achievements']['planner']:
            data['user_stats']['achievements']['planner'] = True
            console.print("[bold magenta]🏆 Achievement Unlocked: The Planner![/bold magenta]")
        
        console.print("\n[bold green]Priorities starred! Good luck today.[/bold green]")

    except ValueError:
        console.print("[bold red]Invalid input. Please enter numbers separated by commas.[/bold red]")

def find_stale_task(data, stale_days=14):
    """Finds the oldest active task that has not been modified."""
    stale_tasks = []
    today = datetime.datetime.now()

    for group in data.get('groups', []):
        for task in group.get('tasks', []):
            # Ignore recurring tasks
            if task.get('recurring'):
                continue
            
            created_date = datetime.datetime.fromisoformat(task['created_at'])
            if (today - created_date).days >= stale_days:
                stale_tasks.append(task)
    
    # Return the oldest one if any are found
    if stale_tasks:
        stale_tasks.sort(key=lambda t: t['created_at'])
        return stale_tasks[0]
    return None

def unstuck_routine(data):
    """A guided routine to help the user take action on a single stale task."""
    console.print("\n[bold cyan]🔍 Let's find a task that might be stuck...[/bold cyan]")
    stale_task = find_stale_task(data)

    if not stale_task:
        console.print("[green]No stale tasks found. Your list is fresh![/green]")
        return

    # Find group for context
    group_name = find_group_for_task(data, stale_task['id'])
    
    console.print(f"\nTask [bold]'{stale_task['name']}'[/bold] in group [yellow]'{group_name}'[/yellow] was created on {datetime.datetime.fromisoformat(stale_task['created_at']).date()}.")
    
    # --- The Interactive Prompt ---
    action = console.input("[bold]What's the next action? ([B]reak down, [R]eschedule, [D]elete, [S]kip): [/bold]").lower().strip()

    if action == 'b': # Break Down
        console.print("Breaking it down is a great way to start. What is the very first step?")
        sub_desc = console.input("First sub-task: ")
        if sub_desc:
            add_sub_task(data, stale_task['id'], sub_desc)
            console.print("Great start! The task is now broken down. You can add more sub-tasks with 'sub-add'.")
    
    elif action == 'r': # Reschedule
        new_due = console.input("When do you want to work on this? (YYYY-MM-DD HH:MM): ")
        edit_task(data, stale_task['id'], new_due_date=new_due)
    
    elif action == 'd': # Delete
        if console.input(f"Are you sure you want to delete '{stale_task['name']}'? (y/n): ").lower() == 'y':
            delete_task(data, stale_task['id'])
    
    elif action == 's': # Skip
        console.print("Okay, we'll leave it for now.")
    
    else:
        console.print("[yellow]Invalid option. No action taken.[/yellow]")

# We also need a small helper to find a task's group name for the display
def find_group_for_task(data, task_id):
    """Finds the group name for a given task ID."""
    for group in data.get('groups', []):
        for task in group.get('tasks', []) + group.get('completed_tasks', []):
            if task['id'] == task_id:
                return group['name']
    return "N/A"

def shutdown_routine(data):
    """A guided routine to review accomplishments, reschedule, and reflect."""
    console.print("\n[bold green]🌙 Let's wrap up the day.[/bold green]")
    today = datetime.date.today()
    
    # 1. Show accomplishments (no change here)
    accomplished_today = []
    for group in data.get('groups', []):
        for task in group.get('completed_tasks', []):
            completed_date = datetime.datetime.fromisoformat(task['completed_at']).date()
            if completed_date == today:
                accomplished_today.append(task)

    if accomplished_today:
        accomplished_panel = Panel("\n".join(f"- {t['name']}" for t in accomplished_today), 
                                   title="✅ Accomplished Today", border_style="green")
        console.print(accomplished_panel)
    else:
        console.print("[yellow]No tasks were completed today.[/yellow]")

    # 2. Review and reschedule pending tasks
    pending_tasks = []
    for group in data.get('groups', []):
        pending_tasks.extend(group.get('tasks', []))

    if not pending_tasks:
        console.print("\n[bold green]All tasks cleared. You're all done! 🎉[/bold green]")
        return
    
    console.print("\n[bold yellow]-- ⏳ Pending Tasks --[/bold yellow]")
    for task in pending_tasks:
        console.print(f"  ID {task['id']}: {task['name']}")
    
    # --- New: Bulk Reschedule Option ---
    if console.input(f"\n[bold]Move all {len(pending_tasks)} pending tasks to tomorrow at 9 AM? (y/n): [/bold]").lower() == 'y':
        tomorrow = datetime.datetime.now().date() + datetime.timedelta(days=1)
        tomorrow_9am_str = tomorrow.strftime("%Y-%m-%d 09:00")
        for task in pending_tasks:
            # Reuse the existing edit_task function!
            edit_task(data, task['id'], new_due_date=tomorrow_9am_str)
        console.print(f"[green]All pending tasks have been rescheduled.[/green]")
    else:
        # --- Existing Manual Reschedule Loop ---
        while True:
            action = console.input("\n[bold]Enter a task ID to reschedule, or type 'done' to finish: [/bold]").lower().strip()
            if action == 'done':
                break
            try:
                task_id_to_edit = int(action)
                new_due_date = console.input(f"Enter new due date for task #{task_id_to_edit} (YYYY-MM-DD HH:MM): ")
                edit_task(data, task_id_to_edit, new_due_date=new_due_date)
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number or 'done'.[/bold red]")
    
    # --- New: Reflection Step ---
    console.print("\n[bold]--- Daily Report ---[/bold]")
    display_stats(data) # Reuse the stats display!
    console.input("\nWhat was one win today? (Press Enter to finish): ")
            
    console.print("\n[bold green]Shutdown routine complete. Well done today! 👏[/bold green]")

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

def edit_task(data, task_id, new_name=None, new_details=None, new_priority=None, new_due_date=None, new_tags_string=None, new_goal=None):
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
    if new_goal is not None:
        if new_goal.lower() == 'none':
            task['goal'] = None
        elif any(g['name'].lower() == new_goal.lower() for g in data['goals']):
            task['goal'] = new_goal
        else:
            console.print(f"[bold red]Error: Goal '{new_goal}' not found. No changes saved.[/bold red]")
            return
        
    console.print(f"[green]Successfully updated task #{task_id}.[/green]")

# --- Task & Sub-task Management ---
def add_task(data, group_name, name, details=None, priority='medium', due_date=None, recurring=None, tags_string=None, goal_name=None):
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

    # --- New: Goal Validation ---
    if goal_name and not any(g['name'].lower() == goal_name.lower() for g in data['goals']):
        console.print(f"[bold red]Error: Goal '{goal_name}' not found. Create it first with 'goal-add'.[/bold red]")
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
                "tags": parse_tags(tags_string),
                "goal": goal_name
                }
    
    target_group['tasks'].append(new_task)
    console.print(f"[green]Added task '{name}' (ID: {new_id}) to group '{target_group['name']}'.[/green]")

def add_sub_task(data, parent_id, description):
    """Adds a sub-task to a parent task using its permanent ID."""
    group, task = find_task_by_id(data, parent_id)

    if not task:
        console.print("[bold red]Error: Invalid parent task ID.[/bold red]")
        return

    # Create the new sub-task
    sub_task = {"description": description, "status": "pending"}
    
    # Safely append the sub-task (creates the list if it somehow doesn't exist)
    task.setdefault('sub_tasks', []).append(sub_task)
    
    # Check for and award the "Delegator" achievement on first use
    if not data['user_stats']['achievements']['delegator']:
        data['user_stats']['achievements']['delegator'] = True
        console.print("[bold magenta]🏆 Achievement Unlocked: The Delegator![/bold magenta]")
        
    console.print(f"[green]Added sub-task to '{task['name']}'.[/green]")

def add_goal(data, name, description=None):
    if any(g['name'].lower() == name.lower() for g in data['goals']):
        console.print(f"[bold red]Error: Goal '{name}' already exists.[/bold red]")
        return
    
    new_goal = {"name": name, "description": description}
    data['goals'].append(new_goal)
    console.print(f"[green]Added new goal: '{name}'[/green]")

def list_goals(data):
    if not data['goals']:
        console.print("[yellow]No goals defined. Use 'goal-add' to create one.[/yellow]")
        return
    
    table = Table(title="Your Long-Term Goals")
    table.add_column("Name", style="bold cyan")
    table.add_column("Description", style="white")

    for goal in data['goals']:
        table.add_row(goal['name'], goal.get('description', ''))
    
    console.print(table)

def plan_day(data):
    """A guided routine to select top priorities from a smart-filtered list."""
    console.print("\n[bold green]☀️ Let's plan your day! Here are your top candidates:[/bold green]")
    
    # Get a smart list of tasks instead of all of them
    candidate_tasks = get_focus_tasks(data)

    if not candidate_tasks:
        console.print("[yellow]You have no urgent or starred tasks to plan. Feel free to add some![/yellow]")
        return
    
    # Display the curated list for selection
    view_table = Table(title="Top Candidates for Today")
    view_table.add_column("ID", style="cyan")
    view_table.add_column("Name")
    view_table.add_column("Group")
    for task in candidate_tasks:
        view_table.add_row(str(task['id']), task['name'], task['group_name'])
    console.print(view_table)

    # Clear existing stars (optional)
    if console.input("\n[bold]Clear all other stars first? (y/n): [/bold]").lower() == 'y':
        for group in data.get('groups', []):
            for task in group.get('tasks', []):
                task['starred'] = False
        console.print("[yellow]Cleared all stars.[/yellow]")

    # Get user's top priorities from the candidate list
    id_string = console.input("[bold]Enter the IDs of up to 3 tasks to star as today's priorities: [/bold]")
    try:
        priority_ids = [int(i.strip()) for i in id_string.split(',') if i.strip()]
        if not priority_ids: return

        for task_id in priority_ids:
            group, task = find_task_by_id(data, task_id)
            if task:
                task['starred'] = True
            else:
                console.print(f"[yellow]Warning: Task ID {task_id} not found.[/yellow]")
        
        # Award achievement if it's the first time
        if not data['user_stats']['achievements']['planner']:
            data['user_stats']['achievements']['planner'] = True
            console.print("[bold magenta]🏆 Achievement Unlocked: The Planner![/bold magenta]")
        
        console.print("\n[bold green]Priorities starred! Good luck today.[/bold green]")

    except ValueError:
        console.print("[bold red]Invalid input. Please enter numbers separated by commas.[/bold red]")

def mark_task_done(data, task_id):
    """Handles task completion, applying gamification and then either rescheduling or archiving."""
    group, task = find_task_by_id(data, task_id)

    if not task:
        console.print("[bold red]Error: Task ID not found.[/bold red]")
        return
    
    if task in group.get('completed_tasks', []):
        console.print(f"[yellow]Task '{task['name']}' is already completed.[/yellow]")
        return

    # --- Step 1: Gamification (runs for ALL completed tasks) ---
    stats = data['user_stats']
    points_earned = 10  # Base points

    if task.get('priority') == 'high':
        points_earned += 10
    elif task.get('priority') == 'medium':
        points_earned += 5
    
    if task.get('due_date') and datetime.datetime.now() <= datetime.datetime.fromisoformat(task['due_date']):
        points_earned += 15 # On-time bonus

    stats['points'] += points_earned

    # Check for High Achiever achievement
    if task.get('priority') == 'high':
        stats['high_priority_completed'] = stats.get('high_priority_completed', 0) + 1
        if stats['high_priority_completed'] >= 10 and not stats['achievements']['high_achiever']:
            stats['achievements']['high_achiever'] = True
            console.print("[bold magenta]🏆 Achievement Unlocked: High Achiever![/bold magenta]")

    # Update streak logic with freeze protection
    today_str = datetime.date.today().isoformat()
    if stats.get('last_completed_date'):
        last_completed = datetime.date.fromisoformat(stats['last_completed_date'])
        delta = datetime.date.today() - last_completed
        if delta.days == 1:
            stats['streak'] += 1
        elif delta.days > 1:
            if stats['streak_freezes'] > 0:
                stats['streak_freezes'] -= 1
                console.print(f"[cyan]A day was missed, but your streak was saved by a freeze! You have {stats['streak_freezes']} left.[/cyan]")
            else:
                stats['streak'] = 1  # Reset streak
    else:
        stats['streak'] = 1 # Start streak
    
    stats['last_completed_date'] = today_str

    # Check for On a Roll achievement
    if stats['streak'] >= 3 and not stats['achievements']['on_a_roll']:
        stats['achievements']['on_a_roll'] = True
        console.print("[bold magenta]🏆 Achievement Unlocked: On a Roll![/bold magenta]")

    # Update user level
    stats['level'] = get_level(stats['points'])

    # --- Step 2: Reschedule or Archive ---
    if task.get('recurring') and task.get('due_date'):
        # This is a recurring task: update its due date
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
        console.print(f"[green]Recurring task '{task['name']}' completed! You earned [bold]{points_earned}[/bold] points. Rescheduled.[/green]")
    else:
        # This is a normal task: archive it
        task['status'] = 'done'
        task['completed_at'] = datetime.datetime.now().isoformat()
        
        if task in group['tasks']:
            group['tasks'].remove(task)
        
        group['completed_tasks'].append(task)
        console.print(f"[green]Completed '{task['name']}'! You earned [bold]{points_earned}[/bold] points. Task archived.[/green]")

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

def display_tasks_by_goal(data, active_theme):
    """A special view function to display tasks organized under their parent goals."""
    console.print("\n[bold magenta]--- Tasks Organized by Goal ---[/bold magenta]")
    
    tasks_by_goal = {goal['name']: [] for goal in data['goals']}
    tasks_by_goal['Unassigned'] = []

    # Collate tasks under their respective goals
    for group in data['groups']:
        for task in group['tasks']:
            goal_name = task.get('goal')
            if goal_name in tasks_by_goal:
                tasks_by_goal[goal_name].append(task)
            else:
                tasks_by_goal['Unassigned'].append(task)

    # Display the collated tasks
    for goal_name, tasks in tasks_by_goal.items():
        if not tasks: continue

        title_color = "cyan" if goal_name != "Unassigned" else "yellow"
        panel = Panel("\n".join(f"- (ID {t['id']}) {t['name']}" for t in tasks), 
                      title=f"🎯 Goal: {goal_name}", 
                      border_style=active_theme[title_color])
        console.print(panel)

def view_tasks(data, active_theme, group_by='group', task_id=None, show_log=False, show_group=None, sort_by=None, filter_priority=None, filter_status=None, show_starred=False, filter_tag=None):
    # --- New: Handle single task view ---
    if task_id:
        display_single_task_view(data, task_id, show_log)
        return
    
    if group_by == 'goal':
        display_tasks_by_goal(data, active_theme)
        return
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

def log_progress(data, task_id, message):
    """Adds a timestamped progress note to a specific task."""
    group, task = find_task_by_id(data, task_id)
    if not task:
        console.print(f"[bold red]Error: Task ID {task_id} not found.[/bold red]")
        return

    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "note": message
    }
    
    # setdefault safely creates the 'log' list if it's a new task
    task.setdefault('log', []).append(log_entry)
    console.print(f"[green]Progress logged for task #{task_id}: '{task['name']}'.[/green]")

def run_health_check(data):
    """Analyzes today's tasks and provides feedback on workload balance."""
    console.print("\n[bold cyan]🩺 Running a Health Check on Your Day...[/bold cyan]")
    
    # --- 1. Gather all tasks scheduled for today ---
    today = datetime.date.today()
    tasks_today = []
    for group in data.get('groups', []):
        for task in group.get('tasks', []):
            if task.get('due_date'):
                due_date = datetime.datetime.fromisoformat(task['due_date']).date()
                if due_date == today:
                    tasks_today.append(task)

    if not tasks_today:
        console.print(Panel("[bold green]Your schedule for today is clear. A great time to plan or rest![/bold green]", 
                        title="Health Check Complete", border_style="green"))
        return

    # --- 2. Analyze the day's schedule ---
    high_priority_count = 0
    rest_task_count = 0
    for task in tasks_today:
        if task.get('priority') == 'high':
            high_priority_count += 1
        if '#rest' in task.get('tags', []):
            rest_task_count += 1
            
    # --- 3. Generate Feedback ---
    feedback_text = (
        f"You have [bold]{len(tasks_today)}[/bold] tasks scheduled for today.\n"
        f"- [bold cyan]{high_priority_count}[/bold cyan] are high priority.\n"
        f"- You have scheduled [bold green]{rest_task_count}[/bold green] breaks."
    )
    
    advice = ""
    # Define a threshold for a "busy day"
    HIGH_PRIORITY_THRESHOLD = 4
    if high_priority_count >= HIGH_PRIORITY_THRESHOLD and rest_task_count == 0:
        advice = "[bold yellow]Warning: A high number of priority tasks are scheduled with no breaks. To avoid burnout, consider adding some downtime with '--tags \"#rest\"'.[/bold yellow]"
    elif rest_task_count > 0:
        advice = "[bold green]Great job scheduling breaks! This is key to sustainable productivity.[/bold green]"
    else:
        advice = "[bold cyan]Your schedule looks manageable. Have a productive day![/bold cyan]"
        
    final_text = f"{feedback_text}\n\n{advice}"
    
    console.print(Panel(final_text, title="Health Check Complete", border_style="blue"))

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
    parser_add.add_argument('--goal', type=str, help='Link task to a long-term goal')

    parser_view = subparsers.add_parser('view', help='View tasks')
    parser_view.add_argument('id', type=int, nargs='?', default=None, help='(Optional) View a specific task by its ID')
    parser_view.add_argument('--show-log', action='store_true', help='Show the progress log for a specific task')
    parser_view.add_argument('--starred', action='store_true', help='Show only starred tasks')
    parser_view.add_argument('-g', '--group', type=str, help='Filter to show only a specific group')
    parser_view.add_argument('-s', '--sort', type=str, choices=['priority', 'due_date'], help='Sort tasks by a field')
    parser_view.add_argument('--filter-priority', type=str, choices=['low', 'medium', 'high'], help='Filter tasks by priority')
    parser_view.add_argument('--filter-status', type=str, choices=['pending', 'done'], help='Filter tasks by status')
    parser_view.add_argument('--filter-tag', type=str, help='Filter tasks by a specific tag')
    parser_view.add_argument('--group-by', type=str, default='group', choices=['group', 'goal'], help='How to organize the task view')
    
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
    parser_edit.add_argument('--goal', type=str, help="Link to a new goal or type 'none' to unlink")

    # --- POMODORO command ---
    parser_pomodoro = subparsers.add_parser('pomodoro', help='Start a Pomodoro focus timer')
    parser_pomodoro.add_argument('-w', '--work', type=int, default=25, help='Duration of the work session in minutes (default: 25)')
    parser_pomodoro.add_argument('-b', '--breaks', type=int, default=5, help='Duration of the break in minutes (default: 5)')

    # --- FOCUS command ---
    parser_focus = subparsers.add_parser('focus', help="Show a focused view of what's important now")
    parser_focus.add_argument('-g', '--group', type=str, help='Include the next task from a specific group')

    parser_stats = subparsers.add_parser('stats', help='Show your productivity stats')

    # --- New Guided Commands ---
    parser_plan = subparsers.add_parser('plan-day', help='Start a guided daily planning session')
    parser_shutdown = subparsers.add_parser('shutdown', help='Start a guided end-of-day shutdown routine')
    
    # --- Gamification Commands ---
    parser_themes = subparsers.add_parser('themes', help='View and manage themes')
    parser_unlock = subparsers.add_parser('unlock-theme', help='Unlock a new theme with points')
    parser_unlock.add_argument('name', type=str, help='The name of the theme to unlock')
    parser_set_theme = subparsers.add_parser('set-theme', help='Set your active theme')
    parser_set_theme.add_argument('name', type=str, help='The name of the theme to activate')
    parser_buy_freeze = subparsers.add_parser('buy-freeze', help='Buy a streak freeze to protect your streak')

    # --- GOAL commands ---
    parser_goal_add = subparsers.add_parser('goal-add', help='Add a new long-term goal')
    parser_goal_add.add_argument('name', type=str, help='The name of the goal')
    parser_goal_add.add_argument('description', type=str, nargs='?', default=None, help='Optional description of the goal')
    parser_goal_list = subparsers.add_parser('goal-list', help='List all goals')
    
    # --- New Proactive Command ---
    parser_unstuck = subparsers.add_parser('unstuck', help='Start an interactive session to deal with a stale task')

    # --- LOG command ---
    parser_log = subparsers.add_parser('log', help='Log progress on a specific task')
    parser_log.add_argument('id', type=int, help='The ID of the task to log progress on')
    parser_log.add_argument('-m', '--message', type=str, required=True, help='The progress note')

    # --- New Proactive Command ---
    parser_health = subparsers.add_parser('health-check', help='Analyze your daily schedule for burnout risk')

    args = parser.parse_args()
    data = load_data()

    # Load the active theme to be used for all printing
    active_theme = THEMES.get(data['user_stats']['active_theme'], THEMES['default'])

    if args.command == 'log':
        log_progress(data, args.id, args.message)
        save_data(data)
    elif args.command == 'view':
        # Pass the new arguments to the view function
        view_tasks(data, active_theme, task_id=args.id, show_log=args.show_log, group_by=args.group_by, 
                   show_group=args.group, sort_by=args.sort, filter_priority=args.filter_priority, filter_status=args.filter_status, show_starred=args.starred, filter_tag=args.filter_tag)
    elif args.command == 'health-check':
        run_health_check(data)
    elif args.command == 'unstuck':
        unstuck_routine(data)
        save_data(data)
    elif args.command == 'themes':
        display_themes(data)
    elif args.command == 'goal-add':
        add_goal(data, args.name, args.description)
        save_data(data)
    elif args.command == 'goal-list':
        list_goals(data)
    elif args.command == 'unlock-theme':
        unlock_theme(data, args.name)
    elif args.command == 'set-theme':
        set_theme(data, args.name)
    elif args.command == 'buy-freeze':
        buy_streak_freeze(data)
    elif args.command == 'plan-day':
        plan_day(data)
        save_data(data)
    elif args.command == 'shutdown':
        shutdown_routine(data)
        save_data(data)
    elif args.command == 'stats':
        display_stats(data)
    elif args.command == 'focus':
        focus_tasks = get_focus_tasks(data, args.group)
        display_focus_view(focus_tasks)
    elif args.command == 'pomodoro':
        start_pomodoro(args.work, args.breaks)
    elif args.command == 'edit':
        edit_task(data, args.id, args.name, args.details, args.priority, args.due, args.tags, args.goal)
        save_data(data)
    elif args.command == 'search':
        results = search_all(data, args.keyword)
        display_search_results(results)
    elif args.command == 'view-completed':
        view_completed_tasks(data, args.group)
    elif args.command == 'view':
        view_tasks(data, active_theme, args.group_by, args.group, args.sort, args.filter_priority, args.filter_status, args.starred, args.filter_tag)
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
        add_task(data, args.group, args.name, args.details, args.priority, args.due, args.recurring, args.tags, args.goal)
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