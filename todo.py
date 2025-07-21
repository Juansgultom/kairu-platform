import json

# Define the filename for our data store
DATA_FILE = "tasks.json"

def show_help():
    print("\n--- Kairu To-Do List Manager ---")
    print("Usage: command [arguments]")
    print("\nCommands:")
    print("  add <task description>   - Adds a new task to your list.")
    print("  view                     - Shows all tasks in your list.")
    print("  delete <task number>     - Deletes a task by its number.")
    print("  help                     - Shows this help message.")
    print("  exit                     - Exits the application.")
    print("--------------------------------\n")

# Loads Tasks from the JSON file
def load_tasks():
    try:
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, return an empty list
        return []

# Saves tasks to the JSON file    
def save_tasks(tasks):
    with open(DATA_FILE, 'w') as file:
        return json.dump(tasks, file, indent=4)

# Add Tasks
def add_tasks(tasks, description):
    """Adds a new task, preventing duplicates."""
    # Check for duplicates (case-insensitive and ignoring whitespace)
    for task in tasks:
        if task['description'].lower().strip() == description.lower().strip():
            print(f"Task '{description}' already exists.")
            return # Stop the function here

    # If no duplicate is found, add the new task
    new_task = {"description": description, "status": "pending"}
    tasks.append(new_task)
    print(f"Added task: '{description}'")

# View Tasks
def view_tasks(tasks):
    if not tasks:
        print("Your to-do list is empty!")
        return
    
    print("\n--- Your To-Do List ---")
    for idx, task in enumerate(tasks):
        print(f"{idx + 1}. {task['description']} [{task["status"]}]")
    print("-----------------------\n")

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
        
        elif action == "delete":
            if len(parts) > 1:
                task_id = parts[1]
                delete_task(tasks, task_id)
                save_tasks(tasks)
            else:
                print("Error: Missing task number. Usage: delete <task number>.")
        
        elif action == "help":
            show_help()

        elif action == "exit":
            print("Exiting the To-DO List Manager. Goodbye!")
            break
    
    else:
        print("Unknown command. Type 'help' to see all available commands.")

if __name__ == "__main__":
    main()