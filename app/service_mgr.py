import questionary
from questionary import Choice
import re
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from sqlmodel import select, Session

from app.database import engine
from app.models import ServiceRequest, User
from app.utils import paginate_results, validate_email, validate_contact, validate_password_complexity
from app.profile_ui import render_profile_dashboard

console = Console()

# Vendor Data dict rich dataset
VENDOR_DATA = [
    {
        "name": "Vendor A",
        "price": 100,
        "rating": 4.2,
        "experience": "3 Yrs - Generalist",
        "badge": "Reliable"
    },
    {
        "name": "Vendor B",
        "price": 150,
        "rating": 4.6,
        "experience": "8 Yrs - Specialist",
        "badge": "Top Rated"
    },
    {
        "name": "Vendor C",
        "price": 200,
        "rating": 4.9,
        "experience": "15 Yrs - Expert",
        "badge": "Premium"
    }
]

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

# --- HELPER UI FUNCTIONS ---
def display_vendor_options():
    """
    Renders a comparison table of available vendors.
    """
    table = Table(
        title="Available Service Partners",
        box=box.ROUNDED,
        header_style="bold cyan",
        expand=True
    )

    # Define Columns
    table.add_column("Vendor Name", style="bold white")
    table.add_column("Price", justify="right", style="green")
    table.add_column("Rating", justify="center", style="yellow")
    table.add_column("Experience & Expertise", style="dim")

    for v in VENDOR_DATA:
        # Convert numeric rating to stars
        # Example: 4.5 -> ⭐⭐⭐⭐½ (Simplified to stars for terminal compatibility)
        stars = "⭐" * int(v['rating'])
        if v['rating'] % 1 >= 0.5:
            stars += "½"

        table.add_row(
            v['name'],
            f"${v['price']}",
            f"{v['rating']} {stars}",
            v['experience']
        )

    console.print(table)
    console.print("\n") # Spacing

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

    # 5. Vendor Selection (ENHANCED)
    console.clear() # Clear screen to focus on the comparison
    console.print(Panel(f"Step 5: Select Vendor for [bold]{service_type}[/bold]", style="cyan"))

    # A. Show the Comparison Table
    display_vendor_options()

    # B. Build the 'Rich' Choices
    # We use questionary.Choice to display a string but return the Dictionary object
    vendor_choices = []
    for v in VENDOR_DATA:
        vendor_choices.append(
            Choice(
                title=f"{v['name']} -- ${v['price']} ({v['experience']})",
                value=v # <--- CRITICAL: Passing the whole dict as the value
            )
        )
    vendor_choices.append("Cancel Request")

    # C. Capture the Object
    selected_vendor = questionary.select(
        "Choose your service partner:",
        choices=vendor_choices
    ).ask()

    if selected_vendor == "Cancel Request" or selected_vendor is None:
        console.print("[yellow] Request creation cancelled.[/yellow]")
        questionary.press_any_key_to_continue().ask()
        return

    # 6. Save Logic
    # Now we access data directly from the selected object
    new_request = ServiceRequest(
        customer_id=current_user.id,
        service_name=service_type,
        date_slot=date_slot_combined,
        address=address,
        vendor_name=selected_vendor['name'], # Direct Access
        amount=selected_vendor['price'],     # Direct Access
        status="Pending"
    )

    try:
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

        if field_choice == "Back to Dashboard" or field_choice == None:
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

                elif new_val is None: return

            elif field_choice == "Update Contact Number":
                new_val = questionary.text(
                    f"Update Contact (Current: {user_in_db.contact_number}):",
                    default=user_in_db.contact_number,
                    validate=validate_contact
                ).ask()

                if new_val:
                    user_in_db.contact_number = new_val
                    current_user.contact_number = new_val

                elif new_val is None: return

            elif field_choice == "Update Address":
                new_val = questionary.text(
                    f"Update Address (Current: {user_in_db.address}):",
                    default=user_in_db.address,
                    validate=lambda t: len(t) <= 100
                ).ask()

                if new_val:
                    user_in_db.address = new_val
                    current_user.address = new_val

                elif new_val is None: return

            elif field_choice == "Update Password":
                console.print("[dim]Enter a new password.[/dim]")
                val1 = questionary.password("Enter New Password:", validate=validate_password_complexity).ask()
                if not val1: return

                val2 = questionary.password("Confirm New Password:").ask()
                if not val2: return

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