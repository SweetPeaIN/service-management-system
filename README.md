# Service Management System (SMS)

A modern, feature-rich Terminal User Interface (TUI) application designed for seamless service request tracking, customer management, and administrative workflows. Built with a focus on robust database integrity and a highly polished, keyboard-driven user experience.

## ✨ Key Features

### 🛡️ Administrative Control
* **Secure Routing**: Hardcoded master-key entry for administrative access.
* **Order Management**: View paginated service requests and securely update lifecycle statuses (with terminal state locking for 'Completed' orders).
* **Advanced Search**: Strict, case-sensitive customer database querying using `GLOB` pattern matching.
* **Safe Deletion**: Atomic database transactions to safely remove users alongside their orphaned service records.

### 👤 Customer Experience
* **Interactive TUI**: Fluid, arrow-key navigation powered by `Questionary`.
* **Dynamic Profiles**: A "Profile Dashboard" that generates visually distinct, randomized ASCII avatars on every load.
* **Smart Booking**: Book services, choose time slots, and review detailed vendor comparison tables.
* **Robust Security**: Password complexity enforcement and secure session state management.

## 🛠️ Tech Stack
* **Language**: Python 3.13+
* **Database**: SQLite via `SQLModel` (Pydantic + SQLAlchemy)
* **UI/UX**: `Rich` (Formatting/Tables) & `Questionary` (Interactive Prompts)
* **Environment Management**: `uv`

## 🚀 Getting Started

This project is optimized for Linux environments and utilizes `uv` for lightning-fast dependency management.

### Prerequisites
* **Python**: 3.13 or higher.
* **Package Manager**: `uv` installed globally.

### Installation

1. **Clone the repository**:

        git clone <your-repository-url>
        cd service-management-system

2. **Sync the environment**: Use `uv` to automatically read the `pyproject.toml` and install dependencies (`rich`, `questionary`, `sqlmodel`).

        uv sync

3. **Initialize the Database**: Run the application once to generate the SQLite database and schema.

        uv run main.py

   *(Exit the application after the main menu appears.)*

4. **Load Dummy Data (Recommended)**: Populate the database with the pre-configured CSV data to test the tables and pagination features immediately.

        uv run data/script.py

## 💻 Usage

Launch the main application loop:

```bash
uv run main.py
```

### Quick Test Credentials

* **Admin Access**:
  * Username: `admin`
  * Password: `admin123`

* **Customer Access**:
  * Create a new user via the "Register" menu, or log in using credentials mapped from your `users.csv` file.

## 📁 Project Structure

```text
service-management-system/
├── app/
│   ├── admin_mgr.py      # Administrative functions & queries
│   ├── auth.py           # Login, registration, & validation logic
│   ├── database.py       # SQLModel engine & connection setup
│   ├── models.py         # Database schema (User, ServiceRequest)
│   ├── profile_ui.py     # Randomized visual profile card generator
│   ├── service_mgr.py    # Customer dashboard & order creation
│   └── utils.py          # Shared tools (e.g., Pagination engine)
├── data/
│   ├── script.py         # Database seeder
│   ├── users.csv         # Dummy user data
│   └── service_requests.csv
├── main.py               # Application entry point & routing loop
├── pyproject.toml        # Project metadata & dependencies
└── README.md
```
