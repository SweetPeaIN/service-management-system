import questionary
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime, timedelta

from sqlmodel import select, Session

from app.database import engine
from app.models import ServiceRequest, User
from app.utils import paginate_results

console = Console()

# Pricing Configuration
VENDOR_PRICING = {
    "Vendor A": 100,
    "Vendor B": 150,
    "Vendor C": 200
}

# --- VALIDATION FUNCTIONS ---
def validate_date_input(date_text: str):
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_text):
        return "Use format YYYY-MM-DD (Example: 2026-02-07)"

    try:
        entered_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid date"

    today = datetime.today().date()
    max_date = today + timedelta(days=30)

    if entered_date < today:
        return "Cannot book for past dates"
    if entered_date > max_date:
        return "Bookings allowed only up to 1 month in advance"

    return True

# --- DATABASE FUNCTIONS ---
def save_request_to_db(request_data: ServiceRequest):
    """
    Saves the request to the database.
    Relies on SQLModel/Database to throw an error if ID exists.
    """
    with Session(engine) as session:
        session.add(request_data)
        session.commit()
        session.refresh(request_data) 
        return request_data

# --- UI FUNCTIONS ---
def create_service_request_ui(current_user: User):
    console.clear()
    console.print(Panel("Create New Service Request", style="bold cyan"))

    # 1. Select Service
    service_type = questionary.select(
        "Select Service Type:",
        choices=["AC Repair", "TV Repair", "Fridge Repair", "Washing Machine Repair"]
    ).ask()
    if not service_type: return

    # 2. Enter Date
    date_input = questionary.text(
        "Enter Preferred Date (YYYY-MM-DD):",
        validate=validate_date_input
    ).ask()
    if not date_input: return

    # 3. Select Time
    time_slot = questionary.select(
        "Select Time Slot:",
        choices=[
            "09:00 AM - 10:00 AM", "10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM",
            "12:00 PM - 01:00 PM", "01:00 PM - 02:00 PM", "02:00 PM - 03:00 PM",
            "03:00 PM - 04:00 PM", "04:00 PM - 05:00 PM", "05:00 PM - 06:00 PM"
        ]
    ).ask()
    if not time_slot: return

    date_slot_combined = f"{date_input} | {time_slot}"

    # 4. Address
    address = questionary.text(
        "Confirm Service Address:",
        default=current_user.address,
        validate=lambda text: True if len(text) <= 100 else "Address too long (max 100 chars)."
    ).ask()
    if not address: return

    # 5. Vendor
    vendor_choice = questionary.select(
        "Select a Vendor:",
        choices=[
            f"Vendor A (${VENDOR_PRICING['Vendor A']})",
            f"Vendor B (${VENDOR_PRICING['Vendor B']})",
            f"Vendor C (${VENDOR_PRICING['Vendor C']})"
        ]
    ).ask()
    if not vendor_choice: return

    vendor_name = vendor_choice.split(" ($")[0]
    amount = VENDOR_PRICING[vendor_name]

    # 6. Save Logic (The Fix)
    new_request = ServiceRequest(
        customer_id=current_user.id,
        service_name=service_type,
        date_slot=date_slot_combined,
        address=address,
        vendor_name=vendor_name,
        amount=amount,
        status="Pending"
    )

    try:
        # Actually calling the DB function now
        saved_request = save_request_to_db(new_request)

        console.print(Panel(
            f"[bold green]Service Request Created Successfully![/bold green]\n"
            f"Order ID: {saved_request.id}\n"
            f"Service: {saved_request.service_name}\n"
            f"Vendor: {saved_request.vendor_name}\n"
            f"Total: ${saved_request.amount}",
            style="green"
        ))

    except Exception as e:
        # This catches the IntegrityError if IDs collide
        console.print(f"[bold red]Error saving request:[/bold red] {e}")

    questionary.press_any_key_to_continue().ask()

def render_history_table(results):
    """
    Draws the table for User Order History.
    Used by the pagination engine.
    """
    table = Table(show_lines=True)
    table.add_column("Service ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Service Type", justify="left", style="bold white")
    table.add_column("Vendor", justify="left")
    table.add_column("Booking Date", justify="center")
    table.add_column("Status", justify="center", style="bold yellow")

    for req in results:
        booking_date = req.created_at.strftime("%Y-%m-%d") if req.created_at else "N/A"
        
        table.add_row(
            str(req.id),
            req.service_name,
            req.vendor_name,
            booking_date,
            req.status
        )
    console.print(table)

def view_order_history_ui(current_user: User):
    """
    Fetches and displays the service history using the shared Pagination Engine.
    """
    with Session(engine) as session:
        # We define the query, filtering ONLY for this customer
        statement = select(ServiceRequest).where(ServiceRequest.customer_id == current_user.id)
        
        # Hand off control to the utility
        paginate_results(
            session=session,
            statement=statement,
            render_func=render_history_table,
            title=f"Order History for {current_user.user_name}"
        )