"""
Chotu Voice Assistant for Zankar Vision Electrical Shop - Pure AI Reasoning Version
"""
import os
from datetime import datetime
import re
from openai import OpenAI


class ChotuAssistant:
    """
    Chotu - Expert voice assistant for Zankar Vision electrical shop
    Uses pure AI reasoning without any pattern matching
    """

    def __init__(
            self,
            customer_model=None,
            product_model=None,
            invoice_model=None,
            invoice_item_model=None,
            db=None):
        """Initialize Chotu Assistant with database models"""
        # Personality
        self.personality = {
            "name": "Chotu",
            "role": "knowledgeable and efficient AI bot assistant for retail businesses",
            "traits": [
                "friendly",
                "helpful",
                "focused on providing clear and concise information",
                "understands the retail industry",
                "warm, friendly tone like a helpful shopkeeper"]}

        # Environment
        self.environment = {
            "context": "interacting with users looking to add voice capabilities to their retail business AI bot",
            "access": "information about various voice AI solutions and their potential applications in retail",
            "shop_details": {
                "name": "Zankar Vision",
                "address": "Opp Busstop, Main Bazaar Road, Waghai, Gujarat 394730",
                "phone": "9879289565",
                "type": "electrical shop specializing in electrical components, wiring, switches, and related products"
            }
        }

        # Tone
        self.tone = {
            "style": "professional, informative, and easy to understand",
            "language_mix": "primarily Hindi with some English terms",
            "natural_words": ["ji", "acha", "theek hai", "sahab", "bhai"],
            "guidelines": [
                "use clear and concise language",
                "avoid technical jargon when possible",
                "be patient and helpful",
                "keep responses SHORT - 2-3 sentences maximum",
                "DO NOT mix languages in one sentence",
                "DO NOT use Gujarati unless specifically asked"
            ]
        }

        # Core Values
        self.values = {
            "reliability": "provide accurate and consistent information",
            "efficiency": "complete tasks quickly and accurately",
            "helpfulness": "always look for ways to assist the user",
            "engagement": "maintain a conversational, approachable tone",
            "focus": "keep responses relevant to retail management",
            "positivity": "never match negativity or use sarcasm",
            "honesty": "always be truthful and transparent"
        }

        # Languages
        self.languages = {
            "primary": "Hindi",
            "secondary": "English",
            "support": [
                "हिंदी (Hindi)",
                "English"],
            "style": "mixed Hindi-English as commonly spoken in Indian retail shops"}

        # Technical setup
        self.model = "gpt-4o"  # Upgraded to better model for improved reasoning
        self.max_tokens = 400
        self.temperature = 0.7
        self.knowledge_cutoff = "September 2024"

        # Initialize OpenAI client
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                self.client = None
                print("Warning: OPENAI_API_KEY not found in environment variables")
        except Exception as e:
            self.client = None
            print(f"Warning: OpenAI client initialization failed: {e}")

        # Database models
        self.customer_model = customer_model
        self.product_model = product_model
        self.invoice_model = invoice_model
        self.invoice_item_model = invoice_item_model
        self.db = db

        # Conversation tracking
        self.conversation_history = {}
        self.conversation_state = {}

        # Ensure invoices directory exists (for optional PDF gen later)
        try:
            self.invoices_dir = os.path.join(
                os.path.dirname(__file__), 'invoices')
            os.makedirs(self.invoices_dir, exist_ok=True)
        except Exception:
            self.invoices_dir = None

    def initialize_models(
            self,
            customer_model,
            product_model,
            invoice_model,
            invoice_item_model=None,
            db=None):
        """Initialize database models after creation"""
        self.customer_model = customer_model
        self.product_model = product_model
        self.invoice_model = invoice_model
        self.invoice_item_model = invoice_item_model
        self.db = db

    def process_message(
            self,
            message,
            session_id='default',
            conversation_history=None):
        """Main entry point for processing user messages"""
        try:
            # Initialize conversation history if needed
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []

            # Add user message to history
            self.conversation_history[session_id].append(
                {"role": "user", "content": message})

            # Check for ongoing conversation states first
            state_result = self._handle_conversation_state(message, session_id)
            if state_result:
                response = state_result
            else:
                # Get intelligent AI-based response - let AI think for itself
                response = self._get_intelligent_response(
                    message, session_id, conversation_history)

            # Add assistant response to history
            self.conversation_history[session_id].append(
                {"role": "assistant", "content": response})

            # Keep conversation history manageable (last 10 messages)
            if len(self.conversation_history[session_id]) > 10:
                self.conversation_history[session_id] = self.conversation_history[session_id][-10:]

            # Build updated client-visible conversation context (append current
            # turn)
            updated_history = (conversation_history or []).copy()
            updated_history.append({"role": "user", "content": message})
            updated_history.append({"role": "model", "content": response})

            return {
                "success": True,
                "response": response,
                "conversation_context": updated_history,
                "session_id": session_id
            }

        except Exception as e:
            error_msg = f"Chotu: Maaf sahab, kuch gadbad hui hai. Error: {
                str(e)}"
            print(f"Chotu: Error processing message: {e}")

            updated_history = (conversation_history or []).copy()
            updated_history.append({"role": "user", "content": message})
            # No assistant response on error
            return {
                "success": False,
                "response": error_msg,
                "conversation_context": updated_history,
                "session_id": session_id,
                "error": str(e)
            }

    def _get_intelligent_response(
            self,
            message,
            session_id,
            conversation_history=None):
        """Use pure AI reasoning to understand user intent and provide intelligent responses"""

        try:
            # Use AI to understand intent and get database data
            if self.client:
                return self._generate_openai_response_with_data(
                    message, session_id, conversation_history)
            else:
                return "OpenAI client setup nahi hai. Phir se koshish kariye."

        except Exception as e:
            return f"Maaf sahab, samjh nahi paya. Error: {
                str(e)}. Phir se try kariye."

    def _generate_openai_response_with_data(
            self, message, session_id, conversation_history=None):
        """Generate response using OpenAI API with current database data"""
        try:
            # Get current database data for context
            database_context = self._get_database_context()

            messages = self._prepare_messages_for_openai_with_data(
                message, session_id, database_context, conversation_history)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=self.max_tokens,
                temperature=self.temperature
            )

            ai_response = response.choices[0].message.content.strip()

            # Parse and execute any actions in the response
            final_response = self._parse_and_execute_actions(
                ai_response, session_id)

            return final_response

        except Exception as e:
            print(f"Chotu: OpenAI API error: {e}")
            return f"Maaf sahab, thoda problem aa gaya hai. Phir se try kariye. Error: {
                str(e)}"

    def _parse_and_execute_actions(self, ai_response, session_id):
        """Parse AI response for action commands and execute them"""
        import re

        # Find all action commands in the response
        action_pattern = r'\[ACTION:\s*([^\]]+)\](.*?)(?=\[ACTION:|\Z)'
        actions = re.findall(
            action_pattern,
            ai_response,
            re.DOTALL | re.IGNORECASE)

        # Remove action commands from the response text
        clean_response = re.sub(
            r'\[ACTION:[^\]]+\].*?(?=\[ACTION:|\Z)',
            '',
            ai_response,
            flags=re.DOTALL | re.IGNORECASE).strip()

        # Execute each action
        for action_match in actions:
            action_type = action_match[0].strip().upper()
            action_params = action_match[1].strip()

            try:
                if action_type == 'CREATE_CUSTOMER':
                    result = self._execute_create_customer(
                        action_params, session_id)
                    if result:
                        clean_response += f" {result}"

                elif action_type == 'CREATE_PRODUCT':
                    result = self._execute_create_product(
                        action_params, session_id)
                    if result:
                        clean_response += f" {result}"

                elif action_type == 'START_INVOICE':
                    result = self._execute_start_invoice(
                        action_params, session_id)
                    if result:
                        clean_response += f" {result}"

                elif action_type == 'ADD_ITEM_TO_INVOICE':
                    result = self._execute_add_item_to_invoice(
                        action_params, session_id)
                    if result:
                        clean_response += f" {result}"

                elif action_type == 'FINALIZE_INVOICE':
                    result = self._execute_finalize_invoice(
                        action_params, session_id)
                    if result:
                        clean_response += f" {result}"

                elif action_type == 'RECORD_PAYMENT':
                    result = self._execute_record_payment(
                        action_params, session_id)
                    if result:
                        clean_response += f" {result}"

            except Exception as e:
                print(f"Error executing action {action_type}: {e}")
                clean_response += f" Action {action_type} mein error: {str(e)}"

        return clean_response

    def _execute_create_customer(self, params, session_id):
        """Execute CREATE_CUSTOMER action"""
        # Parse parameters like "Name: Hema, Phone: 9898021504, Address:
        # Kerala"
        param_dict = {}
        for param in params.split(','):
            if ':' in param:
                key, value = param.split(':', 1)
                param_dict[key.strip().lower()] = value.strip()

        name = param_dict.get('name')
        phone = param_dict.get('phone')
        address = param_dict.get('address', '')

        if not name or not phone:
            return None

        try:
            # Check if customer exists
            existing = self.customer_model.query.filter_by(phone=phone).first()
            if existing:
                existing.name = name
                existing.address = address
                self.db.session.commit()
                return f"Customer {name} update ho gaya!"
            else:
                new_customer = self.customer_model(
                    name=name, phone=phone, address=address)
                self.db.session.add(new_customer)
                self.db.session.commit()
                return f"Customer {name} add ho gaya!"
        except Exception as e:
            self.db.session.rollback()
            return f"Customer create karne mein error: {str(e)}"

    def _execute_create_product(self, params, session_id):
        """Execute CREATE_PRODUCT action"""
        param_dict = {}
        for param in params.split(','):
            if ':' in param:
                key, value = param.split(':', 1)
                param_dict[key.strip().lower()] = value.strip()

        name = param_dict.get('name')
        price = param_dict.get('price')
        description = param_dict.get('description', '')

        if not name or not price:
            return None

        try:
            price_float = float(price.replace('₹', '').replace(',', ''))
            new_product = self.product_model(
                name=name, price=price_float, description=description)
            self.db.session.add(new_product)
            self.db.session.commit()
            return f"Product {name} inventory mein add ho gaya!"
        except Exception as e:
            self.db.session.rollback()
            return f"Product create karne mein error: {str(e)}"

    def _execute_start_invoice(self, params, session_id):
        """Execute START_INVOICE action"""
        param_dict = {}
        for param in params.split(','):
            if ':' in param:
                key, value = param.split(':', 1)
                param_dict[key.strip().lower()] = value.strip()

        customer_name = param_dict.get(
            'customername') or param_dict.get('customer')

        if not customer_name:
            return None

        try:
            # Find customer
            customer = self.customer_model.query.filter(
                self.customer_model.name.ilike(
                    f'%{customer_name}%')).first()
            if not customer:
                return f"Customer {customer_name} nahi mila. Pehle customer add kariye."

            # Start invoice
            invoice = self._start_invoice_for_customer(customer)
            self.conversation_state[session_id] = {
                'process': 'creating_invoice',
                'step': 'waiting_for_items',
                'invoice_id': invoice.id,
                'customer_id': customer.id
            }
            return f"Invoice {invoice.number} start kar diya!"
        except Exception as e:
            return f"Invoice start karne mein error: {str(e)}"

    def _execute_add_item_to_invoice(self, params, session_id):
        """Execute ADD_ITEM_TO_INVOICE action"""
        param_dict = {}
        for param in params.split(','):
            if ':' in param:
                key, value = param.split(':', 1)
                param_dict[key.strip().lower()] = value.strip()

        product_name = param_dict.get('product')
        quantity = param_dict.get('quantity', '1')
        price = param_dict.get('price')

        if not product_name:
            return None

        try:
            qty = int(quantity)
            state = self.conversation_state.get(session_id, {})
            invoice_id = state.get('invoice_id')

            if not invoice_id:
                return "Invoice nahi chal raha. Pehle invoice start kariye."

            # Find or create product
            product = self.product_model.query.filter(
                self.product_model.name.ilike(
                    f'%{product_name}%')).first()
            if not product:
                if not price:
                    return f"Product {product_name} nahi mila aur price nahi diya. Price batayiye."
                # Create product
                price_float = float(price.replace('₹', '').replace(',', ''))
                product = self.product_model(
                    name=product_name,
                    price=price_float,
                    description="Created during invoice")
                self.db.session.add(product)
                self.db.session.flush()

            # Add to invoice
            unit_price = float(
                price.replace(
                    '₹',
                    '').replace(
                    ',',
                    '')) if price else (
                product.price or 0)
            line_total = qty * unit_price
            invoice_item = self.invoice_item_model(
                invoice_id=invoice_id,
                product_id=product.id,
                qty=qty,
                price=unit_price,
                line_total=line_total,
                description=product.description or ''
            )
            self.db.session.add(invoice_item)
            self.db.session.commit()

            return f"{qty} x {
                product.name} @ ₹{unit_price} = ₹{line_total} add ho gaya!"
        except Exception as e:
            self.db.session.rollback()
            return f"Item add karne mein error: {str(e)}"

    def _execute_finalize_invoice(self, params, session_id):
        """Execute FINALIZE_INVOICE action"""
        param_dict = {}
        for param in params.split(','):
            if ':' in param:
                key, value = param.split(':', 1)
                param_dict[key.strip().lower()] = value.strip()

        invoice_number = param_dict.get(
            'invoicenumber') or param_dict.get('invoice')

        try:
            if invoice_number:
                invoice = self.invoice_model.query.filter_by(
                    number=invoice_number).first()
            else:
                state = self.conversation_state.get(session_id, {})
                invoice_id = state.get('invoice_id')
                invoice = self.invoice_model.query.get(
                    invoice_id) if invoice_id else None

            if not invoice:
                return "Invoice nahi mila."

            # Calculate total
            total = sum((item.line_total or 0)
                        for item in invoice.invoice_items)
            invoice.total = total
            self.db.session.commit()

            # Clear state
            self.conversation_state[session_id] = {}

            return f"Invoice {invoice.number} complete! Total: ₹{total}"
        except Exception as e:
            self.db.session.rollback()
            return f"Invoice finalize karne mein error: {str(e)}"

    def _execute_record_payment(self, params, session_id):
        """Execute RECORD_PAYMENT action"""
        param_dict = {}
        for param in params.split(','):
            if ':' in param:
                key, value = param.split(':', 1)
                param_dict[key.strip().lower()] = value.strip()

        invoice_number = param_dict.get(
            'invoice') or param_dict.get('invoicenumber')
        amount = param_dict.get('amount')
        payment_method = param_dict.get('method', 'cash')
        payment_date = param_dict.get(
            'date', datetime.now().strftime('%Y-%m-%d'))

        if not invoice_number or not amount:
            return None

        try:
            # Find invoice
            invoice = self.invoice_model.query.filter_by(
                number=invoice_number).first()
            if not invoice:
                return f"Invoice {invoice_number} nahi mila."

            # Record payment
            amount_float = float(amount.replace('₹', '').replace(',', ''))

            # Import Payment model
            from app import Payment

            payment = Payment(
                invoice_id=invoice.id,
                amount=amount_float,
                payment_date=payment_date,
                payment_method=payment_method,
                notes="Recorded via chat assistant"
            )
            self.db.session.add(payment)

            # Update invoice payment status
            invoice.total_paid = (invoice.total_paid or 0) + amount_float
            if invoice.total_paid >= invoice.total:
                invoice.payment_status = 'paid'
            else:
                invoice.payment_status = 'partial'

            self.db.session.commit()

            remaining = invoice.total - invoice.total_paid
            return f"Payment ₹{amount_float} record ho gaya! Remaining: ₹{remaining}"
        except Exception as e:
            self.db.session.rollback()
            return f"Payment record karne mein error: {str(e)}"

    def _get_database_context(self):
        """Get current database state for AI context"""
        try:
            context = {}

            # Get customers
            customers = self.customer_model.query.all()
            context['customers'] = [
                {"name": c.name, "phone": c.phone, "address": c.address}
                for c in customers[:10]  # Limit to avoid token overflow
            ]

            # Get products
            products = self.product_model.query.all()
            context['products'] = [
                {"name": p.name, "price": p.price, "description": p.description}
                for p in products[:15]  # Limit to avoid token overflow
            ]

            # Get recent invoices
            from datetime import datetime
            recent_invoices = self.invoice_model.query.order_by(
                self.invoice_model.id.desc()
            ).limit(5).all()

            context['recent_invoices'] = [
                {
                    "number": inv.number,
                    "customer": (inv.customer.name if getattr(inv, 'customer', None) else "Unknown"),
                    "total": inv.total,
                    "date": inv.invoice_date
                }
                for inv in recent_invoices
            ]

            # Get today's business summary
            today = datetime.now().strftime('%Y-%m-%d')
            today_invoices = self.invoice_model.query.filter(
                self.invoice_model.invoice_date == today
            ).all()

            context['today_summary'] = {
                "bills_count": len(today_invoices),
                "total_revenue": float(sum((inv.total or 0) for inv in today_invoices))
            }

            return context

        except Exception as e:
            return {"error": f"Database context error: {str(e)}"}

    def _prepare_messages_for_openai_with_data(
            self,
            message,
            session_id,
            database_context,
            conversation_history=None):
        """Prepare messages for OpenAI API with database context"""
        system_prompt = f"""You are Chotu, an expert voice assistant for {self.environment['shop_details']['name']} electrical shop. 

CURRENT DATABASE STATE:
- Customers: {len(database_context.get('customers', []))} customers available
- Products: {len(database_context.get('products', []))} products in inventory  
- Recent Bills: {len(database_context.get('recent_invoices', []))} recent invoices
- Today's Business: {database_context.get('today_summary', {}).get('bills_count', 0)} bills, ₹{database_context.get('today_summary', {}).get('total_revenue', 0)} revenue

CURRENT INVENTORY:
{chr(10).join([f"- {p['name']}: ₹{p['price']}" for p in database_context.get('products', [])[:10]])}

RECENT CUSTOMERS:
{chr(10).join([f"- {c['name']}: {c['phone']}" for c in database_context.get('customers', [])[:5]])}

RECENT INVOICES:
{chr(10).join([f"- {inv['number']}: {inv['customer']} - ₹{inv['total']}" for inv in database_context.get('recent_invoices', [])[:3]])}

IMPORTANT: When you want to perform database operations, output ACTION commands in your response using this exact format:
[ACTION: CREATE_CUSTOMER] Name: CustomerName, Phone: 9876543210, Address: AddressHere
[ACTION: CREATE_PRODUCT] Name: ProductName, Price: 10000, Description: DescriptionHere
[ACTION: START_INVOICE] CustomerName: CustomerName
[ACTION: ADD_ITEM_TO_INVOICE] Product: ProductName, Quantity: 1, Price: 10000
[ACTION: FINALIZE_INVOICE] InvoiceNumber: INV-000001
[ACTION: RECORD_PAYMENT] Invoice: INV-000001, Amount: 5000, Method: cash, Date: 2024-01-15
[ACTION: CREATE_PAYMENT_PLAN] Invoice: INV-000001, Type: installment, Installments: 3, Frequency: monthly

The system will automatically execute these actions and replace the action text with confirmation messages.

INTELLIGENT ACTIONS YOU CAN TAKE:
When users want to:

1. CREATE INVOICES/BILLS:
   - If customer exists: Use their ID to create invoice
   - If customer doesn't exist: Collect name, phone, address, then create customer and invoice
   - For products: Check if exists in inventory, if not collect name and price to create new product
   - Use conversation_state to track multi-step processes

2. RECORD PAYMENTS:
   - Extract invoice number, amount, payment method (cash/card/bank_transfer/cheque/upi)
   - Update invoice payment status (unpaid -> partial -> paid)
   - Calculate remaining balance automatically

3. CREATE PAYMENT PLANS:
   - For installment payments: Set up monthly/weekly/quarterly payment schedules
   - Calculate installment amounts based on remaining balance
   - Support flexible payment arrangements

4. ADD PRODUCTS TO INVENTORY:
   - Extract product name, price, and optional details from user message
   - Create new product entry in database
   - Confirm success to user

5. ADD NEW CUSTOMERS:
   - Extract name and optional phone from user message
   - If phone missing, ask for it
   - Create customer entry and confirm

6. PROVIDE BUSINESS INFO:
   - Use today's summary and recent data to answer questions
   - Show sales reports, customer info, product details as requested
   - Include payment status and outstanding balances

CONVERSATION STATE MANAGEMENT:
You can set conversation_state[session_id] to track multi-step processes:
- For invoice: {{'process': 'creating_invoice', 'step': 'waiting_for_items', 'invoice_id': id, 'customer_id': id}}
- For new customer: {{'process': 'creating_customer_for_invoice', 'step': 'waiting_for_phone', 'customer_name': name}}
- For new product: {{'process': 'creating_product_for_invoice', 'step': 'waiting_for_price', 'product_name': name}}

DATABASE OPERATIONS:
You have access to these models and can perform database operations:
- customer_model.query.filter_by(name=name).first() - find customer
- product_model.query.filter(name.ilike(f'%{{name}}%')).first() - find product
- Create new records and commit to database
- Handle duplicate phone numbers by updating existing customers

RESPONSE GUIDELINES:
- Use natural Hindi-English mix as shopkeeper would speak
- Keep responses SHORT - 2-3 sentences maximum
- Be proactive in offering to create missing customers/products
- Use conversation states for multi-step processes
- Always confirm actions taken
- Use ₹ symbol for prices
- Include invoice numbers when creating bills

CRITICAL: Think intelligently about user intent. Don't rely on keyword matching - understand what they want to accomplish and take appropriate actions using the database and conversation state.

Shop: {self.environment['shop_details']['name']}, {self.environment['shop_details']['address']}"""

        messages = [{"role": "system", "content": system_prompt}]

        # Add prior conversation (if provided by the client)
        if conversation_history:
            # Map client roles to OpenAI roles (client uses 'user' and 'model')
            # limit to last 10 turns for token control
            for turn in conversation_history[-10:]:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if not content:
                    continue
                if role == "model":
                    mapped_role = "assistant"
                elif role == "user":
                    mapped_role = "user"
                else:
                    mapped_role = "user"
                messages.append({"role": mapped_role, "content": content})

        # Add current user message
        messages.append({"role": "user", "content": message})

        return messages

    def _handle_conversation_state(self, message, session_id):
        """Handle ongoing conversation states and multi-step processes"""
        state = self.conversation_state.get(session_id, {})
        message_lower = message.lower()

        # Check for cancellation keywords first in any state
        cancel_keywords = [
            'cancel',
            'cancle',
            'khatam',
            'band karo',
            'stop',
            'abort',
            'quit',
            'exit',
            'mat banao',
            'nahi chahiye']
        if any(keyword in message_lower for keyword in cancel_keywords):
            self.conversation_state[session_id] = {}
            return "Theek hai ji, process cancel kar diya. Aur kuch madad karu?"

        # Handle invoice creation process
        if state.get('process') == 'creating_invoice':
            invoice_id = state.get('invoice_id')

            if state.get('step') == 'waiting_for_items':
                # Allow canceling the invoice creation
                if any(
                    w in message_lower for w in [
                        'cancel',
                        'abort',
                        'mat banao',
                        'band karo',
                        'stop']):
                    # Clean up: if invoice has no items, delete it; else keep
                    # as draft with total = sum(items)
                    inv = self.invoice_model.query.get(invoice_id)
                    if inv:
                        if not inv.invoice_items:
                            try:
                                self.db.session.delete(inv)
                                self.db.session.commit()
                            except Exception:
                                self.db.session.rollback()
                        else:
                            try:
                                inv.total = sum((it.line_total or 0)
                                                for it in inv.invoice_items)
                                self.db.session.commit()
                            except Exception:
                                self.db.session.rollback()
                    self.conversation_state[session_id] = {}
                    return "Theek hai ji, invoice process cancel kar diya. Aur kuch madad karu?"

                # User is adding items to invoice
                if any(
                    word in message_lower for word in [
                        'done',
                        'finish',
                        'complete',
                        'ho gaya',
                        'kar do',
                        'confirm',
                        'finalize']):
                    # Finalize invoice
                    return self._finalize_invoice(session_id, invoice_id)

                # Ignore short filler/noise words
                fillers = {
                    'hey',
                    'are',
                    'arre',
                    'haan',
                    'han',
                    'ok',
                    'okay',
                    'okk',
                    'hmm',
                    'humm',
                    'huh',
                    'hmmm',
                    'hmm.',
                    'ji',
                    'acha'}
                if message_lower.strip() in fillers or len(message_lower.strip()) <= 2:
                    return "Ji. Product ka naam aur quantity batayiye—jaise '1 Samsung TV' ya '2 Fan @ 1450'."

                # Try to add item
                return self._add_item_to_invoice(
                    message, invoice_id, session_id)

        # Handle customer creation process
        elif state.get('process') == 'creating_customer':
            if state.get('step') == 'waiting_for_phone':
                # Extract phone number
                import re
                phone_match = re.search(r'\d{10}', message)
                if phone_match:
                    phone = phone_match.group()
                    customer_name = state.get('customer_name')

                    # Create customer
                    new_customer = self.customer_model(
                        name=customer_name, phone=phone)
                    self.db.session.add(new_customer)
                    self.db.session.commit()

                    # Clear state
                    self.conversation_state[session_id] = {}

                    return f"Customer {customer_name} add ho gaya! Phone: {phone}. Ab kya karna hai?"
                else:
                    return "Phone number theek se nahi samjha. 10 digit ka phone number boliye."

        # Handle customer creation process for invoice
        elif state.get('process') == 'creating_customer_for_invoice':
            if state.get('step') == 'waiting_for_phone':
                # Check if user is correcting the name instead of providing
                # phone
                corrected_name = self._extract_potential_customer_name(message)
                if corrected_name and corrected_name.lower(
                ) != state.get('customer_name', '').lower():
                    # User is correcting the name
                    self.conversation_state[session_id]['customer_name'] = corrected_name
                    return f"Acha, samjha. '{corrected_name}' ka phone number batayiye (10 digits)."

                # Extract phone number
                import re
                phone_match = re.search(r'\d{10}', message)
                if phone_match:
                    phone = phone_match.group()
                    customer_name = state.get('customer_name')

                    # Set next step to collect address
                    self.conversation_state[session_id]['step'] = 'waiting_for_address'
                    self.conversation_state[session_id]['customer_phone'] = phone

                    return f"Phone number {phone} save ho gaya. Ab {customer_name} ka address batayiye."
                else:
                    return "Phone number theek se nahi samjha. 10 digit ka phone number boliye. Ya 'cancel' bolke process band kar sakte hain."

            elif state.get('step') == 'waiting_for_address':
                customer_name = state.get('customer_name')
                phone = state.get('customer_phone')
                address = message.strip()

                try:
                    # Check if customer with this phone already exists
                    existing_customer = self.customer_model.query.filter_by(
                        phone=phone).first()
                    if existing_customer:
                        # Update existing customer's name and address
                        existing_customer.name = customer_name
                        existing_customer.address = address
                        self.db.session.commit()
                        new_customer = existing_customer
                    else:
                        # Create new customer
                        new_customer = self.customer_model(
                            name=customer_name, phone=phone, address=address)
                        self.db.session.add(new_customer)
                        self.db.session.commit()

                    # Start invoice for this customer
                    invoice = self._start_invoice_for_customer(new_customer)
                    self.conversation_state[session_id] = {
                        'process': 'creating_invoice',
                        'step': 'waiting_for_items',
                        'invoice_id': invoice.id,
                        'customer_id': new_customer.id
                    }

                    return f"✅ Customer '{customer_name}' create ho gaya! Invoice {
                        invoice.number} start kar diya. Ab products batayiye, jaise '1 Samsung TV'."

                except Exception as e:
                    self.db.session.rollback()
                    self.conversation_state[session_id] = {}
                    return f"Customer create karne mein problem: {
                        str(e)}. Phir se try kariye."

        # Handle product creation process for invoice
        elif state.get('process') == 'creating_product_for_invoice':
            if state.get('step') == 'waiting_for_price':
                message_lower = message.lower()

                # Check if user wants to complete the invoice instead
                if any(
                    word in message_lower for word in [
                        'done',
                        'finish',
                        'complete',
                        'ho gaya',
                        'kar do',
                        'confirm',
                        'finalize']):
                    # Switch back to invoice mode without adding the product
                    invoice_id = state.get('invoice_id')
                    customer_id = state.get('customer_id')
                    self.conversation_state[session_id] = {
                        'process': 'creating_invoice',
                        'step': 'waiting_for_items',
                        'invoice_id': invoice_id,
                        'customer_id': customer_id
                    }
                    return self._finalize_invoice(session_id, invoice_id)

                # Extract price from message
                import re
                price_match = re.search(r'(\d+[\d,]*\.?\d*)', message)
                if price_match:
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                        return self._create_product_and_add_to_invoice(
                            session_id, price)
                    except ValueError:
                        return "Price samjh nahi aaya. Sirf number batayiye jaise '15000' ya '1299.50'."
                else:
                    return "Price nahi samjha. Product ka price batayiye (sirf number, jaise 15000)."

        return None

    def _extract_customer_from_text(self, text):
        """Find a customer whose name appears in the text (case-insensitive)."""
        candidates = self.customer_model.query.all()
        text_lower = text.lower()
        matches = [c for c in candidates if c.name and c.name.lower()
                   in text_lower]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # If multiple, prefer the longest name match
            matches.sort(key=lambda c: len(c.name), reverse=True)
            return matches[0]
        return None

    def _compute_next_invoice_number(self):
        """Compute next invoice number by scanning existing numbers safely."""
        try:
            all_nums = [
                inv.number for inv in self.invoice_model.query.all() if inv.number]
            values = []
            for n in all_nums:
                m = re.search(r'(\d+)$', n)
                if m:
                    values.append(int(m.group(1)))
            next_num = (max(values) + 1) if values else 1
        except Exception:
            next_num = (self.invoice_model.query.count() + 1)
        return f"INV-{str(next_num).zfill(6)}"

    def _start_invoice_for_customer(self, customer):
        today = datetime.now().strftime('%Y-%m-%d')
        inv_no = self._compute_next_invoice_number()
        inv = self.invoice_model(
            number=inv_no,
            customer_id=customer.id,
            invoice_date=today,
            due_date=today,
            terms='Due on Receipt',
            salesperson=None,
            notes=None,
            discount_type=None,
            discount_amount=0.0,
            total=0.0
        )
        self.db.session.add(inv)
        self.db.session.commit()
        return inv

    def _finalize_invoice(self, session_id, invoice_id):
        invoice = self.invoice_model.query.get(invoice_id)
        if not invoice:
            return "Maaf kijiye, invoice nahi mila. Phir se try kariye."
        total = sum((item.line_total or 0) for item in invoice.invoice_items)
        invoice.total = total
        self.db.session.commit()
        # Clear state
        self.conversation_state[session_id] = {}
        return f"✅ Invoice {
            invoice.number} complete ho gaya! Total: ₹{
            total:.2f}. Aap invoices page par dekh sakte hain."

    def _add_item_to_invoice(self, message, invoice_id, session_id):
        """Add item to invoice from natural language with a simple parser."""
        try:
            # Enhanced parsing for natural language patterns
            # Handle patterns like "she bought computer mouse worth 3000rs" or
            # "he purchased LED TV for 25000"
            text = message.strip()

            # Pattern 1: "bought/purchased [product] worth/for [price]"
            natural_pattern = re.search(
                r'(?:bought|purchased|buy|took)\s+(.+?)\s+(?:worth|for|at)\s*(?:rs\.?|₹)?\s*(\d+[\d,]*\.?\d*)',
                text,
                re.IGNORECASE)
            if natural_pattern:
                product_part = natural_pattern.group(1).strip()
                price_override = float(
                    natural_pattern.group(2).replace(
                        ',', ''))
                qty = 1
            else:
                # Pattern 2: Standard format with optional quantity
                qty = 1
                price_override = None
                m = re.match(r"^(\d+)\s+(.+)$", text)
                if m:
                    qty = int(m.group(1))
                    product_part = m.group(2)
                else:
                    product_part = text

                price_match = re.search(
                    r"(?:@|at)\s*(\d+[\d,]*\.?\d*)",
                    product_part,
                    re.IGNORECASE)
                if price_match:
                    try:
                        price_override = float(
                            price_match.group(1).replace(',', ''))
                    except Exception:
                        price_override = None
                    product_part = re.sub(
                        r"(?:@|at)\s*\d+[\d,]*\.?\d*",
                        "",
                        product_part,
                        flags=re.IGNORECASE).strip()

            # Clean up product name
            product_part = re.sub(
                r'^(she|he|customer|they)\s+',
                '',
                product_part,
                flags=re.IGNORECASE).strip()

            # Find product by name (ILIKE)
            product = self.product_model.query.filter(
                self.product_model.name.ilike(f'%{product_part}%')
            ).first()

            if not product:
                # Offer to create new product
                current_state = self.conversation_state.get(session_id, {})
                self.conversation_state[session_id] = {
                    'process': 'creating_product_for_invoice',
                    'step': 'waiting_for_price',
                    'product_name': product_part,
                    'quantity': qty,
                    'invoice_id': invoice_id,
                    # Preserve customer_id
                    'customer_id': current_state.get('customer_id'),
                    'price_override': price_override
                }
                if price_override is not None:
                    # Price was provided, use it
                    return self._create_product_and_add_to_invoice(
                        session_id, price_override)
                else:
                    suggestions = [
                        p.name for p in self.product_model.query.limit(3).all()]
                    return f"'{product_part}' product database mein nahi hai. Price batayiye ya available products mein se choose kariye: {
                        ', '.join(suggestions)}."

            unit_price = price_override if price_override is not None else (
                product.price or 0)
            line_total = qty * unit_price
            invoice_item = self.invoice_item_model(
                invoice_id=invoice_id,
                product_id=product.id,
                qty=qty,
                price=unit_price,
                discount_amount=0.0,
                tax=0.0,
                line_total=line_total,
                description=product.description or ''
            )
            self.db.session.add(invoice_item)
            self.db.session.commit()

            return f"✅ {qty} x {
                product.name} @ ₹{
                unit_price:.2f} = ₹{
                line_total:.2f} add ho gaya! Aur item? Ya 'done' boliye."

        except Exception as e:
            return f"Item add karne mein error: {str(e)}"

    def _create_product_and_add_to_invoice(self, session_id, price):
        """Create a new product and add it to the invoice."""
        try:
            state = self.conversation_state.get(session_id, {})
            product_name = state.get('product_name')
            quantity = state.get('quantity', 1)
            invoice_id = state.get('invoice_id')

            if not all([product_name, invoice_id]):
                return "Product creation process mein error hai. Phir se try kariye."

            # Create new product
            new_product = self.product_model(
                name=product_name,
                price=float(price),
                description="Created during invoice process",
                company=None,
                barcode=None,
                tax=0.0
            )
            self.db.session.add(new_product)
            self.db.session.flush()  # Get the ID

            # Add to invoice
            line_total = quantity * float(price)
            invoice_item = self.invoice_item_model(
                invoice_id=invoice_id,
                product_id=new_product.id,
                qty=quantity,
                price=float(price),
                discount_amount=0.0,
                tax=0.0,
                line_total=line_total,
                description=new_product.description or ''
            )
            self.db.session.add(invoice_item)
            self.db.session.commit()

            # Clear state back to invoice creation
            self.conversation_state[session_id] = {
                'process': 'creating_invoice',
                'step': 'waiting_for_items',
                'invoice_id': invoice_id,
                'customer_id': state.get('customer_id')
            }

            return f"✅ Product '{product_name}' create ho gaya! {quantity} x {product_name} @ ₹{price} = ₹{line_total} invoice mein add ho gaya. Aur items? Ya 'done' boliye."

        except Exception as e:
            self.db.session.rollback()
            return f"Product create karne mein error: {str(e)}"


def get_assistant():
    """Factory function to create Chotu assistant instance"""
    return ChotuAssistant()


def initialize_models(customer_model, product_model, invoice_model):
    """Initialize assistant with database models"""
    assistant = get_assistant()
    assistant.initialize_models(customer_model, product_model, invoice_model)
    return assistant
