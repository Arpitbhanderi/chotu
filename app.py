from chotu_assistant import get_assistant
from invoice_printer import (
    generate_invoice_pdf,
    print_invoice_directly,
    get_available_printers
)
import os
from datetime import datetime as dt, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    send_file, jsonify, session, make_response
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import io
import csv
import tempfile
import shutil

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)  # Force reload even if already loaded

# Import our printing module

app = Flask(__name__)
app.secret_key = "zankar-vision-2025"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

INVOICE_DIR = os.path.join(os.path.dirname(__file__), "invoices")
os.makedirs(INVOICE_DIR, exist_ok=True)

# ---------- MODELS ----------


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), unique=True)
    address = db.Column(db.Text)
    gstin = db.Column(db.String(20))
    outstanding_balance = db.Column(db.Float, default=0.0)
    credit_limit = db.Column(db.Float, default=0.0)
    last_payment_date = db.Column(db.String(20))
    expected_next_payment_date = db.Column(db.String(20))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'gstin': self.gstin,
            'outstanding_balance': self.outstanding_balance,
            'credit_limit': self.credit_limit,
            'last_payment_date': self.last_payment_date,
            'expected_next_payment_date': self.expected_next_payment_date
        }


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    company = db.Column(db.String(120))
    price = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'barcode': self.barcode,
            'name': self.name,
            'description': self.description,
            'company': self.company,
            'price': self.price,
            'tax': self.tax
        }


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50), unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"))
    invoice_date = db.Column(db.String(20))
    due_date = db.Column(db.String(20))
    terms = db.Column(db.String(50))
    salesperson = db.Column(db.String(120))
    notes = db.Column(db.Text)
    discount_type = db.Column(db.String(120))
    discount_amount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float)
    payment_status = db.Column(db.String(50),
                               default='unpaid')  # 'unpaid', 'partial', 'paid'
    total_paid = db.Column(db.Float, default=0.0)
    customer = db.relationship("Customer", backref="invoices")

    @property
    def remaining_balance(self):
        """Calculate remaining balance (total - total_paid)"""
        return self.total - (self.total_paid or 0)

    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'invoice_date': self.invoice_date,
            'due_date': self.due_date,
            'terms': self.terms,
            'salesperson': self.salesperson,
            'notes': self.notes,
            'discount_type': self.discount_type,
            'discount_amount': self.discount_amount,
            'total': self.total,
            'payment_status': self.payment_status,
            'total_paid': self.total_paid,
            'remaining_balance': self.total - self.total_paid
        }


class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    qty = db.Column(db.Integer)
    price = db.Column(db.Float)
    discount_amount = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    line_total = db.Column(db.Float)
    description = db.Column(db.Text)  # Add description field
    product = db.relationship("Product")
    invoice = db.relationship("Invoice", backref="invoice_items")

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'qty': self.qty,
            'price': self.price,
            'discount_amount': self.discount_amount,
            'tax': self.tax,
            'line_total': self.line_total,
            'description': self.description
        }


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"))
    amount = db.Column(db.Float)
    payment_date = db.Column(db.String(20))
    # 'cash', 'card', 'bank_transfer', 'cheque'
    payment_method = db.Column(db.String(50))
    reference_number = db.Column(db.String(100))
    notes = db.Column(db.Text)
    received_by = db.Column(db.String(120))
    invoice = db.relationship("Invoice", backref="payments")

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'amount': self.amount,
            'payment_date': self.payment_date,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'received_by': self.received_by
        }


with app.app_context():
    db.create_all()

# ---------- ADMIN / SETTINGS MODELS ----------


class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


with app.app_context():
    db.create_all()
    # Ensure a default admin exists
    if not AdminUser.query.first():
        default_admin = AdminUser(username="admin")
        default_admin.set_password("admin")
        db.session.add(default_admin)
        db.session.commit()


class AppSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False)
    value = db.Column(db.Text)

    @staticmethod
    def get(key: str, default=None):
        rec = AppSetting.query.filter_by(key=key).first()
        return rec.value if rec else default

    @staticmethod
    def set(key: str, value: str):
        rec = AppSetting.query.filter_by(key=key).first()
        if rec:
            rec.value = value
        else:
            rec = AppSetting(key=key, value=value)
            db.session.add(rec)
        db.session.commit()


with app.app_context():
    db.create_all()
    # Set sensible defaults if not present
    if AppSetting.get('AUTO_PRINT_AFTER_SAVE') is None:
        AppSetting.set('AUTO_PRINT_AFTER_SAVE', 'false')
    if AppSetting.get('DEFAULT_PRINTER') is None:
        AppSetting.set('DEFAULT_PRINTER', '')
    if AppSetting.get('COMPANY_NAME') is None:
        AppSetting.set('COMPANY_NAME', 'Zankar Vision')
    if AppSetting.get('COMPANY_PHONE') is None:
        AppSetting.set('COMPANY_PHONE', '+91 98792 89565')
    if AppSetting.get('COMPANY_ADDRESS') is None:
        AppSetting.set('COMPANY_ADDRESS', 'Vadhai, Dang, Gujarat')
    if AppSetting.get('COMPANY_GSTIN') is None:
        AppSetting.set('COMPANY_GSTIN', '24AIRPB9566H1ZV')

# Initialize Chotu Assistant with database models

# Create assistant and initialize with models
chotu_assistant = get_assistant()
chotu_assistant.initialize_models(Customer, Product, Invoice, InvoiceItem, db)


def generate_next_invoice_number():
    """Generate the next invoice number safely by finding the maximum existing number"""
    try:
        # Get all existing invoice numbers
        all_nums = [inv.number for inv in Invoice.query.all() if inv.number and inv.number.startswith('INV-')]
        if all_nums:
            # Extract numbers and find the maximum
            values = []
            for n in all_nums:
                # Extract the numeric part after 'INV-'
                if n.startswith('INV-'):
                    try:
                        num_part = int(n[4:])  # Remove 'INV-' prefix
                        values.append(num_part)
                    except ValueError:
                        continue
            next_num = (max(values) + 1) if values else 1
        else:
            next_num = 1
    except Exception:
        # Fallback to count-based approach if there's an error
        next_num = Invoice.query.count() + 1
    
    return f"INV-{str(next_num).zfill(6)}"


# ---------- ROUTES ----------


