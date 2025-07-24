import copy
import datetime
import json
from dateutil.relativedelta import relativedelta

THEMES = {
    "default": {"cyan": "cyan", "magenta": "magenta", "green": "green", "yellow": "yellow", "red": "red", "blue": "blue"},
    "forest": {"cyan": "green", "magenta": "bright_green", "green": "green", "yellow": "yellow", "red": "bold red", "blue": "bright_blue"},
    "ocean": {"cyan": "blue", "magenta": "bright_blue", "green": "cyan", "yellow": "bright_yellow", "red": "bold red", "blue": "blue"}
}
THEME_COST = 500
STREAK_FREEZE_COST = 10

class Task:
    """A blueprint for a single task. Now with all attributes and conversion methods."""
    def __init__(self, id, name, details=None, status='pending', priority='medium', 
                 due_date=None, recurring=None, tags=None, sub_tasks=None, 
                 starred=False, created_at=None, log=None, goal=None, completed_at=None, **kwargs):
        self.id = id
        self.name = name
        self.details = details
        self.status = status
        self.priority = priority
        self.due_date = due_date
        self.recurring = recurring
        self.tags = tags if tags is not None else []
        self.sub_tasks = sub_tasks if sub_tasks is not None else []
        self.starred = starred
        self.created_at = created_at if created_at is not None else datetime.datetime.now().isoformat()
        self.log = log if log is not None else []
        self.goal = goal
        self.completed_at = completed_at

    def to_dict(self):
        """SERIALIZE: Converts this Task object into a dictionary."""
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        """DESERIALIZE: Creates a Task object from a dictionary."""
        return cls(**data)

