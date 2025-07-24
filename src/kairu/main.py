import argparse
import datetime
import sys
import time
from models import ToDoList
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:
    import msvcrt # For Windows
except ImportError:
    import tty, termios # For Unix-like systems (macOS, Linux)

DATA_FILE = "tasks.json"
THEMES = {
    "default": {"cyan": "cyan", "magenta": "magenta", "green": "green", "yellow": "yellow", "red": "red", "blue": "blue"},
    "forest": {"cyan": "green", "magenta": "bright_green", "green": "green", "yellow": "yellow", "red": "bold red", "blue": "bright_blue"},
    "ocean": {"cyan": "blue", "magenta": "bright_blue", "green": "cyan", "yellow": "bright_yellow", "red": "bold red", "blue": "blue"}
}
THEME_COST = 500

console = Console()

# UI Display & Interactive Functions
def display_single_task_view(task, group_name, active_theme, show_log=False):
    star = "⭐ " if task.starred else ""
    title = f"{star}{task.name}"
    
    details_text = (
        f"ID: {task.id}\n"
        f"Group: {group_name}\n"
        f"Status: {task.status.capitalize()}\n"
        f"Priority: {task.priority.capitalize()}\n"
        f"Due: {datetime.datetime.fromisoformat(task.due_date).strftime('%Y-%m-%d %H:%M') if task.due_date else 'N/A'}\n"
        f"Tags: {', '.join(task.tags)}\n"
        f"Details: {task.details or 'No details.'}"
    )
    
    console.print(Panel(details_text, title=title, border_style="green"))

    # --- Show the progress log if requested ---
    if show_log:
        log = task.log
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

def display_tasks_by_goal(all_tasks, all_goals, active_theme):
    """A special view function to display tasks organized under their parent goals."""
    console.print("\n[bold magenta]--- Tasks Organized by Goal ---[/bold magenta]")
    
    tasks_by_goal = {goal['name']: [] for goal in all_goals}
    tasks_by_goal['Unassigned'] = []

    # Collate tasks under their respective goals
    for task in all_tasks:
        goal_name = task.goal
        if goal_name in tasks_by_goal:
            tasks_by_goal[goal_name].append(task)
        else:
            tasks_by_goal['Unassigned'].append(task)

    # Display the collated tasks
    for goal_name, tasks in tasks_by_goal.items():
        if not tasks: continue

        title_color = "cyan" if goal_name != "Unassigned" else "yellow"
        panel = Panel("\n".join(f"- (ID {t.id}) {t.name}" for t in tasks), 
                      title=f"🎯 Goal: {goal_name}", 
                      border_style=active_theme[title_color])
        console.print(panel)
        
def display_tasks_by_group(all_groups, active_theme, show_group=None, sort_by=None, filter_priority=None, filter_status=None, show_starred=False, filter_tag=None):
    for group in all_groups:
        if show_group and show_group.lower() != group['name'].lower():
            continue

        console.print(f"\n[bold {active_theme['cyan']}]-- Group: {group['name']} --[/bold {active_theme['cyan']}]")

        if not group['tasks']:
            console.print(f"[yellow]  This group has no active tasks.[/yellow]")
            continue

        tasks_to_display = group['tasks'][:]
        if show_starred:
            tasks_to_display = [t for t in tasks_to_display if t.starred]
        if filter_priority:
            tasks_to_display = [t for t in tasks_to_display if t.priority == filter_priority]
        if filter_status:
            tasks_to_display = [t for t in tasks_to_display if t.status == filter_status]
        if filter_tag:
            clean_filter_tag = f"#{filter_tag.strip().lstrip('#')}"
            tasks_to_display = [t for t in tasks_to_display if clean_filter_tag in t.tags]
        
        if not tasks_to_display:
            console.print("[yellow]  No tasks match the current filters.[/yellow]")
            continue

        table = Table(show_header=True, header_style=f"bold {active_theme['magenta']}", border_style="dim")
        table.add_column("ID", style=active_theme['cyan'], justify="right")
        table.add_column("Status")
        table.add_column("Name / Sub-task")
        table.add_column("Due", style=active_theme['green'])
        table.add_column("Tags", style=active_theme['blue'])
        for task in tasks_to_display:
            status_symbol = "✅" if task.status == 'done' else "⏳"
            star_symbol = "⭐ " if task.starred else ""
            task_name_display = f"[bold]{star_symbol}{task.name}[/bold]"
            due_display = datetime.datetime.fromisoformat(task.due_date).strftime('%Y-%m-%d %H:%M') if task.due_date else "N/A"
            tags_display = ", ".join(task.tags)
            table.add_row(str(task.id), status_symbol, task_name_display, due_display, tags_display)
            for idx, sub_task in enumerate(task.sub_tasks):
                sub_status_symbol = "✅" if sub_task['status'] == 'done' else "⏳"
                table.add_row(f"{task.id}.{idx + 1}", sub_status_symbol, f"  └── {sub_task['description']}", "", "")
        console.print(table)

