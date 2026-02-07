import questionary
from rich.console import Console
console=Console()
def go_to_admin_dashboard(admin_user=None):
    """Admin dashboard loop with menu options."""
    while True:
        console.print(f"[green]Logged in as Admin[/green]")

        choice = questionary.select(
            "Admin Menu:",
            choices=[
                "View Order History",
                "Search User",
                "Remove User",
                "Logout",
            ],
        ).ask()

        if choice == "View Order History":
            view_order_history_ui(admin_user)
                
                                           

        elif choice == "Search User":
            search_user_ui(admin_user)

        elif choice == "Remove User":
            remove_user_ui(admin_user)

        elif choice == "Logout":
            admin_user = None
            console.print("[yellow]Logged out successfully.[/yellow]")
            questionary.press_any_key_to_continue().ask()
            break  # exit the loop and return to login

        else:
            # Placeholder for features we haven't built yet
            console.print("[dim]This feature is coming in the next module...[/dim]")
            questionary.press_any_key_to_continue().ask()
