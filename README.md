# Kairu - Task Manager 🚀
*A powerful, hierarchical to-do list manager for your command line.*

> Kairu is a sophisticated command-line task manager built with Python. It goes beyond a simple to-do list, offering a hierarchical organization system with groups, tasks, and sub-tasks, along with advanced productivity features to manage complex projects directly from your terminal.

-----

## ✨ Key Features

  * **🗂️ Hierarchical Organization**: Structure your work with **Groups** → **Tasks** → **Sub-tasks**.
  * **📝 Rich Task Attributes**: Assign a **priority**, a specific **due date/time**, and details.
  * **⭐ Starred Tasks**: Mark your most important tasks with a star for quick access.
  * **🏷️ Flexible Tagging**: Add multiple **tags** (e.g., `#client-a`, `#urgent`) for cross-group filtering.
  * **🔄 Recurring Tasks**: Automate routines by setting tasks to recur `daily`, `weekly`, or `monthly`.
  * **🗄️ Task Archiving**: Completed tasks are automatically moved to an archive, keeping your main view clean.
  * **🔍 Universal Search**: Instantly find any keyword across all tasks, groups, details, and archives.
  * **💅 Polished UI**: A clean table view powered by `rich`, with colors and clear formatting.

-----

## 🚀 Getting Started

Get your local copy of Kairu up and running in a few simple steps.

### Prerequisites

  * Python 3.9+
  * pip

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/YourUsername/kairu.git
    cd kairu
    ```
2.  **Create a `requirements.txt` file** with the following content:
    ```txt
    rich
    python-dateutil
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

-----

## 💻 Command Reference

Kairu is run from the command line using `python todo.py <command>`.

| Command | Description | Example |
| :--- | :--- | :--- |
| **`group-add <name>`** | Creates a new task group. | `python todo.py group-add "Personal"` |
| **`add <name>`** | Adds a new task to a group. | `python todo.py add "New Task" -g Work --tags "#proj-x"` |
| **`view`** | Displays active tasks. | `python todo.py view --filter-priority high` |
| **`view-completed`** | Displays archived tasks. | `python todo.py view-completed -g Personal` |
| **`done <id>`** | Completes and archives a task. | `python todo.py done 3` |
| **`star <id>`** | Stars an important task. | `python todo.py star 5` |
| **`edit <id>`** | Edits a task's properties. | `python todo.py edit 5 --priority high --due "2025-07-22 18:00"` |
| **`search <keyword>`** | Searches for a keyword. | `python todo.py search "budget"` |
| **`delete <id>`** | Deletes a task. | `python todo.py delete 2` |

-----

## 🗺️ Roadmap

  * **Phase 4: Architectural Refactoring**: Convert the procedural script into an Object-Oriented structure for better scalability.
  * **Phase 5: Professionalization & Deployment**: Package the application to be installable via `pip` and write unit tests.
  * See the `ROADMAP.md` for more details.

-----

## 📜 License

Distributed under the MIT License. See `LICENSE.txt` for more information.
