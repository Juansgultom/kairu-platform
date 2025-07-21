import json
import datetime

# Define the filename for our data store
DATA_FILE = "tasks.json"

def show_help():
    print("\n--- Kairu To-Do List Manager ---")
    print("Usage: command [arguments]")
    print("\nCommands:")
    print("  add <task description>          - Adds a new task.")
    print("  view                            - Shows all tasks.")
    print("  edit <task_number> <new_desc>   - Edits an existing task.")
    print("  done <task_number>              - Marks a task as done.")
    print("  delete <task_number>            - Deletes a task.")
    print("  clear                           - Deletes all tasks.")
    print("  help                            - Shows this help message.")
    print("  exit                            - Exits the application.")
    print("--------------------------------\n")

# Loads Tasks from the JSON file
def load_tasks():
    try:
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, return an empty list
        return []

# Add Tasks
def add_tasks(tasks, description):
    """Adds a new task, preventing duplicates."""
    # Check for duplicates (case-insensitive and ignoring whitespace)
    for task in tasks:
        if task['description'].lower().strip() == description.lower().strip():
            print(f"Task '{description}' already exists.")
            return # Stop the function here

    # If no duplicate is found, add the new task
    new_task = {"description": description,
                "status": "pending",
                "created_at": datetime.datetime.now().isoformat()
    }
    tasks.append(new_task)
    print(f"Added task: '{description}'")

# Clear Tasks
def clear_tasks(tasks):
    confirm = input("Are you sure you want to delete all tasks? (y/n): ")
    if confirm == 'y':
        tasks.clear()
        print("All tasks have been deleted")
    else:
        print("Operation cancelled.")

# Delete Tasks
def delete_task(tasks, task_id):
    try:
        # Adjust for 0-based index
        index = int(task_id) - 1

        # Check if index is valid
        if 0 <= index < len(tasks):
            removed_task = tasks.pop(index)
            print(f"Deleted task: '{removed_task['description']}'")
        else:
            print("Error: Invalid task number.")
    
    except ValueError:
        print("Error: Please enter a valid number.")
    except IndexError:
        print("Error: Invalid task number.")

# Edit Tasks
def edit_task(tasks, task_id, new_description):
    try:
        index = int(task_id) - 1
        if 0 <= index < len(tasks):
            tasks[index]['description'] = new_description
            print(f"Edited task #{task_id} to: '{new_description}'")
        else:
            print("Error: Invalid task number.")
    except ValueError:
        print("Error: Please enter a valid number")

# Mark Task Done
def mark_task_done(tasks, task_id):
    try:
        index = int(task_id) - 1
        if 0 <= index < len(tasks):
            if tasks[index]['status'] == 'done':
                print(f"Task '{tasks[index]['description']}' is already marked as done.")
            else:
                tasks[index]['status'] = 'done'
                print(f"Marked task '{tasks[index]['description']}' as done.")
        else:
            print("Error: Invalid task number.")
    except ValueError:
        print("Error: Please enter a valid number.")

# Saves Tasks  
def save_tasks(tasks):
    with open(DATA_FILE, 'w') as file:
        return json.dump(tasks, file, indent=4)
    
# View Tasks
def view_tasks(tasks):
    """Displays all tasks, including their status and creation timestamp."""
    if not tasks:
        print("Your to-do list is empty!")
        return
    
    print("\n--- Your To-Do List ---")
    for idx, task in enumerate(tasks):
        status_symbol = "x" if task['status'] == 'done' else " "
        
        created_dt = datetime.datetime.fromisoformat(task['created_at'])

        formatted_time = created_dt.strftime("%Y-%m-%d %H:%M")
        
        print(f"{idx + 1}. [{status_symbol}] {task['description']} (Created: {formatted_time})")
    print("-----------------------\n")

def main():
    tasks = load_tasks()

    while True:
        command = input("\n Enter a command (add, view, delete, exit): ").lower().strip()
        parts = command.split(" ", 1)
        action = parts[0]

        if action == "add":
            if len(parts) > 1:
                description = parts[1]
                add_tasks(tasks, description)
                save_tasks(tasks)
            else:
                print("Error: Missing task description. Usage: add <your task here>")
        
        elif action == "view":
            view_tasks(tasks)
        
        elif action == "edit":
            try:
                sub_parts = parts[1].split(" ", 1)
                task_id = sub_parts[0]
                new_description = sub_parts[1]
                edit_task(tasks, task_id, new_description)
                save_tasks(tasks)
            except (IndexError, ValueError):
                print("Error: Invalid format. Usage: edit <task_number> <new_description>")

        elif action == "done":
            if len(parts) > 1:
                mark_task_done(tasks, parts[1])
                save_tasks(tasks)
            else:
                print("Error: Missing task number. Usage: done <task_number>")
        
        elif action == "delete":
            if len(parts) > 1:
                task_id = parts[1]
                delete_task(tasks, task_id)
                save_tasks(tasks)
            else:
                print("Error: Missing task number. Usage: delete <task number>.")
        
        elif action == "clear":
            clear_tasks(tasks)
            save_tasks(tasks)

        elif action == "help":
            show_help()

        elif action == "exit":
            print("Exiting the To-DO List Manager. Goodbye!")
            break
    
    else:
        print("Unknown command. Type 'help' to see all available commands.")

if __name__ == "__main__":
    main()