def display_themes():
    stats = display_themes()
    console.print("\n[bold]--- Theme Shop ---[/bold]")
    for theme_name in THEMES:
        status = "✅ Unlocked" if theme_name in stats['unlocked_themes'] else f"🔒 ({THEME_COST} points)"
        active = " (Active)" if theme_name == stats['active_theme'] else ""
        console.print(f"- {theme_name.capitalize()}: {status}{active}")

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
            f"{'⭐ ' if task.get('starred', False) else ''}{task.name}",
            task['group_name'],
            due_display
        )
    
    console.print(table)

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
            f"{'⭐ ' if task.get('starred', False) else ''}{task.name}",
            task['group_name'],
            due_display
        )
    
    console.print(table)

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

# In main.py

def shutdown_routine(todo_list, active_theme):
    """A guided routine to review accomplishments, reschedule, and reflect."""
    console.print("\n[bold green]🌙 Let's wrap up the day.[/bold green]")
    
    # 1. Show accomplishments using the new getter method
    accomplished_today = todo_list.get_completed_today()

    if accomplished_today:
        accomplished_panel = Panel("\n".join(f"- {t.name}" for t in accomplished_today), 
                                   title="✅ Accomplished Today", border_style=active_theme['green'])
        console.print(accomplished_panel)
    else:
        console.print("[yellow]No tasks were completed today.[/yellow]")

    # 2. Review and reschedule pending tasks using the new getter method
    pending_tasks = todo_list.get_pending_tasks()

    if not pending_tasks:
        console.print("\n[bold green]All tasks cleared. You're all done! 🎉[/bold green]")
        display_stats(todo_list.data, active_theme)
        return
    
    console.print("\n[bold yellow]-- ⏳ Pending Tasks --[/bold yellow]")
    for task in pending_tasks:
        console.print(f"  ID {task.id}: {task.name}")
    
    # 3. Offer bulk reschedule option
    if console.input(f"\n[bold]Move all {len(pending_tasks)} pending tasks to tomorrow at 9 AM? (y/n): [/bold]").lower() == 'y':
        tomorrow_9am_str = (datetime.datetime.now().date() + datetime.timedelta(days=1)).strftime("%Y-%m-%d 09:00")
        for task in pending_tasks:
            # Call the edit_task method on the todo_list object
            todo_list.edit_task(task.id, new_due_date=tomorrow_9am_str)
        console.print(f"[green]All pending tasks have been rescheduled.[/green]")
    
    # 4. Final reflection step
    console.print("\n[bold]--- Daily Report ---[/bold]")
    display_stats(todo_list.data, active_theme)
    console.input("\nWhat was one win today? (Press Enter to finish): ")
    console.print("\n[bold green]Shutdown routine complete. Well done today! 👏[/bold green]")

# In main.py

