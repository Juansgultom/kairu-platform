# Kairu - The Gamified Productivity Coach 🚀

*An intelligent, hierarchical to-do list manager for your command line.*

> Kairu is a sophisticated command-line application that transforms task management into a productive and engaging experience. It goes beyond a simple to-do list, offering a powerful suite of tools—from hierarchical organization and smart routines to a full gamification system—all designed to help you build focus, fight procrastination, and celebrate your progress directly from the terminal.

-----

## ✨ Key Features

### 🏛️ Organization & Planning

  * **Hierarchical Structure**: Organize your work with **Groups** → **Tasks** → **Sub-tasks**.
  * **☀️ Daily Planner**: A guided `plan-day` routine to intelligently suggest and star your top priorities.
  * **🌙 Evening Review**: A `shutdown` routine to review accomplishments, bulk reschedule pending items, and reflect on your day.

### ✅ Advanced Task Management

  * **Rich Attributes**: Assign priorities, specific due dates with times, and details to every task.
  * **⭐ Starred Tasks**: Mark your most important tasks with a star for quick access via the `focus` command.
  * **🏷️ Flexible Tagging**: Add multiple tags (e.g., `#client-a`, `#urgent`) for powerful, cross-group filtering.
  * **🔄 Recurring Tasks**: Automate routines by setting tasks to recur `daily`, `weekly`, or `monthly`.
  * **🗄️ Task Archiving**: Completed tasks are automatically moved to an archive, keeping your main view clean.

### 🚀 Productivity Tools

  * **🍅 Interactive Pomodoro Timer**: A built-in focus timer with `pause`, `continue`, and `stop` controls.
  * **🔍 Universal Search**: Instantly find any keyword across all tasks, groups, details, and archives.
  * **🎯 Focus Command**: Get an intelligent, consolidated view of what to work on right now.

### 🎮 Gamification Engine

  * **🏆 Points & Levels**: Earn points for completing tasks (with bonuses\!) and level up from "Novice" to "Focus Guru".
  * **🔥 Streaks & Freezes**: Build a streak of daily completions and spend points to buy "freezes" to protect it.
  * **🎖️ Achievements**: Unlock badges for reaching productivity milestones like "Planner" and "On a Roll".
  * **🎨 Unlockable Themes**: Spend points to unlock and apply new color themes for the interface.

-----

## 🚀 Getting Started

Get your local copy of Kairu up and running.

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

## 💻 Complete Command Reference

Kairu is run from the command line using `python todo.py <command> [arguments]`.

### 🏛️ Group & Task Management
| Command | Description | Example Usage |
| :--- | :--- | :--- |
| `group-add <name>` | Creates a new task group. | `python todo.py group-add "Project Phoenix"` |
| `group-list` | Lists all created groups. | `python todo.py group-list` |
| `add <name>` | Adds a new task to a group. | `python todo.py add "New Task" -g "Work" --tags "#proj"` |
| `edit <id>` | Edits properties of a task. | `python todo.py edit 5 --priority high --due "2025-07-23 18:00"` |
| `done <id>` | Completes a task, archives it, and awards points. | `python todo.py done 3` |
| `delete <id>` | Permanently deletes a task. | `python todo.py delete 8` |
| `clear` | Deletes all active tasks in all groups (asks for confirmation). | `python todo.py clear` |

### 📋 Sub-task & Detail Management
| Command | Description | Example Usage |
| :--- | :--- | :--- |
| `sub-add <id> <desc>` | Adds a sub-task to a parent task. | `python todo.py sub-add 5 "Create initial wireframes"` |
| `sub-done <id> <sub_id>`| Marks a sub-task as complete. | `python todo.py sub-done 5 1` |
| `star <id>` | Marks a task as important. | `python todo.py star 5` |
| `unstar <id>` | Removes the star from a task. | `python todo.py unstar 5` |

### 🚀 Productivity Routines
| Command | Description | Example Usage |
| :--- | :--- | :--- |
| `plan-day` | Starts the guided daily planning session. | `python todo.py plan-day` |
| `shutdown` | Starts the guided end-of-day review. | `python todo.py shutdown` |
| `focus` | Shows an intelligent view of current priorities. | `python todo.py focus -g "Work"` |
| `pomodoro` | Starts the interactive Pomodoro timer. | `python todo.py pomodoro -w 50 -b 10` |

### 🎮 Gamification & Stats
| Command | Description | Example Usage |
| :--- | :--- | :--- |
| `stats` | Displays your gamification progress and achievements. | `python todo.py stats` |
| `view-completed` | Displays the archive of completed tasks for a group. | `python todo.py view-completed -g "Project Phoenix"` |
| `buy-freeze` | Buys a streak freeze to protect your streak. | `python todo.py buy-freeze` |
| `themes` | Lists available themes and their status. | `python todo.py themes` |
| `unlock-theme <name>`| Unlocks a new theme using points. | `python todo.py unlock-theme forest` |
| `set-theme <name>` | Sets your active theme from your unlocked collection. | `python todo.py set-theme forest` |

### 🔍 Utility
| Command | Description | Example Usage |
| :--- | :--- | :--- |
| `search <keyword>` | Searches for a keyword across all tasks and groups. | `python todo.py search "budget"` |
| `[command] --help` | Shows detailed help for any command. | `python todo.py add --help` |

-----

## 🗺️ Roadmap

  * **Phase 4: Architectural Refactoring**: Convert the procedural script into an Object-Oriented structure for better scalability.
  * **Phase 5: Professionalization & Deployment**: Package the application to be installable via `pip` and write unit tests.

-----

## 📜 License