@app.route("/")
def dashboard():
    """Main dashboard with statistics"""
    # Basic counts
    cust_count = Customer.query.count()
    prod_count = Product.query.count()
    inv_count = Invoice.query.count()

    # Invoice statistics
    total_revenue = db.session.query(db.func.sum(Invoice.total)).scalar() or 0
    average_invoice = (total_revenue / inv_count) if inv_count > 0 else 0

    # Unique customers who have invoices
    unique_customers = db.session.query(Invoice.customer_id).distinct().count()

    # Khata book statistics
    total_outstanding = db.session.query(db.func.sum(Customer.outstanding_balance)).scalar() or 0

    return render_template("dashboard.html",
                           cust_count=cust_count,
                           prod_count=prod_count,
                           inv_count=inv_count,
                           total_revenue=total_revenue,
                           average_invoice=average_invoice,
                           unique_customers=unique_customers,
                           total_outstanding=total_outstanding)

# ---------- CUSTOMER ROUTES ----------


@app.route("/customers")
def customers():
    """List all customers with search and history functionality"""
    # Get search parameters
    search_query = request.args.get('search', '').strip()
    customer_id = request.args.get('customer_id', type=int)

    # Search customers if query provided
    if search_query:
        customers = Customer.query.filter(
            db.or_(
                Customer.name.ilike(f"%{search_query}%"),
                Customer.email.ilike(f"%{search_query}%"),
                Customer.phone.ilike(f"%{search_query}%")
            )
        ).all()

        # Add purchase statistics for each customer
        customers_with_stats = []
        for customer in customers:
            invoices = Invoice.query.filter_by(customer_id=customer.id).all()
            total_spent = sum(invoice.total or 0 for invoice in invoices)
            invoice_count = len(invoices)

            customers_with_stats.append({
                'customer': customer,
                'total_spent': total_spent,
                'invoice_count': invoice_count
            })
    else:
        # Show all customers with stats
        customers = Customer.query.all()
        customers_with_stats = []
        for customer in customers:
            invoices = Invoice.query.filter_by(customer_id=customer.id).all()
            total_spent = sum(invoice.total or 0 for invoice in invoices)
            invoice_count = len(invoices)

            customers_with_stats.append({
                'customer': customer,
                'total_spent': total_spent,
                'invoice_count': invoice_count
            })

    # Get selected customer's history if customer_id provided
    selected_customer = None
    customer_invoices = []
    customer_stats = {}

    if customer_id:
        selected_customer = Customer.query.get_or_404(customer_id)
        customer_invoices = (
            Invoice.query.filter_by(customer_id=customer_id)
            .order_by(Invoice.id.desc()).all()
        )

        if customer_invoices:
            total_spent = sum(
                invoice.total or 0
                for invoice in customer_invoices
            )
            # Convert string dates to datetime for comparison
            valid_dates = [
                dt.strptime(
                    invoice.invoice_date, '%Y-%m-%d'
                )
                for invoice in customer_invoices
                if invoice.invoice_date
            ]

            if valid_dates:
                first_purchase = min(valid_dates)
                last_purchase = max(valid_dates)
            else:
                first_purchase = None
                last_purchase = None

            avg_order_value = total_spent / len(customer_invoices)

            customer_stats = {
                'total_spent': total_spent,
                'invoice_count': len(customer_invoices),
                'first_purchase': first_purchase,
                'last_purchase': last_purchase,
                'avg_order_value': avg_order_value
            }
        else:
            customer_stats = {
                'total_spent': 0,
                'invoice_count': 0,
                'first_purchase': None,
                'last_purchase': None,
                'avg_order_value': 0
            }

    return render_template("customers.html",
                           customers_with_stats=customers_with_stats,
                           selected_customer=selected_customer,
                           customer_invoices=customer_invoices,
                           customer_stats=customer_stats,
                           search_query=search_query)


def search_customers():
    """Search customers by name or phone"""
    q = request.args.get("q", "").strip()
    if q:
        customers = Customer.query.filter(
            (Customer.name.ilike(f"%{q}%")) | (Customer.phone.ilike(f"%{q}%"))
        ).all()
    else:
        customers = Customer.query.limit(20).all()

    results = []
    for c in customers:
        results.append({
            "id": c.id,
            "text": f"{c.name} ({c.phone or ''})",
            "phone": c.phone,
            "address": c.address
        })
    return jsonify(results)


def add_customer():
    """Add new customer"""
    # Check for existing phone/email
    # Normalize empty strings to None to avoid unique constraint conflicts on
    # ''
    phone = request.form.get("phone") or None
    email = request.form.get("email") or None

    if phone:
        existing = Customer.query.filter_by(phone=phone).first()
        if existing:
            error_msg = "Customer with this phone number already exists."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "error": error_msg}), 400
            flash(error_msg, "danger")
            return redirect(url_for("customers"))

    if email:
        existing = Customer.query.filter_by(email=email).first()
        if existing:
            error_msg = "Customer with this email already exists."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "error": error_msg}), 400
            flash(error_msg, "danger")
            return redirect(url_for("customers"))

    try:
        c = Customer(
            name=request.form["name"],
            phone=phone,
            email=email,
            address=request.form.get("address") or None,
            gstin=request.form.get("gstin") or None,
        )
        db.session.add(c)
        db.session.commit()

        # Check if it's an AJAX request (from new invoice modal)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "success": True,
                "id": c.id,
                "text": f"{c.name} ({c.phone or ''})",
                "phone": c.phone,
                "address": c.address,
                "message": "Customer added successfully!"
            })

        flash("Customer added successfully!", "success")
        return redirect(url_for("customers"))
    except IntegrityError:
        db.session.rollback()
        error_msg = "An error occurred while adding the customer."

        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": error_msg}), 400

        flash(error_msg, "danger")
        return redirect(url_for("customers"))


def edit_customer(customer_id):
    """Edit customer details"""
    customer = Customer.query.get_or_404(customer_id)

    if request.method == "POST":
        try:
            customer.name = request.form["name"]
            customer.phone = request.form.get("phone") or None
            customer.email = request.form.get("email") or None
            customer.address = request.form.get("address") or None
            customer.gstin = request.form.get("gstin") or None

            db.session.commit()
            flash("Customer updated successfully!", "success")
            return redirect(url_for("customers"))
        except IntegrityError:
            db.session.rollback()
            flash("Customer with this phone/email already exists.", "danger")
    # This route is POST-only (modal-based edit). No separate edit page is
    # rendered.
    return redirect(url_for("customers"))


