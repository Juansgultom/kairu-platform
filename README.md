# Kairu - The Gamified Productivity Coach 🚀

*An installable, Object-Oriented CLI application designed to build focus and motivation.*

> Kairu is a sophisticated command-line application that transforms task management into a productive and engaging experience. It goes beyond a simple to-do list, offering a powerful suite of tools—from hierarchical organization and smart routines to a full gamification system—all designed to help you build focus, fight procrastination, and celebrate your progress directly from the terminal.

-----

## ✨ Key Features

### 🏛️ Organization & Planning

  * **Hierarchical Structure**: Organize your work with **Goals** → **Groups** → **Tasks** → **Sub-tasks**.
  * **Goal-Task Linking**: Connect individual tasks to your long-term goals to maintain focus on the "why."
  * **☀️ Daily Planner**: A guided `plan-day` routine to intelligently suggest and star your top priorities.
  * **🌙 Evening Review**: A `shutdown` routine to review accomplishments, bulk reschedule pending items, and reflect on your day.

### ✅ Advanced Task Management

  * **Rich Attributes**: Assign priorities, specific due dates with times, and details to every task.
  * **⭐ Starred Tasks**: Mark your most important tasks with a star for quick access.
  * **🏷️ Flexible Tagging**: Add multiple tags (e.g., `#client-a`, `#urgent`) for powerful, cross-group filtering.
  * **🔄 Recurring Tasks**: Automate routines by setting tasks to recur `daily`, `weekly`, or `monthly`.
  * **🗄️ Task Archiving**: Completed tasks are automatically moved to an archive, keeping your main view clean.
  * **📝 Progress Logging**: Add timestamped `log` notes to tasks to track iterative progress without marking them as complete.

### 🚀 Proactive Productivity Tools

  * **🍅 Interactive Pomodoro Timer**: A built-in focus timer with `pause`, `continue`, and `stop` controls.
  * **🔍 Universal Search**: Instantly find any keyword across all tasks, groups, details, and archives.
  * **🎯 Focus Command**: Get an intelligent, consolidated view of what to work on right now.
  * **🆘 "Unstuck" Assistant**: An interactive `unstuck` command that finds stale tasks and guides you through a decision-making process.
  * **🩺 Health Check**: A `health-check` command that analyzes your daily schedule for burnout risk and suggests adding breaks.

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
2.  **Install the project in editable mode:**:
    ```txt
    pip install -e .
    ```

-----

## 💻 Command Reference

Once installed, you can run Kairu from anywhere using the kairu command. Here are some of the most common commands. For a full list of options for any command, use `kairu <command> --help`.

| Command | Description | Example Usage |
| :--- | :--- | :--- |
| **`plan-day`** | Starts the guided daily planning routine. | `kairu plan-day` |
| **`shutdown`** | Starts the guided end-of-day review. | `kairu shutdown` |
| **`focus`** | Shows an intelligent view of current priorities. | `kairu focus -g "Work"` |
| **`pomodoro`** | Starts the interactive Pomodoro timer. | `kairu pomodoro -w 50 -b 10` |
| **`stats`** | Displays your gamification progress. | `kairu stats` |
| **`unstuck`** | Helps you take action on a stale task. | `kairu unstuck` |
| **`add <name>`** | Adds a new task to a group and goal. | `kairu add "New Task" -g Work --goal "Launch"`|
| **`log <id>`** | Adds a progress note to a task. | `kairu log 3 -m "Draft complete"` |
| **`view <id>`** | Shows a detailed view of a single task. | `kairu view 3 --show-log` |
| **`done <id>`** | Completes and archives a task, awarding points. | `kairu done 3` |

-----

## 🏗️ Architecture
Kairu is built using a clean, Object-Oriented architecture with a clear separation of concerns:
* `src/kairu/models.py`: The "engine" of the application. Contains the Task and TodoList classes and handles all data management and business logic.
* `src/kairu/main.py`: The "user interface" layer. Handles command-line argument parsing and all console output and user interaction.
* `tests/: Contains the pytest unit test suite for the data models.`
  
-----
## 🗺️ Roadmap

  * **Phase 4: Architectural Refactoring (Completed)**: Converted the procedural script into a clean Object-Oriented structure with a separate data layer (models.py) and UI layer (main.py).
  * **Phase 5: Professionalization & Deployment (Completed)**: Package the application to be installable via `pip` and write unit tests.
  * **Phase 6: Database Integration**: Replace the JSON file with a robust SQLite database.
  * **Phase 7: API-First Architecture**: Decouple the application logic into a backend REST API.

-----
