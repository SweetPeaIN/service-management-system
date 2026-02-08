import math
import questionary
from sqlmodel import Session, select, func
from rich.console import Console
from rich.panel import Panel

console = Console()
PAGE_SIZE = 5

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