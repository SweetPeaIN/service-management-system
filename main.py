import sys
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.align import Align

# Import our custom modules from the app package
from app.database import create_db_and_tables
from app.auth import login_user, register_user
from app.service_mgr import create_service_request_ui, view_order_history_ui, view_all_orders_ui

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
            # Define the ASCII Art
            # You can customize this art at: https://patorjk.com/software/taag/
            banner_art = r"""
                                                                                                                                                               
 ▄▄▄▄▄▄▄                                     ▄▄▄      ▄▄▄                                                             ▄▄▄▄▄▄▄                                  
█████▀▀▀                   ▀▀                ████▄  ▄████                                                     ██     █████▀▀▀              ██                  
 ▀████▄  ▄█▀█▄ ████▄ ██ ██ ██  ▄████ ▄█▀█▄   ███▀████▀███  ▀▀█▄ ████▄  ▀▀█▄ ▄████ ▄█▀█▄ ███▄███▄ ▄█▀█▄ ████▄ ▀██▀▀    ▀████▄  ██ ██ ▄█▀▀▀ ▀██▀▀ ▄█▀█▄ ███▄███▄ 
   ▀████ ██▄█▀ ██ ▀▀ ██▄██ ██  ██    ██▄█▀   ███  ▀▀  ███ ▄█▀██ ██ ██ ▄█▀██ ██ ██ ██▄█▀ ██ ██ ██ ██▄█▀ ██ ██  ██        ▀████ ██▄██ ▀███▄  ██   ██▄█▀ ██ ██ ██ 
███████▀ ▀█▄▄▄ ██     ▀█▀  ██▄ ▀████ ▀█▄▄▄   ███      ███ ▀█▄██ ██ ██ ▀█▄██ ▀████ ▀█▄▄▄ ██ ██ ██ ▀█▄▄▄ ██ ██  ██     ███████▀  ▀██▀ ▄▄▄█▀  ██   ▀█▄▄▄ ██ ██ ██ 
                                                                               ██                                               ██                             
                                                                             ▀▀▀                                              ▀▀▀                                               

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

        # --- STATE B: User IS Logged In (Dashboard) ---
        else:
            console.clear()
            is_admin = current_user.user_name == "Aman Solanki"
            # Show who is logged in
            console.print(
                Panel(
                    f"Dashboard\nLogged in as: [bold yellow]{current_user.user_name}[/bold yellow] (ID: {current_user.id})",
                    style="bold cyan",
                )
            )

            # Dashboard Menu

            # Admin
            if is_admin:
                choice = questionary.select(
                    "Admin Menu:",
                    choices=[
                        "View All Order History",
                        "Logout",
                    ],
                ).ask()

                if choice == "View All Order History":
                    view_all_orders_ui()

                elif choice == "Logout":
                    current_user = None
                    questionary.press_any_key_to_continue().ask()
            
            # User

            else :
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
                    # Placeholder for features we haven't built yet
                    console.print("[dim]This feature is coming in the next module...[/dim]")
                    questionary.press_any_key_to_continue().ask()


if __name__ == "__main__":
    main()
