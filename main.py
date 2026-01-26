import sys
import questionary
from rich.console import Console
from rich.panel import Panel

# Import our custom modules from the app package
from app.database import create_db_and_tables
from app.auth import login_user, register_user
from app.service_mgr import create_service_request_ui

console = Console()

def main():
    # 1. Initialize the Database (creates tables if they don't exist)
    create_db_and_tables()

    # 2. State Variable: Tracks who is currently logged in
    current_user = None

    # 3. The Infinite App Loop
    while True:
        # --- STATE A: User is NOT Logged In ---
        if current_user is None:
            console.clear()
            console.print(Panel("Service Management System", style="bold magenta"))

            choice = questionary.select(
                "Welcome! Please select an option:",
                choices=["Login", "Register New Customer", "Exit"]
            ).ask()

            if choice == "Login":
                # Captures the User object if login succeeds
                current_user = login_user()

            elif choice == "Register New Customer":
                register_user()

            elif choice == "Exit":
                console.print("[bold]Goodbye![/bold]")
                sys.exit()

        # --- STATE B: User IS Logged In (Dashboard) ---
        else:
            console.clear()
            # Show who is logged in
            console.print(
                Panel(
                    f"Dashboard\nLogged in as: [bold yellow]{current_user.user_name}[/bold yellow] (ID: {current_user.id})",
                    style="bold cyan",
                )
            )

            # Dashboard Menu
            choice = questionary.select(
                "Main Menu:",
                choices=[
                    "Create Service Request",
                    "View Order History",
                    "Update Profile",
                    "Logout",
                ],
            ).ask()

            if choice == "Create Service Request":
                # ✅ PASS THE LOGGED-IN USER OBJECT HERE
                create_service_request_ui(current_user)

            elif choice == "Logout":
                current_user = None
                console.print("[yellow]Logged out successfully.[/yellow]")
                questionary.press_any_key_to_continue().ask()

            else:
                # Placeholder for features we haven't built yet
                console.print("[dim]This feature is coming in the next module...[/dim]")
                questionary.press_any_key_to_continue().ask()


if __name__ == "__main__":
    main()
