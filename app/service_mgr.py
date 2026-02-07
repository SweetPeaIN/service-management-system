import questionary
from sqlmodel import Session
from rich.console import Console
from rich.panel import Panel
from app.database import engine
from app.models import ServiceRequest, User
from rich.table import Table
from sqlmodel import select

console = Console()

# Pricing Configuration (Fixed per Vendor as requested)
VENDOR_PRICING = {
    "Vendor A": 100,
    "Vendor B": 150,
    "Vendor C": 200
}

def save_request_to_db(request_data: ServiceRequest):
    """
    Independent function to handle the Database Transaction.
    This separates the 'saving' logic from the 'ui' logic.
    """
    with Session(engine) as session:
        session.add(request_data)
        session.commit()
        session.refresh(request_data) # Refresh to get the generated ID
        return request_data

def create_service_request_ui(current_user: User):
    """
    Handles the Interactive Menu for creating a request.
    Receives the 'current_user' object from main.py.
    """
    console.clear()
    console.print(Panel("Create New Service Request", style="bold cyan"))

    # 1. Select Service
    service_type = questionary.select(
        "Select Service Type:",
        choices=["AC Repair", "TV Repair", "Fridge Repair", "Washing Machine Repair"]
    ).ask()
    if not service_type: return # Handle cancel

    # 2. Select Date/Slot
    date_slot = questionary.text("Enter Preferred Date/Time (e.g., 2023-10-25 10AM):").ask()

    # 3. Address (Pre-fill with user's registered address for better UX)
    address = questionary.text(
        "Confirm Service Address:",
        default=current_user.address,
        validate=lambda text: True if len(text) <= 100 else "Address too long (max 100 chars)."
    ).ask()

    # 4. Vendor Selection
    vendor_choice = questionary.select(
        "Select a Vendor:",
        choices=[
            f"Vendor A (${VENDOR_PRICING['Vendor A']})",
            f"Vendor B (${VENDOR_PRICING['Vendor B']})",
            f"Vendor C (${VENDOR_PRICING['Vendor C']})"
        ]
    ).ask()

    # Parse the vendor name from the string (e.g., "Vendor A ($100)" -> "Vendor A")
    vendor_name = vendor_choice.split(" ($")[0]
    amount = VENDOR_PRICING[vendor_name]

    # 5. Confirmation
    confirm = questionary.confirm(f"Confirm booking for {service_type} with {vendor_name} for ${amount}?").ask()

    if confirm:
        # Construct the Model Object
        new_request = ServiceRequest(
            customer_id=current_user.id,
            service_name=service_type,
            date_slot=date_slot,
            address=address,
            vendor_name=vendor_name,
            amount=amount
        )

        try:
            # Call our separate DB function
            saved_request = save_request_to_db(new_request)
            
            console.print(Panel(
                f"[bold green]Booking is successful![/bold green]\n"
                f"Order ID: {saved_request.id}\n"
                f"Service: {saved_request.service_name}\n"
                f"Vendor: {saved_request.vendor_name}",
                style="green"
            ))
        except Exception as e:
            console.print(f"[bold red]Error saving request:[/bold red] {e}")
    else:
        console.print("[yellow]Booking cancelled.[/yellow]")

    questionary.press_any_key_to_continue().ask()


def view_order_history_ui(current_user: User):
    """
    Fetches and displays the service history for the logged-in user.
    """
    console.clear()
    
    # 1. Fetch Data
    with Session(engine) as session:
        statement = select(ServiceRequest).where(ServiceRequest.customer_id == current_user.id)
        results = session.exec(statement).all()

    # 2. Handle Empty State
    if not results:
        console.print(Panel("No service history found.", style="bold yellow"))
        questionary.press_any_key_to_continue().ask()
        return

    # 3. Create Rich Table
    table = Table(title=f"Order History for {current_user.user_name}", show_lines=True)

    # Define Columns (Symmetric and organized)
    table.add_column("Service ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Customer ID", justify="center", style="magenta")
    table.add_column("User Name", justify="left", style="green")
    table.add_column("Service Type", justify="left", style="bold white")
    table.add_column("Booking Date", justify="center") # From created_at
    table.add_column("Scheduled Slot", justify="left") # From date_slot
    table.add_column("Status", justify="center", style="bold yellow")

    # 4. Populate Rows
    for req in results:
        # Format the date nicely (YYYY-MM-DD)
        booking_date = req.created_at.strftime("%Y-%m-%d") if req.created_at else "N/A"
        
        table.add_row(
            str(req.id),
            str(current_user.id),
            current_user.user_name,
            req.service_name,
            booking_date,
            req.date_slot,
            req.status
        )

    # 5. Display
    console.print(table)
    print("\n") # Add a little breathing room
    questionary.press_any_key_to_continue().ask()

    # Admin Functionality

def view_all_orders_ui():
    """
    Admin feature: View service history of ALL users
    """
    console.clear()

    with Session(engine) as session:
        statement = (
            select(ServiceRequest, User)
            .where(ServiceRequest.customer_id == User.id)
        )
        results = session.exec(statement).all()

    if not results:
        console.print(Panel("No service requests found.", style="bold yellow"))
        questionary.press_any_key_to_continue().ask()
        return

    table = Table(title="All Service Requests (Admin View)", show_lines=True)

    table.add_column("Order ID", justify="center", style="cyan")
    table.add_column("User ID", justify="center")
    table.add_column("Username", style="green")
    table.add_column("Service", style="white")
    table.add_column("Vendor")
    table.add_column("Amount", justify="right")
    table.add_column("Status", style="yellow")
    table.add_column("Booking Date")

    for service, user in results:
        booking_date = service.created_at.strftime("%Y-%m-%d")

        table.add_row(
            str(service.id),
            str(user.id),
            user.user_name,
            service.service_name,
            service.vendor_name,
            str(service.amount),
            service.status,
            service.date_slot
        )

    console.print(table)
    questionary.press_any_key_to_continue().ask()