def delete_customer(customer_id):
    """Delete customer"""
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted successfully!", "success")
    return redirect(url_for("customers"))


def export_customers():
    """Export all customers to Excel"""
    import io
    import csv
    from flask import make_response

    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Name', 'Phone', 'Email', 'Address',
                    'GSTIN', 'Total Spent', 'Total Orders'])

    # Write customer data
    customers = Customer.query.all()
    for customer in customers:
        invoices = Invoice.query.filter_by(customer_id=customer.id).all()
        total_spent = sum(invoice.total or 0 for invoice in invoices)
        invoice_count = len(invoices)

        writer.writerow([
            customer.name,
            customer.phone or '',
            customer.email or '',
            customer.address or '',
            customer.gstin or '',
            total_spent,
            invoice_count
        ])

    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    filename = (
        f'customers_export_{dt.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'

    return response

# ---------- PRODUCT ROUTES ----------


@app.route("/products")
def show_products():
    """List all products"""
    products = Product.query.all()
    return render_template("products.html", products=products)


def search_products():
    """Search products by name or barcode"""
    q = request.args.get("q", "").strip()
    if q:
        products = Product.query.filter(
            (Product.name.ilike(f"%{q}%")) | (Product.barcode.ilike(f"%{q}%"))
        ).all()
    else:
        products = Product.query.limit(20).all()

    results = []
    for p in products:
        results.append({
            "id": p.id,
            "description": p.description,
            "text": p.name,
            "price": p.price,
            "barcode": p.barcode
        })
    return jsonify(results)


def add_product():
    """Add new product"""
    # Check for existing barcode
    barcode = request.form.get("barcode") or None

    if barcode:
        existing = Product.query.filter_by(barcode=barcode).first()
        if existing:
            error_msg = "Product with this barcode already exists."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "error": error_msg}), 400
            flash(error_msg, "danger")
            return redirect(url_for("show_products"))

    try:
        p = Product(
            barcode=barcode,
            name=request.form["name"],
            description=request.form.get("description") or None,
            company=request.form.get("company") or None,
            price=float(request.form["price"]),
            tax=float(request.form.get("tax") or 0),
        )
        db.session.add(p)
        db.session.commit()

        # Check if it's an AJAX request (from new invoice modal)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "success": True,
                "id": p.id,
                "text": p.name,
                "price": p.price,
                "description": p.description,
                "barcode": p.barcode,
                "message": "Product added successfully!"
            })

        flash("Product added successfully!", "success")
        return redirect(url_for("show_products"))
    except IntegrityError:
        db.session.rollback()
        error_msg = "An error occurred while adding the product."

        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": error_msg}), 400

        flash(error_msg, "danger")
        return redirect(url_for("show_products"))
    except ValueError:
        error_msg = "Invalid price or tax value."

        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": error_msg}), 400

        flash(error_msg, "danger")
        return redirect(url_for("show_products"))


