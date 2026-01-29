import questionary
import re
from sqlmodel import Session, select
from rich.console import Console
from rich.panel import Panel
from app.database import engine
from app.models import User

console = Console()

def validate_email(text):
    # Simple regex for basic email format (user@domain.com)
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if re.match(pattern, text) and len(text) <= 255:
        return True
    return "Please enter a valid email address (max 255 chars)."

def validate_contact(text):
    if text.isdigit() and len(text) == 10:
        return True
    return "Contact Number must be exactly 10 digits."

def register_user():
    console.clear()
    console.print(Panel("Register New Customer", style="bold blue"))

    # 1. Username (Max 50 chars)
    username = questionary.text(
        "Enter User Name:",
        validate=lambda text: True if len(text) > 0 and len(text) <= 50 else "Username must be 1-50 characters."
    ).ask()
    
    if not username: return  # Handle cancellation

    with Session(engine) as session:
        # Real-time DB check for duplicate username
        existing_user = session.exec(select(User).where(User.user_name == username)).first()
        if existing_user:
            console.print("[bold red]Error:[/bold red] Username already taken!")
            questionary.press_any_key_to_continue().ask()
            return

        # 2. Email (Format & Length check)
        email = questionary.text(
            "Enter Email:",
            validate=validate_email
        ).ask()

        # 3. Password (Max 30 chars)
        password = questionary.password(
            "Enter Password:",
            validate=lambda text: True if len(text) > 0 and len(text) <= 30 else "Password must be 1-30 characters."
        ).ask()

        confirm_password = questionary.password(
            "Confirm Password:",
            validate=lambda text: True if text == password else "Passwords do not match!"
        ).ask()
        
        # Handle case where user might cancel (Ctrl+C)
        if confirm_password is None: return
        
        # 4. Address (Max 100 chars)
        address = questionary.text(
            "Enter Address (Street, City):",
            validate=lambda text: True if len(text) <= 100 else "Address is too long (max 100 chars)."
        ).ask()

        # 5. Contact Number (Exactly 10 digits)
        contact = questionary.text(
            "Enter Contact Number:",
            validate=validate_contact
        ).ask()

        # Create User Object (ID generated automatically in models.py)
        new_user = User(
            user_name=username,
            email=email,
            password=password,
            address=address,
            contact_number=contact
        )

        try:
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            # Success Message
            console.print(Panel(
                f"[bold green]Customer Registration is successful[/bold green]\n"
                f"User ID: {new_user.id}\n"
                f"Name: {new_user.user_name}",
                style="bold green"
            ))
            
        except Exception as e:
            console.print(f"[bold red]Database Error:[/bold red] {e}")
        
        questionary.press_any_key_to_continue().ask()

def login_user() -> User | None:
    """Returns a User object if successful, None otherwise."""
    console.clear()
    console.print(Panel("Login", style="bold green"))

    username = questionary.text("Username:").ask()
    password = questionary.password("Password:").ask()

    with Session(engine) as session:
        statement = select(User).where(User.user_name == username)
        user = session.exec(statement).first()

        if user and user.password == password:
            console.print(f"[green]Welcome back, {user.user_name}![/green]")
            return user
        else:
            console.print("[bold red]Invalid username or password.[/bold red]")
            questionary.press_any_key_to_continue().ask()
            return None