def display_stats(todo_list, active_theme):
    """Displays user's progress stats by getting data from the TodoList object."""
    # Get the raw stats dictionary from the manager
    stats = todo_list.data.get('user_stats', {})

    # Call the new getter methods to get calculated values
    total_completed = todo_list.get_total_completed_count()
    completed_today_count = todo_list.get_completed_today_count()
    
    # --- The rest of the function is for display only ---
    stats_text = (
        f"🏆 Total Points: [bold {active_theme['cyan']}]{stats.get('points', 0)}[/bold {active_theme['cyan']}]\n"
        f"🏅 Current Level: [bold {active_theme['yellow']}]{stats.get('level', 'Novice')}[/bold {active_theme['yellow']}]\n"
        f"🔥 Current Streak: [bold {active_theme['red']}]{stats.get('streak', 0)} day(s)[/bold {active_theme['red']}]\n"
        f"🧊 Streak Freezes: [bold {active_theme['blue']}]{stats.get('streak_freezes', 0)} available[/bold {active_theme['blue']}]\n\n"
        f"✅ Tasks Completed (Today): [bold {active_theme['green']}]{completed_today_count}[/bold {active_theme['green']}]\n"
        f"✅ Tasks Completed (All Time): [bold {active_theme['green']}]{total_completed}[/bold {active_theme['green']}]"
    )
    
    unlocked_achievements = [name.replace('_', ' ').title() for name, unlocked in stats.get('achievements', {}).items() if unlocked]
    if unlocked_achievements:
        stats_text += "\n\n🎖️ Achievements: " + ", ".join(unlocked_achievements)
    
    panel = Panel(stats_text, title="📊 Your Kairu Stats", border_style=active_theme['blue'])
    console.print(panel)

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
            
            if char == 'p' and state == 'running':
                state = 'paused'
                console.print("\n[yellow]Timer paused. Press 'c' to continue or 's' to stop.[/yellow]")
            elif char == 'c' and state == 'paused':
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

# In main.py

def plan_day(todo_list, active_theme):
    """A guided routine to select top priorities from a smart-filtered list."""
    console.print("\n[bold green]☀️ Let's plan your day! Here are your top candidates:[/bold green]")
    
    # 1. Ask the engine for the list of candidate tasks.
    candidate_tasks = todo_list.get_focus_tasks()

    if not candidate_tasks:
        console.print("[yellow]You have no urgent or starred tasks to plan. Feel free to add some![/yellow]")
        return
    
    # 2. Display the curated list for selection.
    view_table = Table(title="Top Candidates for Today", border_style=active_theme['magenta'])
    view_table.add_column("ID", style=active_theme['cyan'])
    view_table.add_column("Name")
    view_table.add_column("Group")
    for task in candidate_tasks:
        view_table.add_row(str(task.id), task.name, task.group_name)
    console.print(view_table)

    # 3. Clear existing stars (optional).
    if console.input("\n[bold]Clear all other stars first? (y/n): [/bold]").lower() == 'y':
        for group in todo_list.data['groups']:
            for task in group['tasks']:
                task.starred = False
        console.print("[yellow]Cleared all stars.[/yellow]")

    # 4. Get user's priorities and tell the engine to star them.
    id_string = console.input("[bold]Enter the IDs of up to 3 tasks to star as today's priorities: [/bold]")
    try:
        priority_ids = [int(i.strip()) for i in id_string.split(',') if i.strip()]
        if not priority_ids: return

        for task_id in priority_ids:
            # Tell the engine to star the task.
            todo_list.toggle_star(task_id, star_status=True)
        
        # 5. Check for and award the achievement.
        if not todo_list.data['user_stats']['achievements']['planner']:
            todo_list.data['user_stats']['achievements']['planner'] = True
            console.print("[bold magenta]🏆 Achievement Unlocked: The Planner![/bold magenta]")
        
        console.print("\n[bold green]Priorities starred! Good luck today.[/bold green]")

    except ValueError:
        console.print("[bold red]Invalid input. Please enter numbers separated by commas.[/bold red]")

# In main.py, in the "UI Display & Interactive Functions" section

def display_completed_tasks(tasks, group_name, active_theme):
    """Displays a table of completed tasks for a specific group."""
    if not tasks:
        console.print(f"[yellow]No completed tasks found in group '{group_name}'.[/yellow]")
        return

    table = Table(title=f"Completed Tasks in Group: {group_name}", border_style=active_theme['blue'])
    table.add_column("Name", style="dim white")
    table.add_column("Completed At", style=f"dim {active_theme['green']}")

    # Sort by completion date (most recent first)
    tasks.sort(key=lambda t: t.completed_at, reverse=True)

    for task in tasks:
        completed_dt = datetime.datetime.fromisoformat(task.completed_at)
        completed_display = completed_dt.strftime("%Y-%m-%d %H:%M")
        table.add_row(task.name, completed_display)
    
    console.print(table)

# In main.py, in the "UI Display & Interactive Functions" section

