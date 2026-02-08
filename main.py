import sys
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.align import Align

# Import our custom modules from the app package
from app.database import create_db_and_tables
from app.auth import login_user, register_user
from app.service_mgr import create_service_request_ui, view_order_history_ui
from app.admin_mgr import show_admin_dashboard

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
            banner_art = r"""
========================================
      SERVICE MANAGEMENT SYSTEM
========================================
"""

            # We use Align.center to make it look professional on any terminal width
            styled_banner = Align.center(
            Panel(banner_art, style="bold cyan", border_style="blue", padding=(1, 2))
            )
    
            console.print(styled_banner)
            console.print("\n") # Add some breathing room
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

        # --- STATE B: ADMIN MODE (Updated) ---
        elif current_user == "ADMIN":
            show_admin_dashboard()
            current_user = None # reset the user to None (Logout).

        # --- STATE C: Customer Dashboard (Existing Logic) ---
        elif isinstance(current_user, object): 
            # We use 'elif' here to be explicit, or just 'else' acts as catch-all for Customers
            console.clear()
            console.print(
                Panel(
                    f"Dashboard\nLogged in as: [bold yellow]{current_user.user_name}[/bold yellow] (ID: {current_user.id})",
                    style="bold cyan",
                )
            )

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
                create_service_request_ui(current_user)

            elif choice == "View Order History":
                view_order_history_ui(current_user)

            elif choice == "Logout":
                current_user = None
                console.print("[yellow]Logged out successfully.[/yellow]")
                questionary.press_any_key_to_continue().ask()

            else:
                console.print("[dim]This feature is coming soon...[/dim]")
                questionary.press_any_key_to_continue().ask()

if __name__ == "__main__":
    main()