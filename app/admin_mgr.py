from sqlmodel import Session, select, delete, col
from sqlalchemy.exc import IntegrityError

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import questionary

from app.database import engine
from app.models import User, ServiceRequest
from app.utils import paginate_results

console = Console()

# 1. The Renderer (Pure UI Logic)
def render_orders_table(results):
    table = Table(show_lines=True)
    
    table.add_column("Order ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Cust ID", justify="center", style="magenta")
    table.add_column("Service", justify="left", style="bold white")
    table.add_column("Vendor", justify="left")
    table.add_column("Amount", justify="right", style="green")
    table.add_column("Status", justify="center")
    table.add_column("Date", justify="center")

    for req in results:
        status_style = "yellow" if req.status == "Pending" else "green"
        status_text = f"[{status_style}]{req.status}[/{status_style}]"
        booking_date = req.created_at.strftime("%Y-%m-%d") if req.created_at else "N/A"

        table.add_row(
            str(req.id),
            str(req.customer_id),
            req.service_name,
            req.vendor_name,
            f"${req.amount}",
            status_text,
            booking_date
        )
    console.print(table)

def view_all_orders():
    """
    Fetches every service request using the generic pagination engine.
    """
    with Session(engine) as session:
        # We just define the query. The engine handles the fetching loop.
        statement = select(ServiceRequest)
        
        paginate_results(
            session=session,
            statement=statement,
            render_func=render_orders_table,
            title="All Service Orders (Admin View)"
        )

def change_order_status_ui():
    """
    Allows the Admin to update the lifecycle status of a specific Service Request.
    """
    console.clear()
    console.print(Panel("Change Order Status", style="bold blue"))

    # 1. Target Selection
    order_id_input = questionary.text("Enter Order ID to update:").ask()

    # Basic Validation
    if not order_id_input.isdigit():
        console.print("[red]Error: Order ID must be a number.[/red]")
        questionary.press_any_key_to_continue().ask()
        return

    order_id = int(order_id_input)

    with Session(engine) as session:
        # 2. Find Record (Efficient Retrieval)
        # Explainability: session.get(Model, PK) is the most optimized way to fetch a row.
        # It skips the overhead of constructing a WHERE clause because it looks directly up the Primary Key index.
        order = session.get(ServiceRequest, order_id)

        if not order:
            console.print(Panel(f"[bold red]Error:[/bold red] Order ID {order_id} not found."))
            questionary.press_any_key_to_continue().ask()
            return

        # ... (after order retrieval and existence check) ...
        if order.status == "Completed":
            console.print(Panel(
                "[bold red]Action Denied:[/bold red] This order is already 'Completed' and cannot be modified.",
                title="Locked Record",
                style="red"
            ))
            questionary.press_any_key_to_continue().ask()
            return


        # 3. Display Current State (Context is King)
        console.print(Panel(
            f"[bold]Service:[/bold] {order.service_name}\n"
            f"[bold]Vendor:[/bold] {order.vendor_name}\n"
            f"[bold]Customer ID:[/bold] {order.customer_id}\n"
            f"[bold]Current Status:[/bold] [yellow]{order.status}[/yellow]",
            title=f"Order #{order.id} Details",
            style="cyan"
        ))

        # 4. Status Submenu
        new_status = questionary.select(
            "Select New Status:",
            choices=[
                "In Progress",
                "Completed",
                "Cancelled",
                "Back"
            ]
        ).ask()

        if new_status == "Back":
            return

        # 5. Database Update
        try:
            # We modify the Python object directly
            order.status = new_status
            
            # session.add tells SQLModel this object is 'dirty' and needs saving
            session.add(order)
            session.commit()
            session.refresh(order)

            console.print(Panel(
                f"[bold green]Success:[/bold green] Order #{order.id} status updated to '{order.status}'.",
                style="green"
            ))

        except Exception as e:
            session.rollback()
            console.print(f"[bold red]Database Error:[/bold red] {e}")
    
    questionary.press_any_key_to_continue().ask()

def display_users(results: list[User]):
    """
    Helper function to render a list of Users in a Rich Table.
    Keeps the main logic clean.
    """
    if not results:
        console.print(Panel("[yellow]No users found matching that criteria.[/yellow]", title="Search Results"))
        return

    table = Table(title=f"Search Results ({len(results)} found)", show_lines=True)
    
    # Define Columns
    table.add_column("ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Username", style="magenta")
    table.add_column("Email", style="blue")
    table.add_column("Address")
    table.add_column("Contact")

    for user in results:
        table.add_row(
            str(user.id),
            user.user_name,
            user.email,
            user.address,
            user.contact_number
        )

    console.print(table)