def edit_product():
    """Edit product details via modal"""
    try:
        product_id = request.form["product_id"]
        product = Product.query.get_or_404(product_id)

        product.barcode = request.form.get("barcode") or None
        product.name = request.form["name"]
        product.description = request.form.get("description") or None
        product.company = request.form.get("company") or None
        product.price = float(request.form["price"])
        product.tax = float(request.form.get("tax") or 0)

        db.session.commit()
        flash("Product updated successfully!", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Product with this barcode already exists.", "danger")
    except ValueError:
        flash("Invalid price or tax value.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating product: {str(e)}", "danger")

    return redirect(url_for("show_products"))


def delete_product(product_id):
    """Delete product"""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully!", "success")
    return redirect(url_for("show_products"))

# ---------- INVOICE ROUTES ----------


def invoices():
    """List all invoices"""
    invoices = Invoice.query.order_by(Invoice.id.desc()).all()
    today_str = dt.now().strftime("%Y-%m-%d")
    return render_template(
        "invoices.html",
        invoices=invoices,
        today_str=today_str)


@app.route("/new-invoice")
def new_invoice():
    """Create new invoice form"""
    today = dt.now().strftime("%Y-%m-%d")

    # Get pre-selected customer if provided
    customer_id = request.args.get('customer_id', type=int)
    selected_customer = None
    if customer_id:
        selected_customer = Customer.query.get(customer_id)

    return render_template(
        "new_invoice.html",
        today=today,
        selected_customer=selected_customer)


def save_invoice():
    """Save new invoice"""
    try:
        cust_id = request.form["customer_id"]
        inv_no = generate_next_invoice_number()

        # Create invoice
        inv = Invoice(
            number=inv_no,
            customer_id=cust_id,
            invoice_date=request.form.get("invoice_date"),
            due_date=request.form.get("due_date"),
            terms=request.form.get("terms"),
            salesperson=request.form.get("salesperson"),
            notes=request.form.get("notes"),
            discount_type=request.form.get("discount_type"),
            discount_amount=float(request.form.get("invoice_discount") or 0),
            total=0
        )
        db.session.add(inv)
        db.session.commit()

        # Add invoice items
        subtotal = 0
        for pid, q, d, t, r, desc in zip(
            request.form.getlist("product_id[]"),
            request.form.getlist("qty[]"),
            request.form.getlist("discount[]"),
            request.form.getlist("tax[]"),
            request.form.getlist("rate[]"),
            request.form.getlist("description[]")
        ):
            if not pid:
                continue

            product = Product.query.get(pid)
            qty = int(q)
            price = float(r) if r else product.price
            discount_amt = float(d or 0)
            tax = float(t or 0)
            line_total = (qty * price - discount_amt) * (1 + tax / 100)

            item = InvoiceItem(
                invoice_id=inv.id,
                product_id=pid,
                qty=qty,
                price=price,
                discount_amount=discount_amt,
                tax=tax,
                line_total=line_total,
                description=desc or (product.description if product else '')
            )
            db.session.add(item)
            subtotal += line_total

        # Update invoice total
        inv.total = subtotal - inv.discount_amount
        db.session.commit()

        # Handle initial payment if provided
        initial_payment_amount = float(request.form.get("initial_payment_amount") or 0)
        if initial_payment_amount > 0:
            payment_method = request.form.get("initial_payment_method")
            payment_date = request.form.get("initial_payment_date")
            payment_notes = request.form.get("initial_payment_notes")

            # Create payment record
            payment = Payment(
                invoice_id=inv.id,
                amount=initial_payment_amount,
                payment_method=payment_method,
                payment_date=payment_date,
                notes=payment_notes or f"Initial payment for invoice {inv.number}"
            )
            db.session.add(payment)

            # Update invoice payment status
            inv.total_paid = initial_payment_amount
            if inv.total_paid >= inv.total:
                inv.payment_status = 'paid'
            elif inv.total_paid > 0:
                inv.payment_status = 'partial'
            else:
                inv.payment_status = 'unpaid'

            # Update customer's outstanding balance
            customer = Customer.query.get(cust_id)
            if customer:
                customer.outstanding_balance = (customer.outstanding_balance or 0) + inv.total - initial_payment_amount
                customer.last_payment_date = payment_date
                
                # Update next expected payment date if provided
                next_expected_date = request.form.get("next_expected_payment_date")
                if next_expected_date:
                    customer.expected_next_payment_date = next_expected_date
                
            db.session.commit()

        # Generate PDF
        pdf_path = os.path.join(INVOICE_DIR, f"{inv.number}.pdf")
        if generate_invoice_pdf(inv, pdf_path):
            flash("Invoice created successfully!", "success")
            # Auto print based on settings
            try:
                auto_print = (
                    (AppSetting.get('AUTO_PRINT_AFTER_SAVE', 'false') or 'false')
                    .lower() == 'true'
                )
                default_printer = (
                    AppSetting.get('DEFAULT_PRINTER', '') or None
                )
                if auto_print:
                    result = print_invoice_directly(
                        inv.number, default_printer)
                    if not result.get('success'):
                        flash(
                            f"Auto-print failed: {result.get('message')}", "warning")
            except Exception as e:
                flash(f"Auto-print error: {e}", "warning")
        else:
            flash("Invoice created but PDF generation failed.", "warning")

        return redirect(url_for("invoices"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error creating invoice: {str(e)}", "danger")
        return redirect(url_for("new_invoice"))


def invoice_pdf(number):
    """Serve invoice PDF"""
    path = os.path.join(INVOICE_DIR, f"{number}.pdf")
    if os.path.exists(path):
        return send_file(
            path,
            download_name=f"{number}.pdf",
            mimetype="application/pdf")
    return "PDF not found", 404


@app.route("/invoice/<int:invoice_id>")
def invoice_details(invoice_id):
    """Show invoice details"""
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template("invoice_details.html", invoice=invoice)


def delete_invoice(number):
    """Delete invoice"""
    inv = Invoice.query.filter_by(number=number).first_or_404()
    InvoiceItem.query.filter_by(invoice_id=inv.id).delete()
    db.session.delete(inv)
    db.session.commit()

    # Remove PDF file
    pdf_path = os.path.join(INVOICE_DIR, f"{number}.pdf")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    flash("Invoice deleted successfully!", "success")
    return redirect(url_for("invoices"))


def duplicate_invoice(number):
    """Create a duplicate of an existing invoice"""
    try:
        original = Invoice.query.filter_by(number=number).first_or_404()

        # Create new invoice number
        new_number = generate_next_invoice_number()
        today = dt.now().strftime("%Y-%m-%d")

        # Create duplicate invoice
        new_invoice = Invoice(
            number=new_number,
            customer_id=original.customer_id,
            invoice_date=today,
            due_date=original.due_date,
            terms=original.terms,
            salesperson=original.salesperson,
            notes=original.notes,
            discount_type=original.discount_type,
            discount_amount=original.discount_amount,
            total=original.total
        )

        db.session.add(new_invoice)
        db.session.flush()

        # Duplicate all invoice items
        for item in original.invoice_items:
            new_item = InvoiceItem(
                invoice_id=new_invoice.id,
                product_id=item.product_id,
                qty=item.qty,
                price=item.price,
                discount_amount=item.discount_amount,
                tax=item.tax,
                line_total=item.line_total
            )
            db.session.add(new_item)

        db.session.commit()

        # Generate PDF for new invoice
        pdf_path = os.path.join(INVOICE_DIR, f"{new_number}.pdf")
        generate_invoice_pdf(new_invoice, pdf_path)

        flash(f"Invoice duplicated as {new_number}!", "success")
        return redirect(url_for("invoices"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error duplicating invoice: {str(e)}", "danger")
        return redirect(url_for("invoices"))


def search_invoices():
    """Search invoices by number or customer name"""
    q = request.args.get("q", "").strip()
    if q:
        invoices = Invoice.query.join(Customer).filter(
            (Invoice.number.ilike(f"%{q}%")) |
            (Customer.name.ilike(f"%{q}%"))
        ).order_by(Invoice.id.desc()).limit(20).all()
    else:
        invoices = Invoice.query.order_by(Invoice.id.desc()).limit(20).all()

    results = []
    for inv in invoices:
        customer_name = inv.customer.name if inv.customer else "Unknown"
        results.append({
            "id": inv.id,
            "number": inv.number,
            "customer_name": customer_name,
            "date": inv.invoice_date,
            "total": inv.total,
            "text": (
                f"{inv.number} - "
                f"{inv.customer.name if inv.customer else 'Unknown'} - "
                f"₹{inv.total:.2f}"
            )
        })
    return jsonify(results)


@app.route("/invoice-history")
def invoice_history():
    """Advanced invoice history with filtering and search"""
    # Get filter parameters
    search_query = request.args.get("search", "").strip()
    customer_filter = request.args.get("customer", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    min_amount = request.args.get("min_amount", "").strip()
    max_amount = request.args.get("max_amount", "").strip()
    sort_by = request.args.get("sort", "date_desc")

    # Start with base query
    query = Invoice.query.join(Customer, isouter=True)

    # Apply filters
    if search_query:
        query = query.filter(
            (Invoice.number.ilike(f"%{search_query}%")) |
            (Customer.name.ilike(f"%{search_query}%")) |
            (Invoice.notes.ilike(f"%{search_query}%"))
        )

    if customer_filter:
        query = query.filter(Customer.name.ilike(f"%{customer_filter}%"))

    if date_from:
        query = query.filter(Invoice.invoice_date >= date_from)

    if date_to:
        query = query.filter(Invoice.invoice_date <= date_to)

    if min_amount:
        try:
            query = query.filter(Invoice.total >= float(min_amount))
        except ValueError:
            pass

    if max_amount:
        try:
            query = query.filter(Invoice.total <= float(max_amount))
        except ValueError:
            pass

    # Apply sorting
    if sort_by == "date_asc":
        query = query.order_by(Invoice.invoice_date.asc(), Invoice.id.asc())
    elif sort_by == "date_desc":
        query = query.order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
    elif sort_by == "amount_asc":
        query = query.order_by(Invoice.total.asc())
    elif sort_by == "amount_desc":
        query = query.order_by(Invoice.total.desc())
    elif sort_by == "customer":
        query = query.order_by(
            Customer.name.asc()
        )
    elif sort_by == "number":
        query = query.order_by(Invoice.number.asc())
    else:
        query = query.order_by(Invoice.id.desc())

    invoices = query.all()

    # Get all customers for filter dropdown
    customers = Customer.query.order_by(Customer.name).all()

    # Calculate statistics
    total_revenue = sum(inv.total for inv in invoices) if invoices else 0
    total_discounts = sum(
        inv.discount_amount for inv in invoices if inv.discount_amount) if invoices else 0
    avg_invoice = total_revenue / len(invoices) if invoices else 0

    # Get today's date for overdue calculation
    today_str = dt.now().strftime('%Y-%m-%d')

    return render_template("invoice_history.html",
                           invoices=invoices,
                           customers=customers,
                           search_query=search_query,
                           customer_filter=customer_filter,
                           date_from=date_from,
                           date_to=date_to,
                           min_amount=min_amount,
                           max_amount=max_amount,
                           sort_by=sort_by,
                           total_revenue=total_revenue,
                           total_discounts=total_discounts,
                           avg_invoice=avg_invoice,
                           today_str=today_str)

# ---------- PRINTING ROUTES ----------


def print_invoice_route(invoice_number):
    """Print invoice"""
    # First, ensure PDF exists
    invoice = Invoice.query.filter_by(number=invoice_number).first()
    if not invoice:
        flash(f"Invoice {invoice_number} not found", "danger")
        return redirect(url_for("invoices"))

    # Generate PDF if it doesn't exist
    pdf_path = os.path.join("invoices", f"{invoice_number}.pdf")
    if not os.path.exists(pdf_path):
        try:
            if not generate_invoice_pdf(invoice, pdf_path):
                flash(
                    f"Failed to generate PDF for invoice {invoice_number}",
                    "danger")
                return redirect(url_for("invoices"))
        except Exception as e:
            flash(f"Error generating PDF: {str(e)}", "danger")
            return redirect(url_for("invoices"))

    # Now proceed with printing
    printer_name = request.form.get(
        'printer_name') if request.method == 'POST' else None
    if not printer_name:
        # Fallback to default printer from settings
        try:
            printer_name = AppSetting.get('DEFAULT_PRINTER', '') or None
        except Exception:
            printer_name = None

    result = print_invoice_directly(invoice_number, printer_name)

    if result["success"]:
        flash(result["message"], "success")
    else:
        flash(result["message"], "danger")

    return redirect(url_for("invoices"))


def api_printers():
    """API endpoint to get available printers"""
    result = get_available_printers()
    return jsonify(result)

# ---------- REPORTS ROUTES ----------


# ---------- KHATA BOOK ROUTES ----------

@app.route("/khata-book")
def khata_book():
    """Khata Book - Customer Account Ledger"""
    try:
        # Get search and filter parameters
        search = request.args.get('search', '').strip()
        balance_filter = request.args.get('balance_filter', 'all')
        sort_by = request.args.get('sort_by', 'balance_desc')
        selected_month = request.args.get('month') or dt.now().strftime('%Y-%m')

        # Base query for customers with outstanding balances
        query = Customer.query.filter(Customer.outstanding_balance > 0)

        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    Customer.name.ilike(f'%{search}%'),
                    Customer.phone.ilike(f'%{search}%')
                )
            )

        # Apply balance filter
        if balance_filter == 'high':
            query = query.filter(Customer.outstanding_balance >= 10000)
        elif balance_filter == 'medium':
            query = query.filter(
                db.and_(
                    Customer.outstanding_balance >= 1000,
                    Customer.outstanding_balance < 10000
                )
            )
        elif balance_filter == 'low':
            query = query.filter(Customer.outstanding_balance < 1000)

        # Apply sorting
        if sort_by == 'balance_desc':
            query = query.order_by(Customer.outstanding_balance.desc())
        elif sort_by == 'balance_asc':
            query = query.order_by(Customer.outstanding_balance.asc())
        elif sort_by == 'name':
            query = query.order_by(Customer.name.asc())
        elif sort_by == 'last_payment':
            query = query.order_by(Customer.last_payment_date.desc().nulls_last())

        customers = query.all()

        khata_data = []
        for customer in customers:
            # Use customer's expected next payment date
            next_payment = customer.expected_next_payment_date

            khata_data.append({
                'customer': customer,
                'outstanding_balance': customer.outstanding_balance,
                'next_payment_date': next_payment
            })

        # Calculate money expected this month
        current_month = selected_month  # Use selected month instead of current month
        money_expected_this_month = 0.0
        
        # Include outstanding balances for customers with expected payment dates this month
        customers_with_expected_payments = Customer.query.filter(
            Customer.expected_next_payment_date.like(f'{current_month}%')
        ).all()
        
        for customer in customers_with_expected_payments:
            money_expected_this_month += customer.outstanding_balance

        # Generate month options for the filter (current month and next 11 months)
        month_options = []
        selected_month_display = ""
        current_date = dt.now().replace(day=1)  # Start from current month
        
        for i in range(12):
            # Calculate the month by adding i months to current date
            year = current_date.year
            month = current_date.month + i
            
            # Handle year rollover
            if month > 12:
                year += (month - 1) // 12
                month = ((month - 1) % 12) + 1
            
            month_date = dt(year, month, 1)
            month_value = month_date.strftime('%Y-%m')
            month_display = month_date.strftime('%B')  # Only month name for dropdown
            month_options.append({'value': month_value, 'display': month_display})
            if month_value == selected_month:
                selected_month_display = month_date.strftime('%B')  # Only month name for display

        return render_template("khata_book.html",
                             khata_data=khata_data,
                             search=search,
                             balance_filter=balance_filter,
                             sort_by=sort_by,
                             selected_month=selected_month,
                             selected_month_display=selected_month_display,
                             money_expected_this_month=money_expected_this_month,
                             month_options=month_options)
    except Exception as e:
        flash(f"Error loading khata book: {str(e)}", "danger")
        return redirect(url_for("dashboard"))


@app.route("/customer/<int:customer_id>/khata")
def customer_khata(customer_id):
    """Detailed khata book for a specific customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)

        # Get all invoices for this customer
        invoices = Invoice.query.filter_by(customer_id=customer_id).all()

        # Get all payments for this customer
        payments = db.session.query(Payment).join(Invoice).filter(
            Invoice.customer_id == customer_id
        ).order_by(Payment.payment_date.desc()).all()

        # Calculate total outstanding
        total_outstanding = sum(
            inv.total - inv.total_paid for inv in invoices
            if inv.total > inv.total_paid
        )

        # Update customer's outstanding balance
        customer.outstanding_balance = total_outstanding
        db.session.commit()

        return render_template(
            "customer_khata.html",
            customer=customer,
            invoices=invoices,
            payments=payments,
            total_outstanding=total_outstanding
        )
    except Exception as e:
        flash(f"Error loading customer khata: {str(e)}", "danger")
        return redirect(url_for("khata_book"))


@app.route("/customer/<int:customer_id>/add-payment", methods=["GET", "POST"])
def add_customer_payment(customer_id):
    """Add payment for a customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)

        if request.method == "POST":
            invoice_id = request.form.get("invoice_id")
            amount = float(request.form.get("amount", 0))
            payment_date = request.form.get("payment_date")
            payment_method = request.form.get("payment_method")
            reference_number = request.form.get("reference_number")
            notes = request.form.get("notes")
            expected_next_payment = request.form.get("expected_next_payment")

            if not amount or not payment_date:
                flash("Please fill all required fields", "danger")
                return redirect(request.url)

            remaining_amount = amount

            # If specific invoice selected, apply payment to that invoice
            if invoice_id:
                # Create payment
                payment = Payment(
                    invoice_id=invoice_id,
                    amount=amount,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    reference_number=reference_number,
                    notes=notes,
                    received_by="Admin"
                )
                db.session.add(payment)

                # Update invoice total_paid
                invoice = Invoice.query.get(invoice_id)
                if invoice:
                    payment_amount = min(remaining_amount, invoice.total - invoice.total_paid)
                    invoice.total_paid += payment_amount
                    if invoice.total_paid >= invoice.total:
                        invoice.payment_status = 'paid'
                    elif invoice.total_paid > 0:
                        invoice.payment_status = 'partial'
                    remaining_amount -= payment_amount
            else:
                # No specific invoice selected - apply to oldest unpaid invoices
                unpaid_invoices = Invoice.query.filter_by(
                    customer_id=customer_id
                ).filter(Invoice.total > Invoice.total_paid).order_by(Invoice.invoice_date).all()

                for invoice in unpaid_invoices:
                    if remaining_amount <= 0:
                        break

                    payment_amount = min(remaining_amount, invoice.total - invoice.total_paid)

                    # Create payment for this invoice
                    payment = Payment(
                        invoice_id=invoice.id,
                        amount=payment_amount,
                        payment_date=payment_date,
                        payment_method=payment_method,
                        reference_number=reference_number,
                        notes=notes,
                        received_by="Admin"
                    )
                    db.session.add(payment)

                    # Update invoice
                    invoice.total_paid += payment_amount
                    if invoice.total_paid >= invoice.total:
                        invoice.payment_status = 'paid'
                    elif invoice.total_paid > 0:
                        invoice.payment_status = 'partial'

                    remaining_amount -= payment_amount

            # Update customer outstanding balance and last payment date
            customer.outstanding_balance = max(0, customer.outstanding_balance - amount)
            customer.last_payment_date = payment_date
            if expected_next_payment:
                customer.expected_next_payment_date = expected_next_payment

            db.session.commit()
            flash("Payment added successfully!", "success")
            
            # Get the payment details for challan generation
            if invoice_id:
                # Single invoice payment - get the invoice that was paid
                paid_invoice = Invoice.query.get(invoice_id)
                payment_details = {
                    'customer': customer,
                    'invoice': paid_invoice,
                    'amount': amount,
                    'payment_date': payment_date,
                    'payment_method': payment_method,
                    'reference_number': reference_number,
                    'notes': notes,
                    'received_by': "Admin",
                    'challan_number': f"CH-{customer_id}-{int(dt.now().timestamp())}"
                }
            else:
                # Multiple invoices payment
                payment_details = {
                    'customer': customer,
                    'invoices': unpaid_invoices,
                    'amount': amount,  # Changed from 'total_amount' to 'amount' to match template
                    'payment_date': payment_date,
                    'payment_method': payment_method,
                    'reference_number': reference_number,
                    'notes': notes,
                    'received_by': "Admin",
                    'challan_number': f"CH-{customer_id}-{int(dt.now().timestamp())}"
                }
            
            return render_template("payment_challan.html", **payment_details)

        # GET request - show form
        invoices = Invoice.query.filter_by(
            customer_id=customer_id
        ).filter(Invoice.total > Invoice.total_paid).all()

        return render_template(
            "add_payment.html",
            customer=customer,
            invoices=invoices,
            today=dt.now().strftime("%Y-%m-%d")
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding payment: {str(e)}", "danger")
        return redirect(url_for("customer_khata", customer_id=customer_id))


@app.route("/assistant")
def assistant():
    """Chotu AI Assistant Chat Interface"""
    return render_template("assistant.html")


def api_chat():
    """Chat with Chotu AI Assistant"""
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        # Accept both 'conversation_history' (preferred) and legacy 'history'
        conversation_history = data.get("conversation_history")
        if conversation_history is None:
            conversation_history = data.get("history", [])

        if not user_message.strip():
            return jsonify({"success": False, "message": "Empty message"})

        # Get response from Chotu
        result = chotu_assistant.process_message(
            user_message, 'default', conversation_history
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Chat error: {str(e)}",
            "response": "माफ करें, कुछ गलत हुआ है। Sorry, something went wrong."
        })

# ---------- API ROUTES ----------


def dashboard_stats():
    """API endpoint for dashboard statistics"""
    try:
        stats = {
            'customers_count': Customer.query.count(),
            'products_count': Product.query.count(),
            'invoices_count': Invoice.query.count(),
            'total_revenue': db.session.query(
                db.func.sum(
                    Invoice.total)).scalar() or 0}
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ---------- SETTINGS / ADMIN ROUTES ----------
# ---------- ERROR HANDLERS ----------


@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    flash("Page not found.", "danger")
    return redirect(url_for("dashboard"))


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    flash("Internal server error occurred.", "danger")
    return redirect(url_for("dashboard"))


# ---------- SETTINGS / ADMIN ROUTES ----------

# Add missing settings routes
@app.route("/settings", methods=["GET"])
def settings_route():
    return settings_page()

@app.route("/settings/login", methods=["POST"])
def settings_login_route():
    return settings_login()

@app.route("/settings/logout", methods=["GET"])
def settings_logout_route():
    return settings_logout()


def admin_logged_in() -> bool:
    return session.get("admin_logged_in") is True


def settings_page():
    """Settings page (login if not authenticated)"""
    if not admin_logged_in():
        return render_template("settings.html", mode="login")
    # Some quick counts to show on settings page
    stats = {
        "customers": Customer.query.count(),
        "products": Product.query.count(),
        "invoices": Invoice.query.count(),
    }
    # Load preferences
    prefs = {
        'COMPANY_NAME': AppSetting.get('COMPANY_NAME', ''),
        'COMPANY_PHONE': AppSetting.get('COMPANY_PHONE', ''),
        'COMPANY_ADDRESS': AppSetting.get('COMPANY_ADDRESS', ''),
        'COMPANY_GSTIN': AppSetting.get('COMPANY_GSTIN', ''),
        'DEFAULT_PRINTER': AppSetting.get('DEFAULT_PRINTER', ''),
        'AUTO_PRINT_AFTER_SAVE': (
            AppSetting.get('AUTO_PRINT_AFTER_SAVE', 'false') or 'false'
        ).lower() == 'true'
    }
    return render_template(
        "settings.html",
        mode="settings",
        stats=stats,
        prefs=prefs)


def settings_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user = AdminUser.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session["admin_logged_in"] = True
        session["admin_username"] = user.username
        flash("Logged in to Settings.", "success")
        return redirect(url_for("settings_page"))
    flash("Invalid credentials.", "danger")
    return redirect(url_for("settings_page"))


def settings_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Logged out.", "success")
    return redirect(url_for("settings_page"))


def change_credentials():
    if not admin_logged_in():
        flash("Please login first.", "danger")
        return redirect(url_for("settings_page"))

    current_password = request.form.get("current_password", "")
    new_username = request.form.get("new_username", "").strip()
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    admin = AdminUser.query.filter_by(
        username=session.get("admin_username")).first()
    if not admin or not admin.check_password(current_password):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("settings_page"))

    # Update username if provided and different
    if new_username and new_username != admin.username:
        # Ensure unique username
        if AdminUser.query.filter_by(username=new_username).first():
            flash("Username already taken.", "danger")
            return redirect(url_for("settings_page"))
        admin.username = new_username
        session["admin_username"] = new_username

    # Update password if provided
    if new_password:
        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("settings_page"))
        admin.set_password(new_password)

    db.session.commit()
    flash("Credentials updated successfully.", "success")
    return redirect(url_for("settings_page"))


def update_preferences():
    if not admin_logged_in():
        flash("Please login first.", "danger")
        return redirect(url_for("settings_page"))
    # Save preferences
    AppSetting.set(
        'COMPANY_NAME',
        request.form.get(
            'company_name',
            '').strip())
    AppSetting.set(
        'COMPANY_PHONE',
        request.form.get(
            'company_phone',
            '').strip())
    AppSetting.set(
        'COMPANY_ADDRESS',
        request.form.get(
            'company_address',
            '').strip())
    AppSetting.set(
        'COMPANY_GSTIN',
        request.form.get(
            'company_gstin',
            '').strip())
    AppSetting.set(
        'DEFAULT_PRINTER',
        request.form.get(
            'default_printer',
            '').strip())
    AppSetting.set(
        'AUTO_PRINT_AFTER_SAVE',
        'true' if request.form.get('auto_print') == 'on' else 'false')
    flash("Preferences saved.", "success")
    return redirect(url_for("settings_page"))


def _clear_invoices_internal():
    # Delete invoice items first
    InvoiceItem.query.delete()
    db.session.commit()
    # Delete invoices
    Invoice.query.delete()
    db.session.commit()
    # Remove PDFs
    try:
        if os.path.isdir(INVOICE_DIR):
            for fname in os.listdir(INVOICE_DIR):
                if fname.lower().endswith(".pdf"):
                    try:
                        os.remove(os.path.join(INVOICE_DIR, fname))
                    except Exception:
                        pass
    except Exception:
        pass


def _check_admin_password(form_field_name='admin_password'):
    pwd = request.form.get(form_field_name, '')
    admin = AdminUser.query.filter_by(
        username=session.get("admin_username")).first()
    return bool(admin and admin.check_password(pwd))


def clear_products():
    if not admin_logged_in():
        flash("Unauthorized.", "danger")
        return redirect(url_for("settings_page"))
    if not _check_admin_password():
        flash("Password required for this action.", "danger")
        return redirect(url_for("settings_page"))
    Product.query.delete()
    db.session.commit()
    flash("All products cleared.", "success")
    return redirect(url_for("settings_page"))


def clear_customers():
    if not admin_logged_in():
        flash("Unauthorized.", "danger")
        return redirect(url_for("settings_page"))
    if not _check_admin_password():
        flash("Password required for this action.", "danger")
        return redirect(url_for("settings_page"))
    # Detach customers from invoices to avoid FK issues
    db.session.query(Invoice).update({Invoice.customer_id: None})
    db.session.commit()
    Customer.query.delete()
    db.session.commit()
    flash("All customers cleared.", "success")
    return redirect(url_for("settings_page"))


def clear_invoices():
    if not admin_logged_in():
        flash("Unauthorized.", "danger")
        return redirect(url_for("settings_page"))
    if not _check_admin_password():
        flash("Password required for this action.", "danger")
        return redirect(url_for("settings_page"))
    _clear_invoices_internal()
    flash("All invoices cleared.", "success")
    return redirect(url_for("settings_page"))


def clear_all():
    if not admin_logged_in():
        flash("Unauthorized.", "danger")
        return redirect(url_for("settings_page"))
    if not _check_admin_password():
        flash("Password required for this action.", "danger")
        return redirect(url_for("settings_page"))
    _clear_invoices_internal()
    Product.query.delete()
    Customer.query.delete()
    db.session.commit()
    flash("All data cleared (invoices, products, customers).", "success")
    return redirect(url_for("settings_page"))


def backup_db():
    if not admin_logged_in():
        flash("Unauthorized.", "danger")
        return redirect(url_for('settings_page'))
    # Prefer configured DB path; for sqlite:///data.db this is project root
    db_path = os.path.join(os.path.dirname(__file__), 'data.db')
    if not os.path.exists(db_path):
        # Fallback to instance folder
        db_path = os.path.join(
            os.path.dirname(__file__),
            'instance',
            'data.db')
    if not os.path.exists(db_path):
        flash('Database file not found.', 'danger')
        return redirect(url_for('settings_page'))
    return send_file(
        db_path,
        as_attachment=True,
        download_name=f"backup_{
            dt.now().strftime('%Y%m%d_%H%M%S')}.db")


def backup_invoices():
    if not admin_logged_in():
        flash("Unauthorized.", "danger")
        return redirect(url_for('settings_page'))
    # Create a temporary ZIP of invoices folder
    if not os.path.isdir(INVOICE_DIR):
        flash('Invoices folder not found.', 'danger')
        return redirect(url_for('settings_page'))
    tmp_dir = tempfile.mkdtemp()
    archive_path = os.path.join(tmp_dir, 'invoices_backup')
    shutil.make_archive(archive_path, 'zip', INVOICE_DIR)
    zip_path = archive_path + '.zip'
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=(
            f"invoices_{dt.now().strftime('%Y%m%d_%H%M%S')}.zip"
        ))