def display_health_check(stats, active_theme):
    """Displays the health check feedback in a panel."""
    if stats['total_today'] == 0:
        console.print(Panel("[bold green]Your schedule for today is clear. A great time to plan or rest![/bold green]", 
                        title="Health Check Complete", border_style=active_theme['green']))
        return

    # --- Generate Feedback ---
    feedback_text = (
        f"You have [bold]{stats['total_today']}[/bold] tasks scheduled for today.\n"
        f"- [bold {active_theme['cyan']}]{stats['high_priority_count']}[/bold {active_theme['cyan']}] are high priority.\n"
        f"- You have scheduled [bold {active_theme['green']}]{stats['rest_task_count']}[/bold {active_theme['green']}] breaks."
    )
    
    advice = ""
    HIGH_PRIORITY_THRESHOLD = 4
    if stats['high_priority_count'] >= HIGH_PRIORITY_THRESHOLD and stats['rest_task_count'] == 0:
        advice = f"[bold {active_theme['yellow']}]Warning: A high number of priority tasks are scheduled with no breaks. To avoid burnout, consider adding some downtime with '--tags \"#rest\"'.[/bold {active_theme['yellow']}]"
    elif stats['rest_task_count'] > 0:
        advice = f"[bold {active_theme['green']}]Great job scheduling breaks! This is key to sustainable productivity.[/bold {active_theme['green']}]"
    else:
        advice = f"[bold {active_theme['cyan']}]Your schedule looks manageable. Have a productive day![/bold {active_theme['cyan']}]"
        
    final_text = f"{feedback_text}\n\n{advice}"
    
    console.print(Panel(final_text, title="🩺 Health Check Complete", border_style=active_theme['blue']))

# In main.py, in the "UI Display & Interactive Functions" section

def unstuck_routine(todo_list, active_theme):
    """A guided routine to help the user take action on a single stale task."""
    console.print("\n[bold cyan]🔍 Let's find a task that might be stuck...[/bold cyan]")
    
    # 1. Ask the engine to find a stale task.
    stale_task = todo_list.find_stale_task()

    if not stale_task:
        console.print("[green]No stale tasks found. Your list is fresh![/green]")
        return

    # 2. Get additional info and present it to the user.
    group_name = todo_list.find_group_for_task(stale_task.id)
    console.print(f"\nTask [bold]'{stale_task.name}'[/bold] in group [yellow]'{group_name}'[/yellow] was created on {datetime.datetime.fromisoformat(stale_task.created_at).date()}.")
    
    # 3. Handle user input and call the appropriate engine methods.
    action = console.input("[bold]What's the next action? ([B]reak down, [R]eschedule, [D]elete, [S]kip): [/bold]").lower().strip()

    if action == 'b':
        sub_desc = console.input("First sub-task: ")
        if sub_desc:
            success, (message, achievement) = todo_list.add_sub_task(stale_task.id, sub_desc)
            color = active_theme['green'] if success else active_theme['red']
            console.print(f"[{color}]{message}[/{color}]")
            if achievement: console.print(f"[bold magenta]{achievement}[/bold magenta]")
    
    elif action == 'r':
        new_due = console.input("When do you want to work on this? (YYYY-MM-DD HH:MM): ")
        success, message = todo_list.edit_task(stale_task.id, new_due_date=new_due)
        color = active_theme['green'] if success else active_theme['red']
        console.print(f"[{color}]{message}[/{color}]")
    
    elif action == 'd':
        if console.input(f"Are you sure you want to delete '{stale_task.name}'? (y/n): ").lower() == 'y':
            success, message = todo_list.delete_task(stale_task.id)
            color = active_theme['yellow'] if success else active_theme['red']
            console.print(f"[{color}]{message}[/{color}]")
    
    elif action == 's':
        console.print("Okay, we'll leave it for now.")
    
    else:
        console.print("[yellow]Invalid option. No action taken.[/yellow]")

