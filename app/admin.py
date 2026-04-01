import questionary
from sqlmodel import Session, select
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from app.database import engine
from app.models import User



console = Console()

# This method is containing search user functionality
def search_user_ui():
    console.clear()
    console.print(Panel("Search User (Admin)", style="bold cyan"))
    # admin can search user using following two fields
    search_type = questionary.select(
        "Search user by:",
        choices=["User Name", "Mobile Number"]
    ).ask()

    if not search_type:
        return
    #search by user name
    if search_type == "User Name":
        value = questionary.text("Enter User Name:").ask()
        statement = select(User).where(User.user_name.ilike(f"%{value}%"))
     # or by mobile number
    else:
        value = questionary.text("Enter Mobile Number:").ask()
        statement = select(User).where(User.contact_number == value)

    with Session(engine) as session:
        users = session.exec(statement).all()
     # if user not found
    if not users:
        console.print(Panel("No user found.", style="bold yellow"))
        questionary.press_any_key_to_continue().ask()
        return

    table = Table(title="Search Results", show_lines=True)
    table.add_column("User ID", justify="center", style="cyan")
    table.add_column("User Name", style="green")
    table.add_column("Email", style="white")
    table.add_column("Mobile", style="magenta")

    for user in users:
        table.add_row(
            str(user.id),
            user.user_name,
            user.email,
            user.contact_number
        )

    console.print(table)
    questionary.press_any_key_to_continue().ask()


# this methods is containing delete user functionality
def remove_user_ui():
    console.clear()
    # Admin panel heading
    console.print(Panel("Remove User (Admin)", style="bold red"))

    # Ask admin for username to delete
    username = questionary.text(
        "Enter Username to delete:",
        validate=lambda text: True if len(text.strip()) > 0 else "Username cannot be empty."
    ).ask()

    
    if not username:
        return

    with Session(engine) as session:
        # Fetch user by username
        statement = select(User).where(User.user_name == username)
        user = session.exec(statement).first()

        # If user does not exist
        if not user:
            console.print(Panel("User not found.", style="bold yellow"))
            questionary.press_any_key_to_continue().ask()
            return

        # Final confirmation before deletion
        confirm = questionary.confirm(
            f"Are you sure you want to delete user '{user.user_name}'?"
        ).ask()

        if not confirm:
            console.print("[yellow]Deletion cancelled.[/yellow]")
            questionary.press_any_key_to_continue().ask()
            return

        # Delete user from database
        session.delete(user)
        session.commit()

        # Success message
        console.print(Panel("User deleted successfully.", style="bold green"))
        questionary.press_any_key_to_continue().ask()





