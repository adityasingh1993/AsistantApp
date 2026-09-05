"""
seed_demo.py
Seeds the AppAI Hub with BillingPro app registration and knowledge base.

Run AFTER the Hub is started:
    python seed_demo.py
"""
import httpx
import json
import sys

HUB = "http://localhost:7788"

def post(path, body):
    r = httpx.post(f"{HUB}{path}", json=body, timeout=15)
    r.raise_for_status()
    return r.json()

def main():
    print("Seeding BillingPro into AppAI Hub...")

    # 1. Register the app
    try:
        app = post("/api/apps/register", {
            "name": "BillingPro",
            "description": "Invoice management system for tracking, creating and exporting invoices.",
            "source_path": "",
            "docs_path": ""
        })
        app_id = app["id"]
        print(f"  App registered: id={app_id}")
    except Exception as e:
        print(f"  [WARN] App registration failed (may already exist): {e}")
        # Try to get existing
        r = httpx.get(f"{HUB}/api/apps", timeout=10)
        apps = r.json()
        match = [a for a in apps if a["name"] == "BillingPro"]
        if not match:
            print("  [ERROR] Could not find or create BillingPro app. Is the Hub running?")
            sys.exit(1)
        app_id = match[0]["id"]
        print(f"  Using existing app: id={app_id}")

    # 2. Seed knowledge base documents
    docs = [
        {
            "content": "BillingPro is an invoice management system. The main Invoice Dashboard shows all invoices with their status (Paid, Pending, Overdue, Draft), client name, issue date, due date, and amount. Users can filter, search, and sort invoices from this screen.",
            "content_type": "ui_description",
            "source": "app_overview"
        },
        {
            "content": "To create a new invoice: Click the 'New Invoice' button (top-right, blue button) or click 'Create Invoice' in the left sidebar. A slide panel will open on the right side. Fill in the Client Name (required), select Issue Date and Due Date, enter the Amount, optionally attach a document by dropping a file in the drop zone, then click 'Save Invoice'.",
            "content_type": "workflow",
            "source": "create_invoice_workflow"
        },
        {
            "content": "To export an invoice report: Click the 'Export Report' button (top-right, beside New Invoice) or click 'Export Report' in the Reports section of the left sidebar. The Export Report dialog will open. Select the Export Format (PDF, CSV, or Excel/XLSX), set the Start Date and End Date for the date range, optionally filter by status (All, Paid, Pending, Overdue), then click 'Export Report'. Both Start Date and End Date must be filled in before exporting.",
            "content_type": "workflow",
            "source": "export_report_workflow"
        },
        {
            "content": "Invoice statuses in BillingPro: Paid (green badge) - invoice has been settled. Pending (yellow badge) - invoice sent, awaiting payment. Overdue (red badge) - payment is past due date. Draft (gray badge) - invoice created but not yet sent to client.",
            "content_type": "ui_description",
            "source": "status_descriptions"
        },
        {
            "content": "Error: 'Please select both Start Date and End Date before exporting.' This error appears in the Export Report dialog when you click Export without filling in the date range. Fix: Set the Start Date and End Date fields in the Export Report dialog before clicking Export.",
            "content_type": "error_message",
            "source": "export_error"
        },
        {
            "content": "To attach a document to an invoice: When creating a new invoice in the slide panel, find the 'Attach Document' section. You can drag and drop a PDF or image file onto the drop zone, or click the drop zone to browse your files. Supported formats: PDF, PNG, JPG up to 10MB.",
            "content_type": "workflow",
            "source": "attach_document_workflow"
        },
        {
            "content": "To send a payment reminder for an overdue invoice: Find the overdue invoice (shown with a red 'Overdue' badge) in the invoice table. Click the red 'Send Reminder' button in the Actions column. A reminder email will be sent to the client.",
            "content_type": "workflow",
            "source": "send_reminder_workflow"
        },
        {
            "content": "The left sidebar navigation sections: Invoices section contains: All Invoices (shows complete invoice list), Create Invoice (opens new invoice panel), Pending (shows only pending invoices - currently 3), Overdue (shows only overdue invoices - currently 1). Reports section contains: Export Report (opens export dialog), Analytics. Finance section contains: Import Data, Payments.",
            "content_type": "ui_description",
            "source": "sidebar_navigation"
        },
        {
            "content": "The invoice dashboard shows four summary cards at the top: Total Revenue, Pending amount, Overdue amount, and Paid This Month. Below the stats cards is the invoice table with a search bar and filter button. The search bar allows filtering invoices by any text.",
            "content_type": "ui_description",
            "source": "dashboard_layout"
        },
    ]

    for doc in docs:
        post(f"/api/kb/{app_id}/add_document", doc)
        print(f"  KB doc added: [{doc['content_type']}] {doc['source']}")

    print()
    print("Done! BillingPro is ready in AppAI Hub.")
    print()
    print("Open the demo app:")
    print("  file:///f:/Projects/AppAI/demo/index.html")
    print()
    print("The WebSocket URL the demo uses:")
    print(f"  ws://localhost:7788/ws/billingpro/ravi-kumar-001")

if __name__ == "__main__":
    main()