def export_products():
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Barcode', 'Name', 'Description',
                        'Company', 'Price', 'Tax'])
        for p in Product.query.all():
            writer.writerow([p.barcode or '',
                             p.name,
                             p.description or '',
                             p.company or '',
                             p.price or 0,
                             p.tax or 0])
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f"attachment; filename=products_export_{
            dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return response
    except Exception as e:
        flash(f"Export failed: {e}", 'danger')
        return redirect(url_for('settings_page'))

# ---------- PAYMENT MANAGEMENT ROUTES ----------


@app.route("/invoice/<int:invoice_id>/payments")
def invoice_payments(invoice_id):
    """View all payments for an invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template("invoice_payments.html", invoice=invoice)


@app.route("/invoice/<int:invoice_id>/add-payment", methods=["GET", "POST"])
def add_payment(invoice_id):
    """Add a new payment to an invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            payment_date = request.form.get(
                "payment_date", dt.now().strftime("%Y-%m-%d"))
            payment_method = request.form.get("payment_method", "cash")
            reference_number = request.form.get("reference_number", "")
            notes = request.form.get("notes", "")
            received_by = request.form.get("received_by", "")

            # Create payment
            payment = Payment(
                invoice_id=invoice_id,
                amount=amount,
                payment_date=payment_date,
                payment_method=payment_method,
                reference_number=reference_number,
                notes=notes,
                received_by=received_by
            )
            db.session.add(payment)

            # Update invoice payment status
            invoice.total_paid = (invoice.total_paid or 0) + amount
            if invoice.total_paid >= invoice.total:
                invoice.payment_status = 'paid'
            else:
                invoice.payment_status = 'partial'

            # Update customer's outstanding balance
            if invoice.customer:
                invoice.customer.outstanding_balance = max(
                    0, (invoice.customer.outstanding_balance or 0) - amount
                )
                invoice.customer.last_payment_date = payment_date

            db.session.commit()

            flash(
                f"Payment of ₹{
                    amount:.2f} recorded successfully!",
                "success")
            
            # Prepare challan data
            payment_details = {
                'customer': invoice.customer,
                'invoice': invoice,
                'amount': amount,
                'payment_date': payment_date,
                'payment_method': payment_method,
                'reference_number': reference_number,
                'notes': notes,
                'received_by': received_by,
                'challan_number': f"CH-{invoice.customer_id}-{int(dt.now().timestamp())}"
            }
            
            return render_template("payment_challan.html", **payment_details)

        except Exception as e:
            db.session.rollback()
            flash(f"Error recording payment: {str(e)}", "danger")
            return redirect(request.url)

    return render_template("add_payment.html", invoice=invoice, today=dt.now().strftime("%Y-%m-%d"))