def search_user_ui():
    """
    Submenu for searching users by specific fields.
    """
    console.clear()
    console.print(Panel("Search Customer Database", style="bold blue"))

    # 1. Submenu: Choose Search Parameter
    search_by = questionary.select(
        "Search by:",
        choices=[
            "User ID",
            "Username",
            "Email",
            "Contact Number",
            "Back to Dashboard"
        ]
    ).ask()

    if search_by == "Back to Dashboard":
        return

    # 2. Get Input
    search_term = questionary.text(f"Enter {search_by}:").ask()
    if not search_term: return

    # 3. Database Logic
    with Session(engine) as session:
        statement = select(User)

        # We build the query based on the selection
        if search_by == "User ID":
            # Integer search remains exact
            if not search_term.isdigit():
                console.print("[red]Error: User ID must be a number.[/red]")
                questionary.press_any_key_to_continue().ask()
                return
            statement = statement.where(User.id == int(search_term))

        elif search_by == "Username":
            # CASE SENSITIVE SEARCH (GLOB)
            # GLOB uses '*' as a wildcard instead of '%'.
            # "David" will match "David", "Davids", but NOT "david".
            statement = statement.where(col(User.user_name).op("GLOB")(f"*{search_term}*"))

        elif search_by == "Email":
            # CASE SENSITIVE SEARCH (GLOB)
            statement = statement.where(col(User.email).op("GLOB")(f"*{search_term}*"))

        elif search_by == "Contact Number":
            # CASE SENSITIVE SEARCH (GLOB)
            statement = statement.where(col(User.contact_number).op("GLOB")(f"*{search_term}*"))
            
        # Execute
        results = session.exec(statement).all()

        # 4. Display
        display_users(results)
    
    questionary.press_any_key_to_continue().ask()

from sqlmodel import select, delete, Session
from sqlalchemy.exc import IntegrityError
# ... (Keep existing imports)

def remove_user_ui():
    """
    Safely removes a user and their associated service history.
    Uses an Atomic Transaction to ensure data integrity.
    """
    console.clear()
    console.print(Panel("Remove User & History", style="bold red"))

    # 1. Identify Target
    target_id_input = questionary.text("Enter User ID to remove:").ask()
    
    # Basic Validation
    if not target_id_input.isdigit():
        console.print("[red]Error: User ID must be a number.[/red]")
        questionary.press_any_key_to_continue().ask()
        return
    
    target_id = int(target_id_input)

    with Session(engine) as session:
        # 2. Safety Check: Does User Exist?
        user_to_delete = session.get(User, target_id)
        
        if not user_to_delete:
            console.print(Panel(f"[bold red]Error:[/bold red] User ID {target_id} not found."))
            questionary.press_any_key_to_continue().ask()
            return

        # 3. Impact Analysis: Count associated records
        # We search for requests where customer_id matches our target
        statement = select(ServiceRequest).where(ServiceRequest.customer_id == target_id)
        linked_requests = session.exec(statement).all()
        count = len(linked_requests)

        # 4. Final Warning / Confirmation
        console.print(Panel(
            f"[bold]User:[/bold] {user_to_delete.user_name} (ID: {user_to_delete.id})\n"
            f"[bold]Full Name:[/bold] {user_to_delete.user_name}\n" # Assuming user_name holds the name based on previous models
            f"[bold]Associated Orders:[/bold] {count}",
            title="Confirm Deletion",
            style="yellow"
        ))

        confirm = questionary.confirm(
            f"WARNING: This will permanently delete the user AND {count} service records. Proceed?",
            default=False
        ).ask()

        if not confirm:
            console.print("[green]Deletion cancelled.[/green]")
            questionary.press_any_key_to_continue().ask()
            return

        # 5. The Atomic Transaction
        try:
            # Step A: Delete Child Records (ServiceRequests)
            # We use the delete() statement for efficiency
            delete_statement = delete(ServiceRequest).where(ServiceRequest.customer_id == target_id)
            session.exec(delete_statement)

            # Step B: Delete Parent Record (User)
            session.delete(user_to_delete)

            # Step C: Commit (The Point of No Return)
            session.commit()

            console.print(Panel(
                f"[bold green]Success:[/bold green] User {target_id} and {count} linked orders have been removed.",
                style="green"
            ))

        except IntegrityError as e:
            # This catches database constraints we might have missed
            session.rollback()
            console.print(f"[bold red]Database Integrity Error:[/bold red] {e}")
        except Exception as e:
            session.rollback()
            console.print(f"[bold red]Unexpected Error:[/bold red] {e}")

    questionary.press_any_key_to_continue().ask()

def show_admin_dashboard():
    """
    The main loop for the Admin Interface.
    Control stays here until 'Logout' is selected.
    """
    while True:
        console.clear()
        
        # Visual Distinction: Purple Style for Admin
        console.print(Panel(
            "[bold magenta]ADMIN DASHBOARD[/bold magenta]\n"
            "Manage Users, Orders, and System Settings",
            style="magenta",
            subtitle="[dim]Access Level: Superuser[/dim]"
        ))

        choice = questionary.select(
            "Admin Menu:",
            choices=[
                "View All Orders",
                "Change Order Status",
                "Search a User",
                "Remove User",
                "Logout"
            ]
        ).ask()

        # --- NAVIGATION LOGIC ---
        if choice == "View All Orders":
            view_all_orders()

        elif choice == "Change Order Status":
            change_order_status_ui()

        elif choice == "Search a User":
            search_user_ui()

        elif choice == "Remove User":
            remove_user_ui()

        elif choice == "Logout":
            # Breaking this loop returns control to main.py
            console.print("[yellow]Logging out...[/yellow]")
            break