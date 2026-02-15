import questionary
import re
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sqlmodel import select, Session

from app.database import engine
from app.models import ServiceRequest, User
from app.utils import paginate_results, validate_email, validate_contact, validate_password_complexity
from app.profile_ui import render_profile_dashboard

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
    Now displays ALL fields from the ServiceRequest table.
    """
    table = Table(show_lines=True)
    
    # 1. Define Columns for ALL Database Fields
    table.add_column("Order ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Cust ID", justify="center", style="dim")
    table.add_column("Service", justify="left", style="bold white")
    table.add_column("Vendor", justify="left")
    table.add_column("Amount", justify="right", style="green")
    table.add_column("Status", justify="center", style="bold yellow")
    table.add_column("Scheduled Slot", justify="left", style="blue")
    table.add_column("Address", justify="left")
    table.add_column("Created On", justify="center", style="dim")

    # 2. Populate Rows
    for req in results:
        # Format the timestamp nicely
        created_date = req.created_at.strftime("%Y-%m-%d") if req.created_at else "N/A"
        
        table.add_row(
            str(req.id),
            str(req.customer_id),
            req.service_name,
            req.vendor_name,
            f"${req.amount}",
            req.status,
            req.date_slot,
            req.address,
            created_date
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


def update_profile_ui(current_user: User):
    """
    Allows the user to update their profile details.
    Delegates visual rendering to app.profile_ui.
    """
    while True:
        # 1. RENDER THE UI (Visual Separation)
        # This function handles the clear screen, random themes, and avatar drawing.
        render_profile_dashboard(current_user)

        # 2. MENU LOGIC
        field_choice = questionary.select(
            "What would you like to update?",
            choices=[
                "Update Email",
                "Update Contact Number",
                "Update Address",
                "Update Password",
                "Back to Dashboard"
            ]
        ).ask()

        if field_choice == "Back to Dashboard":
            break

        # 3. DATABASE LOGIC (Transactional)
        with Session(engine) as session:
            # Fetch fresh user record
            user_in_db = session.get(User, current_user.id)
            
            if not user_in_db:
                console.print("[red]Error: User record not found.[/red]")
                return

            # --- INPUT & UPDATE HANDLERS ---
            
            if field_choice == "Update Email":
                new_val = questionary.text(
                    f"Update Email (Current: {user_in_db.email}):",
                    default=user_in_db.email, 
                    validate=validate_email
                ).ask()
                
                if new_val:
                    user_in_db.email = new_val
                    current_user.email = new_val 

            elif field_choice == "Update Contact Number":
                new_val = questionary.text(
                    f"Update Contact (Current: {user_in_db.contact_number}):",
                    default=user_in_db.contact_number,
                    validate=validate_contact
                ).ask()
                
                if new_val:
                    user_in_db.contact_number = new_val
                    current_user.contact_number = new_val

            elif field_choice == "Update Address":
                new_val = questionary.text(
                    f"Update Address (Current: {user_in_db.address}):",
                    default=user_in_db.address,
                    validate=lambda t: len(t) <= 100
                ).ask()
                
                if new_val:
                    user_in_db.address = new_val
                    current_user.address = new_val

            elif field_choice == "Update Password":
                console.print("[dim]Note: For security, you must enter a completely new password.[/dim]")
                val1 = questionary.password("Enter New Password:", validate=validate_password_complexity).ask()
                val2 = questionary.password("Confirm New Password:").ask()
                
                if val1 != val2:
                    console.print("[bold red]Error:[/bold red] Passwords do not match.")
                    questionary.press_any_key_to_continue().ask()
                    continue 
                
                user_in_db.password = val1
                current_user.password = val1

            # 4. COMMIT
            try:
                session.add(user_in_db)
                session.commit()
                session.refresh(user_in_db)
                
                # We don't need a huge success panel here because the loop restarts
                # and the new data appears instantly on the "Identity Card".
                # A subtle confirmation is enough.
                # console.print(f"[green]>> Success! {field_choice} completed.[/green]")
                # questionary.press_any_key_to_continue().ask()
                
            except Exception as e:
                session.rollback()
                console.print(f"[bold red]Update Failed:[/bold red] {e}")
                questionary.press_any_key_to_continue().ask()