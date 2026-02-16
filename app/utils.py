import math
import re

import questionary
from sqlmodel import Session, select, func
from rich.console import Console
from rich.panel import Panel

console = Console()
PAGE_SIZE = 5

def validate_email(text):
    # Simple regex for basic email format (user@domain.com)
    pattern = r"^(?!\.)(?!.*\.\.)([A-Za-z0-9._%+-]{1,64})@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$"
    if re.match(pattern, text) and len(text) <= 255:
        return True
    return "Please enter a valid email address (max 255 chars)."

def validate_password_complexity(text):
    if len(text) < 8 or len(text) > 30:
        return "Password must be between 8 and 30 characters."
    if not any(char.isupper() for char in text):
        return "Password must contain at least one uppercase letter."
    if not any(char.isdigit() for char in text):
        return "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", text):
        return "Password must contain at least one special character."
    return True

def validate_contact(text):
    if text.isdigit() and len(text) == 10 and text[0] in "6789":
        return True
    return "Contact Number must be exactly 10 digits and starts from 6,7,8,9."


def paginate_results(session: Session, statement, render_func, title: str):
    """
    A generic pagination engine for SQLModel queries.
    
    Args:
        session: The database session.
        statement: The base SQLModel select statement (without filters applied yet).
        render_func: A function that accepts 'results' and prints a Rich table.
        title: The title to display at the top of the view.
    """
    # 1. Calculate Total Records (Efficient Count Query)
    # We use a subquery to safely count results regardless of the original statement's complexity
    count_statement = select(func.count()).select_from(statement.subquery())
    total_records = session.exec(count_statement).one()
    
    if total_records == 0:
        console.clear()
        console.print(Panel(f"[yellow]No records found for: {title}[/yellow]", title="System Status"))
        questionary.press_any_key_to_continue().ask()
        return

    total_pages = math.ceil(total_records / PAGE_SIZE)
    current_page = 1

    # 2. The Pagination Loop
    while True:
        console.clear()
        
        # Calculate Offset
        offset = (current_page - 1) * PAGE_SIZE
        
        # Fetch ONLY the records for this page
        # We clone the statement to avoid modifying the original permanently
        paginated_statement = statement.offset(offset).limit(PAGE_SIZE)
        results = session.exec(paginated_statement).all()

        # UI Header
        console.print(Panel(
            f"[bold cyan]{title}[/bold cyan]\n"
            f"Page {current_page} of {total_pages} | Total Records: {total_records}",
            style="cyan"
        ))

        # 3. Delegate Rendering
        render_func(results)

        # 4. Dynamic Navigation Menu
        choices = []
        
        if current_page < total_pages:
            choices.append("Next Page >")
        
        if current_page > 1:
            choices.append("< Previous Page")
            
        choices.append("Back to Menu")

        choice = questionary.select(
            "Navigation:",
            choices=choices,
            use_indicator=True
        ).ask()

        # Handle Navigation
        if choice == "Next Page >":
            current_page += 1
        elif choice == "< Previous Page":
            current_page -= 1
        elif choice == "Back to Menu":
            break