class ToDoList:
    def __init__(self, filename):
        self.filename = filename
        self.data = self.load_data()
    
    def load_data(self):
        """DESERIALIZE: Loads data and converts all task dictionaries into Task objects."""
        try:
            with open(self.filename, 'r') as file:
                loaded_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            loaded_data = {"last_task_id": 0, "groups": [], "user_stats": {}, "goals": []}

        # Use the bridge!
        for group in loaded_data.get('groups', []):
            group['tasks'] = [Task.from_dict(t) for t in group.get('tasks', [])]
            group['completed_tasks'] = [Task.from_dict(t) for t in group.get('completed_tasks', [])]
        
        loaded_data.setdefault('goals', [])
        stats = loaded_data.setdefault('user_stats', {})
        stats.setdefault('points', 0)
        stats.setdefault('level', 'Novice')
        stats.setdefault('streak', 0)
        stats.setdefault('last_completed_date', None)
        stats.setdefault('streak_freezes', 0)
        stats.setdefault('active_theme', 'default')
        stats.setdefault('unlocked_themes', ['default'])
        stats.setdefault('achievements', {
            "planner": False, "on_a_roll": False,
            "high_achiever": False, "delegator": False
        })
        stats.setdefault('high_priority_completed', 0)
        return loaded_data

    def save_data(self):
        """SERIALIZE: Converts all Task objects back to dictionaries before saving."""
        data_to_save = copy.deepcopy(self.data)
        for group in data_to_save.get('groups', []):
            group['tasks'] = [t.to_dict() for t in group.get('tasks', [])]
            group['completed_tasks'] = [t.to_dict() for t in group.get('completed_tasks', [])]
        with open(self.filename, 'w') as file:
            json.dump(data_to_save, file, indent=4)

    def add_group(self, group_name):
        for group in self.data['groups']:
            if group['name'].lower() == group_name.lower():
                return False, f"Error: Group '{group_name}' already exists."
        
        new_group = {
            "name": group_name,
            "tasks": [],
            "completed_tasks": []
        }
        self.data['groups'].append(new_group)
        return True, f"Added new group: '{group_name}'"
    
    def parse_tags(self, tags_string):
        if not tags_string:
            return []
        return [f"#{tag.strip().lstrip('#')}" for tag in tags_string.split(',')]
    
    def add_task(self, group_name, name, details=None, priority='medium', due_date=None, recurring=None, tags_string=None, goal_name=None):
        target_group = next((g for g in self.data['groups'] if g['name'].lower() == group_name.lower()), None)
        if not target_group:
            return False, f"Error: Group '{group_name}' not found."
        
        if due_date:
            try:
                datetime.datetime.strptime(due_date, "%Y-%m-%d %H:%M")
            except ValueError:
                return False, "Error: Invalid due date format. Please use 'YYYY-MM-DD HH:MM'."
            
        for task in target_group['tasks']:
            if task.name.lower() == name.lower():
                return False, f"Error: Task '{name}' already exists in group '{target_group['name']}'."
        
        if goal_name and not any(g['name'].lower() == goal_name.lower() for g in self.data['goals']):
            return False, f"Error: Goal '{goal_name}' not found. Create it first with 'goal-add'."
        
        self.data['last_task_id'] += 1
        new_id = self.data['last_task_id']

        # Correctly create a Task OBJECT
        new_task = Task(
            id=new_id,
            name=name,
            details=details,
            priority=priority,
            due_date=due_date,
            recurring=recurring,
            tags=self.parse_tags(tags_string),
            goal=goal_name
        )
        
        target_group['tasks'].append(new_task)
        return True, f"Added task '{name}' (ID: {new_id}) to group '{target_group['name']}'."
    
    def find_task_by_id(self, task_id):
        """Finds a task and its parent group by its permanent ID."""
        for group in self.data['groups']:
            # Use OBJECT notation (task.id)
            for task in group['tasks']:
                if task.id == task_id:
                    return group, task
            for task in group.get('completed_tasks', []):
                if task.id == task_id:
                    return group, task
        return None, None
    
    def edit_task(self, task_id, new_name=None, new_details=None, new_priority=None, new_due_date=None, new_tags_string=None, new_goal=None): 
        group, task = self.find_task_by_id(task_id)

        if not task:
            return False, f"Error: Task ID {task_id} not found."
        
        if new_name is not None:
            task.name = new_name

        if new_details is not None:
            task.details = new_details

        if new_priority is not None:
            if new_priority in ['low', 'medium', 'high']:
                task.priority = new_priority
            else:
                return False, f"Error: Invalid priority. No changes saved."
            
        if new_due_date is not None:
            try:
                due_date_obj = datetime.datetime.strptime(new_due_date, "%Y-%m-%d %H:%M")
                task.due_date = due_date_obj.isoformat()
            except ValueError:
                return False, f"Error: Invalid due date format. No changes saved."
        
        if new_tags_string is not None:
            task.tags = self.parse_tags(new_tags_string)

        if new_goal is not None:
            if new_goal.lower() == 'none':
                task.goal = None
            elif any(g['name'].lower() == new_goal.lower() for g in self.data['goals']):
                task.goal = new_goal
            else:
                return False, f"Error: Goal '{new_goal}' not found. No changes saved."

        return True, f"Successfully updated task #{task_id}."
    
    def add_goal(self, name, description = None):
        if any(g['name'].lower() == name.lower() for g in self.data['goals']):
            return False, f"Error: Goal '{name}' already exists."
        
        new_goal = {"name": name, "description": description}
        self.data['goals'].append(new_goal)

        return True, f"Added new goal: '{name}'"
    
    def add_sub_task(self, parent_id, description):
        group, task = self.find_task_by_id(parent_id)

        if not task:
            return False, f"Error: Invalid parent task ID."

        # Create the new sub-task
        sub_task = {"description": description, "status": "pending"}
        
        # Safely append the sub-task (creates the list if it somehow doesn't exist)
        task.sub_tasks.append(sub_task)

        achievement_message = None
        # Check for and award the "Delegator" achievement on first use
        if not self.data['user_stats']['achievements']['delegator']:
            self.data['user_stats']['achievements']['delegator'] = True
            achievement_message = "🏆 Achievement Unlocked: The Delegator!"
        
        # Return the success message and the optional achievement message
        return True, f"Added sub-task to '{task.name}'.", achievement_message
    
    def list_goals(self):
        return self.data['goals']
    
    def list_groups(self):
        return self.data['groups']
    
    def display_themes(self):
        return self.data['user_stats']
    
    def unlock_theme(self, theme_name):
        stats = self.data['user_stats']
        theme_name = theme_name.lower()

        if theme_name not in THEMES:
            return False, f"Error: Theme not found."
        if theme_name in stats['unlocked_themes']:
            return False, f"You have already unlocked the '{theme_name}' theme."
        if stats['points'] < THEME_COST:
            return False, f"Not enough points! You need {THEME_COST} points to unlock a theme."

        stats['points'] -= THEME_COST
        stats['unlocked_themes'].append(theme_name)

        return True, f"Congratulations! You have unlocked the '{theme_name}' theme."
    
    def set_theme(self, theme_name):
        stats = self.data['user_stats']
        theme_name = theme_name.lower()

        if theme_name not in stats['unlocked_themes']:
            return False, f"Error: You have not unlocked the '{theme_name}' theme yet."
        
        stats['active_theme'] = theme_name

        return True, f"Active theme set to '{theme_name}'."
    
    def get_focus_tasks(self, focus_group_name = None):
        """Gathers tasks for the focus view based on due date, starred status, and priority."""
        focus_list = []
        seen_ids = set()
        today = datetime.date.today()

        all_tasks = []
        for group in self.data.get('groups', []):
            for task in group.get('tasks', []):
                task.group_name = group['name']
                all_tasks.append(task)
        
        # 1. Gather tasks due today
        for task in all_tasks:
            if task.due_date:
                due_date = datetime.datetime.fromisoformat(task.due_date).date()
                if due_date == today and task.id not in seen_ids:
                    focus_list.append(task)
                    seen_ids.add(task.id)

            # 2. Gather all starred tasks
            for task in all_tasks:
                if task.starred and task.id not in seen_ids:
                    focus_list.append(task)
                    seen_ids.add(task.id)

            # --- New Logic: Gather all high-priority tasks ---
            for task in all_tasks:
                if task.priority == 'high' and task.id not in seen_ids:
                    focus_list.append(task)
                    seen_ids.add(task.id)

            # 4. Gather next task from a specific group
            if focus_group_name:
                target_group = next((g for g in self.data['groups'] if g['name'].lower() == focus_group_name.lower()), None)
                if target_group and target_group['tasks']:
                    priority_map = {'high': 1, 'medium': 2, 'low': 3}
                    sorted_tasks = sorted(target_group['tasks'], key=lambda t: priority_map.get(t.get('priority'), 4))
                    if sorted_tasks and sorted_tasks[0]['id'] not in seen_ids:
                        focus_list.append(sorted_tasks[0])
                        seen_ids.add(sorted_tasks[0]['id'])
            
            return focus_list
    
    def buy_streak_freeze(self):
        stats = self.data['user_stats']
        if stats['points'] < STREAK_FREEZE_COST:
            return False, f"Not enough points! You need {STREAK_FREEZE_COST} to buy a freeze."
        
        stats['points'] -= STREAK_FREEZE_COST
        stats['streak_freezes'] += 1

        return True, f"Streak Freeze purchased! You now have {stats['streak_freezes']}."
    
    @staticmethod
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
    
    def search_all(self, keyword):
        """Searches for a keyword across all groups, tasks, and sub-tasks."""
        results = []
        keyword_lower = keyword.lower()

        for group in self.data.get('groups', []):
            # Search in parent tasks (active)
            for task in group.get('tasks', []):
                if (keyword_lower in task.name.lower() or (task.details and keyword_lower in task.details.lower())):
                    results.append({"type": "Active Task", "id": task.id, "match": task.name, "location": f"Group '{group['name']}'"})
                
                # Search in sub-tasks of active tasks
                for i, sub_task in enumerate(task.sub_tasks):
                    if keyword_lower in sub_task['description'].lower():
                        results.append({"type": "Sub-task", "id": f"{task.id}.{i+1}", "match": sub_task['description'], "location": f"Task #{task.id}"})
            
            # Search in completed tasks
            for task in group.get('completed_tasks', []):
                if (keyword_lower in task.name.lower() or (task.details and keyword_lower in task.details.lower())):
                    results.append({"type": "Completed Task", "id": task.id, "match": task.name, "location": f"Group '{group['name']}'"})

        return results
    
    def get_pending_tasks(self):
        """Returns a flat list of all active Task objects."""
        return [task for group in self.data['groups'] for task in group['tasks']]
     
    def get_completed_today(self):
        """Returns a list of Task objects completed today."""
        today = datetime.date.today()
        completed_today = []
        for group in self.data['groups']:
            for task in group.get('completed_tasks', []):
                if datetime.datetime.fromisoformat(task.completed_at).date() == today:
                    completed_today.append(task)
        return completed_today
    
    # In models.py, inside the TodoList class

    def get_total_completed_count(self):
        """Calculates the total number of completed tasks across all groups."""
        return sum(len(g.get('completed_tasks', [])) for g in self.data['groups'])

    def get_completed_today_count(self):
        """Calculates the number of tasks completed today."""
        today = datetime.date.today()
        count = 0
        for group in self.data['groups']:
            for task in group.get('completed_tasks', []):
                if datetime.datetime.fromisoformat(task.completed_at).date() == today:
                    count += 1
        return count
    
    def toggle_star(self, task_id, star_status: bool):
        """Stars or unstars a task by its permanent ID."""
        group, task = self.find_task_by_id(task_id)
        if not task:
            return False, f"Error: Invalid task ID {task_id}."
        
        task.starred = star_status
        status_text = "Starred" if star_status else "Unstarred"
        return True, f"{status_text} task '{task.name}' in group '{group['name']}'."
    
    def get_completed_tasks_for_group(self, group_name):
        """Finds a group and returns its list of completed Task objects."""
        target_group = next((g for g in self.data['groups'] if g['name'].lower() == group_name.lower()), None)
        
        if not target_group:
            # Return None to indicate the group was not found
            return None
            
        return target_group.get('completed_tasks', [])
    
    def mark_task_done(self, task_id):
        """Handles all logic for task completion and returns a tuple of messages."""
        group, task = self.find_task_by_id(task_id)
        if not task:
            return False, ("Task ID not found.", None, None)
        if task in group.get('completed_tasks', []):
            return False, (f"Task '{task.name}' is already completed.", None, None)

        # --- Gamification Logic ---
        stats = self.data['user_stats']
        points_earned = 10
        if task.priority == 'high': points_earned += 10
        if task.priority == 'medium': points_earned += 5
        if task.due_date and datetime.datetime.now() <= datetime.datetime.fromisoformat(task.due_date):
            points_earned += 15
        stats['points'] += points_earned
        
        achievement_unlocked = None
        if task.priority == 'high':
            stats['high_priority_completed'] += 1
            if stats['high_priority_completed'] >= 10 and not stats['achievements']['high_achiever']:
                stats['achievements']['high_achiever'] = True
                achievement_unlocked = "🏆 Achievement Unlocked: High Achiever!"

        today_str = datetime.date.today().isoformat()
        streak_message = None
        if stats.get('last_completed_date'):
            delta = datetime.date.today() - datetime.date.fromisoformat(stats['last_completed_date'])
            if delta.days == 1:
                stats['streak'] += 1
            elif delta.days > 1:
                if stats['streak_freezes'] > 0:
                    stats['streak_freezes'] -= 1
                    streak_message = f"Your streak was saved by a freeze! You have {stats['streak_freezes']} left."
                else:
                    stats['streak'] = 1
        else:
            stats['streak'] = 1
        
        stats['last_completed_date'] = today_str
        if stats['streak'] >= 3 and not stats['achievements']['on_a_roll']:
            stats['achievements']['on_a_roll'] = True
            achievement_unlocked = "🏆 Achievement Unlocked: On a Roll!"
        
        stats['level'] = self.get_level(stats['points'])

        # --- Reschedule or Archive Logic ---
        if task.recurring and task.due_date:
            current_due_date = datetime.datetime.fromisoformat(task.due_date)
            if task.recurring == 'daily': task.due_date = (current_due_date + datetime.timedelta(days=1)).isoformat()
            elif task.recurring == 'weekly': task.due_date = (current_due_date + datetime.timedelta(weeks=1)).isoformat()
            elif task.recurring == 'monthly': task.due_date = (current_due_date + relativedelta(months=1)).isoformat()
            
            message = f"Recurring task '{task.name}' completed! You earned {points_earned} points. Rescheduled."
            return True, (message, achievement_unlocked, streak_message)
        else:
            task.status = 'done'
            task.completed_at = datetime.datetime.now().isoformat()
            if task in group['tasks']:
                group['tasks'].remove(task)
            group['completed_tasks'].append(task)
            
            message = f"Completed '{task.name}'! You earned {points_earned} points. Task archived."
            return True, (message, achievement_unlocked, streak_message)
    
    def mark_sub_task_done(self, parent_id, sub_task_id):
        """Marks a sub-task as 'done'."""
        _, task = self.find_task_by_id(parent_id)
        if not task:
            return False, "Error: Invalid parent task ID."
        
        try:
            # sub_task_id from the user is 1-based, so we subtract 1 for the index
            sub_task_index = int(sub_task_id) - 1
            
            if 0 <= sub_task_index < len(task.sub_tasks):
                # Check if it's already done
                if task.sub_tasks[sub_task_index]['status'] == 'done':
                    return False, f"Sub-task {sub_task_id} for '{task.name}' is already done."
                
                task.sub_tasks[sub_task_index]['status'] = 'done'
                return True, f"Completed sub-task for '{task.name}'."
            else:
                return False, "Error: Invalid sub-task number."
        except (ValueError, IndexError):
            return False, "Error: Invalid sub-task number."
    
    def delete_task(self, task_id):
        """Deletes a parent task and its sub-tasks from the data structure."""
        group, task_to_delete = self.find_task_by_id(task_id)
        
        if not task_to_delete:
            return False, f"Error: Task ID {task_id} not found."
        
        # Check if the task is in the active list and remove it
        if task_to_delete in group['tasks']:
            group['tasks'].remove(task_to_delete)
            return True, f"Deleted task: '{task_to_delete.name}' from group '{group['name']}'."
            
        # Check if the task is in the completed list and remove it
        elif task_to_delete in group.get('completed_tasks', []):
            group['completed_tasks'].remove(task_to_delete)
            return True, f"Deleted task: '{task_to_delete.name}' from group '{group['name']}'."
            
        # This case should ideally not be reached if find_task_by_id is correct
        return False, "Error: Could not find the task to delete in its group."
    
    # In models.py, inside the TodoList class

    def log_progress(self, task_id, message):
        """Adds a timestamped progress note to a specific task."""
        _, task = self.find_task_by_id(task_id)
        if not task:
            return False, f"Error: Task ID {task_id} not found."

        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "note": message
        }
        
        # The Task object's log is a list, so we can append to it
        task.log.append(log_entry)
        return True, f"Progress logged for task #{task_id}: '{task.name}'."
    
    def get_health_check_stats(self):
        """Analyzes today's tasks and returns a dictionary of stats."""
        today = datetime.date.today()
        tasks_today = []
        for group in self.data.get('groups', []):
            for task in group.get('tasks', []):
                if task.due_date:
                    due_date = datetime.datetime.fromisoformat(task.due_date).date()
                    if due_date == today:
                        tasks_today.append(task)
        
        stats = {
            "total_today": len(tasks_today),
            "high_priority_count": 0,
            "rest_task_count": 0
        }

        for task in tasks_today:
            if task.priority == 'high':
                stats['high_priority_count'] += 1
            if '#rest' in task.tags:
                stats['rest_task_count'] += 1
        
        return stats

    def find_stale_task(self, stale_days=14):
        """Finds the oldest active, non-recurring task."""
        stale_tasks = []
        today = datetime.datetime.now()

        for group in self.data.get('groups', []):
            for task in group.get('tasks', []):
                # Ignore recurring tasks
                if task.recurring:
                    continue
                
                created_date = datetime.datetime.fromisoformat(task.created_at)
                if (today - created_date).days >= stale_days:
                    stale_tasks.append(task)
        
        # Return the oldest one if any are found
        if stale_tasks:
            stale_tasks.sort(key=lambda t: t.created_at)
            return stale_tasks[0]
        
        return None

    def find_group_for_task(self, task_id):
        """Finds the group name for a given task ID."""
        # This method reuses our other find_task_by_id method.
        group, task = self.find_task_by_id(task_id)
        
        # If a group was found, return its name. Otherwise, return 'N/A'.
        return group['name'] if group else "N/A"
    