def delete_payment(payment_id):
    """Delete a payment"""
    payment = Payment.query.get_or_404(payment_id)
    invoice_id = payment.invoice_id

    try:
        # Update invoice totals
        invoice = payment.invoice
        invoice.total_paid = (invoice.total_paid or 0) - payment.amount

        # Update payment status
        if invoice.total_paid <= 0:
            invoice.payment_status = 'unpaid'
        elif invoice.total_paid < invoice.total:
            invoice.payment_status = 'partial'
        else:
            invoice.payment_status = 'paid'

        db.session.delete(payment)
        db.session.commit()

        flash("Payment deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting payment: {str(e)}", "danger")

    return redirect(url_for("invoice_payments", invoice_id=invoice_id))


@app.route("/payment/<int:payment_id>/challan")
def payment_challan(payment_id):
    """View payment challan for a specific payment"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        invoice = payment.invoice
        customer = invoice.customer if invoice else None
        
        if not customer:
            flash("Payment challan not available - customer information missing", "danger")
            return redirect(url_for("dashboard"))
        
        # Prepare challan data
        payment_details = {
            'customer': customer,
            'invoice': invoice,
            'amount': payment.amount,
            'payment_date': payment.payment_date,
            'payment_method': payment.payment_method,
            'reference_number': payment.reference_number,
            'notes': payment.notes,
            'received_by': payment.received_by,
            'challan_number': f"CH-{customer.id}-{payment.id}"
        }
        
        return render_template("payment_challan.html", **payment_details)
        
    except Exception as e:
        flash(f"Error loading payment challan: {str(e)}", "danger")
        return redirect(url_for("dashboard"))


# ---------- CHOTU AI ASSISTANT ROUTES ----------

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8000)