def main():
    todo_list = ToDoList(DATA_FILE)

    parser = argparse.ArgumentParser(description="Kairu: A CLI Productivity Coach.")
    subparsers = parser.add_subparsers(dest='command', required = True)

    # GROUP
    # Add Group
    parser_group_add = subparsers.add_parser('group-add', help = 'Add a new task group')
    parser_group_add.add_argument('name', type = str, help = 'The name of the new group')

    parser_group_list = subparsers.add_parser('group-list', help='List all task groups')

    # TASK
    # Add Task
    parser_add = subparsers.add_parser('add', help='Add a new task')
    parser_add.add_argument('name', type=str, help='The name/title of the task')
    parser_add.add_argument('-g', '--group', type=str, required=True, help='The group to add the task to')
    parser_add.add_argument('--details', type=str, help='Optional details about the task')
    parser_add.add_argument('-p', '--priority', type=str, default='medium', choices=['low', 'medium', 'high'])
    parser_add.add_argument('-d', '--due', type=str, help="Set a due date using 'YYYY-MM-DD HH:MM' format")
    parser_add.add_argument('-r', '--recurring', type=str, choices=['daily', 'weekly', 'monthly'])
    parser_add.add_argument('--tags', type=str, help='Comma-separated tags')
    parser_add.add_argument('--goal', type=str, help='Link task to a long-term goal')

    # VIEW
    # View Task
    parser_view = subparsers.add_parser('view', help='View tasks')
    parser_view.add_argument('id', type=int, nargs='?', default=None, help='(Optional) View a specific task by its ID')
    parser_view.add_argument('--show-log', action='store_true', help='Show the progress log for a specific task')
    parser_view.add_argument('--group-by', type=str, default='group', choices=['group', 'goal'])
    parser_view.add_argument('-g', '--group', type=str, help='Filter to show only a specific group')
    parser_view.add_argument('-s', '--sort', type=str, choices=['priority', 'due_date'])
    parser_view.add_argument('--filter-priority', type=str, choices=['low', 'medium', 'high'])
    parser_view.add_argument('--filter-status', type=str, choices=['pending', 'done'])
    parser_view.add_argument('--starred', action='store_true', help='Show only starred tasks')
    parser_view.add_argument('--filter-tag', type=str, help='Filter tasks by a specific tag')

    # EDIT
    parser_edit = subparsers.add_parser('edit', help='Edit an existing task')
    parser_edit.add_argument('id', type=int, help='The ID of the task to edit')
    parser_edit.add_argument('--name', type=str, help='The new name for the task')
    parser_edit.add_argument('--details', type=str, help='The new details for the task')
    parser_edit.add_argument('--priority', type=str, choices=['low', 'medium', 'high'], help='The new priority for the task')
    parser_edit.add_argument('--due', type=str, help="The new due date in 'YYYY-MM-DD HH:MM' format")
    parser_edit.add_argument('--tags', type=str, help='Set a new comma-separated list of tags')
    parser_edit.add_argument('--goal', type=str, help="Link to a new goal or type 'none' to unlink")

    # GOAL
    # Add Goal
    parser_goal_add = subparsers.add_parser('goal-add', help='Add a new long-term goal')
    parser_goal_add.add_argument('name', type=str, help='The name of the goal')
    parser_goal_add.add_argument('description', type=str, nargs='?', default=None, help='Optional description of the goal')

    # View Goal List
    parser_goal_list = subparsers.add_parser('goal-list', help='List all goals')

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

    parser_unlock = subparsers.add_parser('unlock-theme', help='Unlock a new theme with points')
    parser_unlock.add_argument('name', type=str, help='The name of the theme to unlock')

    parser_set_theme = subparsers.add_parser('set-theme', help='Set your active theme')
    parser_set_theme.add_argument('name', type=str, help='The name of the theme to activate')

    parser_focus = subparsers.add_parser('focus', help="Show a focused view of what's important now")
    parser_focus.add_argument('-g', '--group', type=str, help='Include the next task from a specific group')

    parser_search = subparsers.add_parser('search', help='Search for a keyword across all tasks')
    parser_search.add_argument('keyword', type=str, help='The text to search for')

    # --- POMODORO command ---
    parser_pomodoro = subparsers.add_parser('pomodoro', help='Start a Pomodoro focus timer')
    parser_pomodoro.add_argument('-w', '--work', type=int, default=25, help='Duration of the work session in minutes (default: 25)')
    parser_pomodoro.add_argument('-b', '--breaks', type=int, default=5, help='Duration of the break in minutes (default: 5)')

    # --- New Guided Commands ---
    parser_plan = subparsers.add_parser('plan-day', help='Start a guided daily planning session')
    parser_shutdown = subparsers.add_parser('shutdown', help='Start a guided end-of-day shutdown routine')

    # --- Gamification Commands ---
    parser_themes = subparsers.add_parser('themes', help='View and manage themes')
    parser_buy_freeze = subparsers.add_parser('buy-freeze', help='Buy a streak freeze to protect your streak')

    # --- New Proactive Command ---
    parser_unstuck = subparsers.add_parser('unstuck', help='Start an interactive session to deal with a stale task')

    # --- LOG command ---
    parser_log = subparsers.add_parser('log', help='Log progress on a specific task')
    parser_log.add_argument('id', type=int, help='The ID of the task to log progress on')
    parser_log.add_argument('-m', '--message', type=str, required=True, help='The progress note')

    parser_stats = subparsers.add_parser('stats', help='Show your productivity stats')

    # --- STAR/UNSTAR commands ---
    parser_star = subparsers.add_parser('star', help='Star an important task')
    parser_star.add_argument('id', type=int, help='The global ID of the task to star')
    
    parser_unstar = subparsers.add_parser('unstar', help='Unstar a task')
    parser_unstar.add_argument('id', type=int, help='The global ID of the task to unstar')
    
    parser_view_completed = subparsers.add_parser('view-completed', help='View completed/archived tasks for a group')
    parser_view_completed.add_argument('-g', '--group', type=str, required=True, help='The group whose completed tasks you want to see')

    # --- New Proactive Command ---
    parser_health = subparsers.add_parser('health-check', help='Analyze your daily schedule for burnout risk')
    args = parser.parse_args()
    active_theme = THEMES.get(todo_list.data['user_stats']['active_theme'], THEMES['default'])

    if args.command == 'group-add':
        success, message = todo_list.add_group(args.name)
        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[bold red]{message}[/bold red]")
    
    elif args.command == 'add':
        success, message = todo_list.add_task(
            group_name=args.group,
            name=args.name,
            details=args.details,
            priority=args.priority,
            due_date=args.due,
            recurring=args.recurring,
            tags_string=args.tags,
            goal_name=args.goal
        )
        color = active_theme['green'] if success else active_theme['red']
        console.print(f"[{color}]{message}[/{color}]")

    elif args.command == 'view':
        if args.id:
            # First, ask the manager to find the data
            group, task = todo_list.find_task_by_id(args.id)
            if task:
                # Then, pass that data to the UI function
                display_single_task_view(task, group['name'], active_theme, args.show_log)
            else:
                console.print(f"[red]Error: Task ID {args.id} not found.[/red]")
        elif args.group_by == 'goal':
            all_tasks = [t for g in todo_list.data['groups'] for t in g['tasks']]
            all_goals = todo_list.data['goals']
            display_tasks_by_goal(all_tasks, all_goals, active_theme)
        else:
            display_tasks_by_group(
                todo_list.data['groups'],
                active_theme,
                show_group=args.group,
                sort_by=args.sort,
                filter_priority=args.filter_priority,
                filter_status=args.filter_status,
                show_starred=args.starred,
                filter_tag=args.filter_tag
            )
    
    elif args.command == 'edit':
        success, message = todo_list.edit_task(
            task_id = args.id,
            new_name=args.name,
            new_details=args.details,
            new_priority=args.priority,
            new_due_date=args.due,
            new_tags_string=args.tags,
            new_goal=args.goal
        )
        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[bold red]{message}[/bold red]")

    elif args.command == 'goal-add':
        success, message = todo_list.add_goal(
            name = args.name,
            description = args.description
        )

        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[bold red]{message}[/bold red]")

    elif args.command == 'sub-add':
        success, message, achievement = todo_list.add_sub_task(
            parent_id = args.parent_id,
            description = args.description
        )

        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[bold red]{message}[/bold red]")

        if achievement:
           console.print(f"[bold magenta]{achievement}[/bold magenta]")

    elif args.command == 'goal-list':
        all_goals = todo_list.list_goals()

        if not all_goals:
            console.print("[yellow]No goals defined. Use 'goal-add' to create one.[/yellow]")
        else:
            table = Table(title="Your Long-Term Goals")
            table.add_column("Name", style="bold cyan")
            table.add_column("Description", style="white")

            for goal in todo_list.data['goals']:
                table.add_row(goal['name'], goal.get('description', ''))
            
            console.print(table)

    elif args.command == 'group-list':
        all_groups = todo_list.list_groups()
            
        if not all_groups:
            console.print("[yellow]No goals defined. Use 'goal-add' to create one.[/yellow]")
        else:
            table = Table(title="Your Groups")
            table.add_column("Name", style="bold cyan")

            for group in todo_list.data['groups']:
                table.add_row(group['name'])

            console.print(table)

    elif args.command == 'unlock-theme':
        success, message = todo_list.unlock_theme(
            theme_name = args.name
        )

        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[bold red]{message}[/bold red]")
    
    elif args.command == 'set-theme':
        success, message = todo_list.set_theme(
            theme_name = args.name
        )

        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[bold red]{message}[/bold red]")

    elif args.command == 'focus':
        focus_tasks = todo_list.get_focus_tasks(args.group)
        display_focus_view(focus_tasks)

    elif args.command == 'search':
        results = todo_list.search_all(args.keyword)
        display_search_results(results)

    elif args.command == 'pomodoro':
        start_pomodoro(args.work, args.breaks)

    elif args.command == 'plan-day':
        plan_day(todo_list, active_theme)

    elif args.command == 'view-completed':
        # 1. Ask the engine for the data
        completed_tasks = todo_list.get_completed_tasks_for_group(args.group)
        
        # 2. Check if the engine found the group
        if completed_tasks is None:
            console.print(f"[bold red]Error: Group '{args.group}' not found.[/bold red]")
        else:
            # 3. If the group was found, tell the UI to display the data
            display_completed_tasks(completed_tasks, args.group, active_theme)
    
    elif args.command == 'done':
        # 1. Call the method and capture all the returned information
        success, (message, achievement, streak_msg) = todo_list.mark_task_done(args.id)
        
        # 2. The UI is now responsible for printing everything
        color = active_theme['green'] if success else active_theme['red']
        if message:
            console.print(f"[{color}]{message}[/{color}]")
        
        # Print achievement and streak messages if they exist
        if achievement:
            console.print(f"[bold magenta]{achievement}[/bold magenta]")
        if streak_msg:
            console.print(f"[cyan]{streak_msg}[/cyan]")

    elif args.command == 'sub-done':
        success, message = todo_list.mark_sub_task_done(args.parent_id, args.sub_task_id)
        
        color = active_theme['green'] if success else active_theme['red']
        console.print(f"[{color}]{message}[/{color}]")

    elif args.command == 'delete':
        success, message = todo_list.delete_task(args.id)

        color = active_theme['yellow'] if success else active_theme['red']
        console.print(f"[{color}]{message}[/{color}]")

    elif args.command == 'log':
        success, message = todo_list.log_progress(args.id, args.message)
        
        color = active_theme['green'] if success else active_theme['red']
        console.print(f"[{color}]{message}[/{color}]")
    
    elif args.command == 'star':
        success, message = todo_list.toggle_star(args.id, star_status=True)
        color = active_theme['green'] if success else active_theme['red']
        console.print(f"[{color}]{message}[/{color}]")

    elif args.command == 'unstar':
        success, message = todo_list.toggle_star(args.id, star_status=False)
        color = active_theme['green'] if success else active_theme['red']
        console.print(f"[{color}]{message}[/{color}]")

    elif args.command == 'health-check':
        # 1. Ask the engine for the analysis
        health_stats = todo_list.get_health_check_stats()
        
        # 2. Tell the UI to display the results
        display_health_check(health_stats, active_theme)
    
    elif args.command == 'unstuck':
        unstuck_routine(todo_list, active_theme)

    elif args.command == 'stats':
        display_stats(todo_list, active_theme)

    elif args.command == 'buy-freeze':
        success, message = todo_list.buy_streak_freeze()
        
        color = active_theme['green'] if success else active_theme['red']
        console.print(f"[{color}]{message}[/{color}]")
        
    modifying_commands = [
            'group-add', 'goal-add', 'add', 'edit', 'delete', 'done', 'sub-add', 'sub-done',
            'star', 'unstar', 'log', 'plan-day', 'shutdown', 'buy-freeze',
            'unlock-theme', 'set-theme', 'delete', 'health-check', 'view_completed', 'pomodoro', 'search', 'focus', 'group_list', 'goal_list', 'stats'
        ]
    
    if args.command in modifying_commands:
        todo_list.save_data()

if __name__ == "__main__":
    main()