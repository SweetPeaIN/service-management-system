import csv
from pathlib import Path
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError
from rich.console import Console
from rich.panel import Panel

# Import from the application logic
# Note: These imports work because we run the script from the Project Root
from app.database import engine
from app.models import User, ServiceRequest

console = Console()

def load_data():
    """
    Reads CSV files from the 'data/' directory and seeds the SQLite database.
    Handles type conversion and Foreign Key integrity.
    """
    # 1. Setup Paths
    # We use pathlib to find the CSVs relative to THIS script file
    base_path = Path(__file__).parent
    users_csv = base_path / "users.csv"
    requests_csv = base_path / "service_requests.csv"

    # Check if files exist
    if not users_csv.exists() or not requests_csv.exists():
        console.print("[bold red]Error:[/bold red] CSV files not found in 'data/' folder.")
        return

    user_count = 0
    request_count = 0

    try:
        with Session(engine) as session:
            # --- STEP A: Load Users ---
            console.print("[yellow]Seeding Users...[/yellow]")
            with open(users_csv, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # We explicitely set the ID to match the CSV, overriding the random generator
                    user = User(
                        id=int(row["id"]), 
                        user_name=row["user_name"],
                        email=row["email"],
                        password=row["password"],
                        address=row["address"],
                        contact_number=row["contact_number"]
                    )
                    # Merge checks if it exists (updates) or adds if new. 
                    # For seeding, 'add' is usually fine, but 'merge' is safer for re-runs.
                    session.merge(user)
                    user_count += 1

            # --- STEP B: Load Service Requests ---
            console.print("[yellow]Seeding Service Requests...[/yellow]")
            with open(requests_csv, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    request = ServiceRequest(
                        id=int(row["id"]),
                        customer_id=int(row["customer_id"]), # Must match a User ID from Step A
                        service_name=row["service_name"],
                        status=row["status"],
                        date_slot=row["date_slot"],
                        address=row["address"],
                        vendor_name=row["vendor_name"],
                        amount=int(row["amount"])
                    )
                    session.merge(request)
                    request_count += 1

            # --- STEP C: Commit Transaction ---
            session.commit()
            
            # Feedback
            console.print(Panel(
                f"[bold green]Database Seeding Successful![/bold green]\n"
                f"• Users Loaded: {user_count}\n"
                f"• Requests Loaded: {request_count}",
                title="System Initialization",
                style="green"
            ))

    except IntegrityError as e:
        session.rollback()
        console.print(Panel(
            f"[bold red]Integrity Error:[/bold red]\n"
            f"This usually means a User ID or Order ID already exists.\n"
            f"Details: {e}",
            style="red"
        ))
    except Exception as e:
        session.rollback()
        console.print(f"[bold red]Unexpected Error:[/bold red] {e}")

if __name__ == "__main__":
    load_data()