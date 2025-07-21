import json

# Define the filename for our data store
DATA_FILE = "tasks.json"

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
    new_tasks = {"description": description, "status": "pending"}
    tasks.append(new_tasks)
    print("Added task: '{description}'")

# View Tasks
def view_tasks(tasks):
    if not tasks:
        print("Your to-do list is empty!")
        return
    
    print("\n--- Your To-Do List ---")
    for idx, task in enumerate(tasks):
        print(f"{idx + 1}. [{task["Status"]}] {task['description']}")
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
        command = input("\Enter a command (add, view, delete, exit): ").lower().strip()
        parts = command.split(" ", 1)
        action = parts[0]

        if action == "add":
            if len(parts) > 1:
                description = parts[1]
                add_tasks(tasks, description)
                save_tasks(tasks)
            else:
                print("Error: Please provide a task description after 'add'.")
        
        elif action == "view":
            view_tasks(tasks)
        
        elif action == "delete":
            if len(parts) > 1:
                task_id = parts[1]
                delete_task(tasks, task_id)
                save_tasks(tasks)
            else:
                print("Error: Please provide the task number to delete.")
        
        elif action == "exit":
            print("Exiting the To-DO List Manager. Goodbye!")
            break
    
    else:
        print("Unknown command. Please use 'add', 'view', 'delete', or 'exit'.")

if __name__ == "__main__":
    main()