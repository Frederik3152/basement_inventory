"""
Simple database module for Basement Inventory Manager
"""
import os
import psycopg2
import psycopg2.extras
from datetime import datetime
import uuid
import json
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        """Initialize database connection and create tables"""
        self.connection_string = os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Get schema from environment variable, default to 'home_database_dev'
        self.schema = os.getenv('DATABASE_SCHEMA', 'home_database_dev')
        
        self.init_tables()
    
    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(self.connection_string)
    
    def _get_table_name(self, table: str) -> str:
        """Get fully qualified table name with schema"""
        return f"{self.schema}.{table}"
    
    def init_tables(self):
        """Initialize database tables in the specified schema"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create schema if it doesn't exist
                if self.schema != 'public':
                    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
                
                # Categories table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self._get_table_name('categories')} (
                        id VARCHAR(50) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL
                    )
                """)
                
                # Items table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self._get_table_name('items')} (
                        id VARCHAR(36) PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        barcodes TEXT[], -- Array of barcodes
                        category_id VARCHAR(50) REFERENCES {self._get_table_name('categories')}(id),
                        current_stock INTEGER NOT NULL DEFAULT 0,
                        min_stock INTEGER NOT NULL DEFAULT 0,
                        unit VARCHAR(50) NOT NULL,
                        location VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Transactions table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self._get_table_name('transactions')} (
                        id VARCHAR(36) PRIMARY KEY,
                        item_id VARCHAR(36) REFERENCES {self._get_table_name('items')}(id) ON DELETE CASCADE,
                        type VARCHAR(20) NOT NULL CHECK (type IN ('restock', 'usage')),
                        quantity INTEGER NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Projects table (for fermentations, brines, etc.)
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self._get_table_name('projects')} (
                        id VARCHAR(36) PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        type VARCHAR(50) NOT NULL,
                        start_date DATE NOT NULL,
                        ready_date DATE,
                        expiry_date DATE,
                        status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'expired', 'discarded')),
                        location VARCHAR(100),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert default categories if they don't exist
                default_categories = [
                    ('paper-products', 'Paper Products'),
                    ('canned-goods', 'Canned Goods'),
                    ('cleaning-supplies', 'Cleaning Supplies'),
                    ('personal-care', 'Personal Care'),
                    ('beverages', 'Beverages'),
                    ('snacks', 'Snacks'),
                    ('alcohol', 'Alcohol'),
                    ('other', 'Other')
                ]
                
                for cat_id, cat_name in default_categories:
                    cur.execute(f"""
                        INSERT INTO {self._get_table_name('categories')} (id, name) 
                        VALUES (%s, %s) 
                        ON CONFLICT (id) DO NOTHING
                    """, (cat_id, cat_name))
                
                conn.commit()
                print(f"✅ Database tables initialized in schema: {self.schema}")
    
    def get_categories(self):
        """Get all categories"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"SELECT id, name FROM {self._get_table_name('categories')} ORDER BY name")
                categories = {}
                for row in cur.fetchall():
                    categories[row['id']] = {'name': row['name'], 'items': []}
                return categories
    
    def get_items(self):
        """Get all items with category names"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"""
                    SELECT i.*, c.name as category_name 
                    FROM {self._get_table_name('items')} i 
                    JOIN {self._get_table_name('categories')} c ON i.category_id = c.id 
                    ORDER BY i.name
                """)
                items = []
                for row in cur.fetchall():
                    item = dict(row)
                    item['category'] = item['category_id']
                    item['last_updated'] = item['updated_at'].isoformat() if item['updated_at'] else None
                    items.append(item)
                return items
    
    def get_item_by_id(self, item_id: str):
        """Get a single item by ID"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"""
                    SELECT i.*, c.name as category_name 
                    FROM {self._get_table_name('items')} i 
                    JOIN {self._get_table_name('categories')} c ON i.category_id = c.id 
                    WHERE i.id = %s
                """, (item_id,))
                row = cur.fetchone()
                if row:
                    item = dict(row)
                    item['category'] = item['category_id']
                    item['last_updated'] = item['updated_at'].isoformat() if item['updated_at'] else None
                    return item
                return None
    
    def get_item_by_barcode(self, barcode: str):
        """Get item by barcode"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"""
                    SELECT i.*, c.name as category_name 
                    FROM {self._get_table_name('items')} i 
                    JOIN {self._get_table_name('categories')} c ON i.category_id = c.id 
                    WHERE %s = ANY(i.barcodes)
                """, (barcode,))
                row = cur.fetchone()
                if row:
                    item = dict(row)
                    item['category'] = item['category_id']
                    item['last_updated'] = item['updated_at'].isoformat() if item['updated_at'] else None
                    return item
                return None
    
    def create_item(self, item_data: dict) -> str:
        """Create a new item"""
        item_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self._get_table_name('items')} (id, name, barcodes, category_id, current_stock, min_stock, unit, location)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """, (
                    item_id,
                    item_data['name'],
                    item_data.get('barcodes', []),
                    item_data['category'],
                    item_data['current_stock'],
                    item_data['min_stock'],
                    item_data['unit'],
                    item_data.get('location', '')
                ))
                conn.commit()
                return item_id
    
    def update_item(self, item_id: str, item_data: dict) -> bool:
        """Update an existing item"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE {self._get_table_name('items')} 
                    SET name = %s, barcodes = %s, category_id = %s, current_stock = %s, 
                        min_stock = %s, unit = %s, location = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    item_data['name'],
                    item_data.get('barcodes', []),
                    item_data['category'],
                    item_data['current_stock'],
                    item_data['min_stock'],
                    item_data['unit'],
                    item_data.get('location', ''),
                    item_id
                ))
                conn.commit()
                return cur.rowcount > 0
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {self._get_table_name('items')} WHERE id = %s", (item_id,))
                conn.commit()
                return cur.rowcount > 0
    
    def add_barcode_to_item(self, item_id: str, barcode: str) -> bool:
        """Add a barcode to an item"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if barcode already exists
                cur.execute(f"SELECT id FROM {self._get_table_name('items')} WHERE %s = ANY(barcodes)", (barcode,))
                if cur.fetchone():
                    return False
                
                # Add barcode
                cur.execute(f"""
                    UPDATE {self._get_table_name('items')} 
                    SET barcodes = array_append(barcodes, %s), updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (barcode, item_id))
                conn.commit()
                return cur.rowcount > 0
    
    def remove_barcode_from_item(self, item_id: str, barcode: str) -> bool:
        """Remove a barcode from an item"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE {self._get_table_name('items')} 
                    SET barcodes = array_remove(barcodes, %s), updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (barcode, item_id))
                conn.commit()
                return cur.rowcount > 0
    
    def create_transaction(self, transaction_data: dict) -> str:
        """Create a new transaction"""
        transaction_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create transaction
                cur.execute(f"""
                    INSERT INTO {self._get_table_name('transactions')} (id, item_id, type, quantity, notes)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    transaction_id,
                    transaction_data['item_id'],
                    transaction_data['type'],
                    transaction_data['quantity'],
                    transaction_data['notes']
                ))
                
                # Update item stock
                if transaction_data['type'] == 'restock':
                    cur.execute(f"""
                        UPDATE {self._get_table_name('items')} 
                        SET current_stock = current_stock + %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (transaction_data['quantity'], transaction_data['item_id']))
                else:  # usage
                    cur.execute(f"""
                        UPDATE {self._get_table_name('items')} 
                        SET current_stock = GREATEST(0, current_stock - %s), updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (transaction_data['quantity'], transaction_data['item_id']))
                
                conn.commit()
                return transaction_id
    
    def get_transactions(self):
        """Get all transactions with item names"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"""
                    SELECT t.*, i.name as item_name
                    FROM {self._get_table_name('transactions')} t
                    JOIN {self._get_table_name('items')} i ON t.item_id = i.id
                    ORDER BY t.created_at DESC
                """)
                transactions = []
                for row in cur.fetchall():
                    transaction = dict(row)
                    transaction['timestamp'] = transaction['created_at'].isoformat()
                    transactions.append(transaction)
                return transactions
    
    def get_low_stock_items(self):
        """Get items that are running low on stock"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"""
                    SELECT i.*, c.name as category_name 
                    FROM {self._get_table_name('items')} i 
                    JOIN {self._get_table_name('categories')} c ON i.category_id = c.id 
                    WHERE i.current_stock <= i.min_stock
                    ORDER BY i.name
                """)
                items = []
                for row in cur.fetchall():
                    item = dict(row)
                    item['category'] = item['category_id']
                    item['last_updated'] = item['updated_at'].isoformat() if item['updated_at'] else None
                    items.append(item)
                return items
    
    # ==================== PROJECT METHODS ====================
    
    def get_projects(self):
        """Get all projects"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"""
                    SELECT * FROM {self._get_table_name('projects')}
                    ORDER BY expiry_date ASC, name
                """)
                projects = []
                for row in cur.fetchall():
                    project = dict(row)
                    project['start_date'] = project['start_date'].isoformat() if project['start_date'] else None
                    project['ready_date'] = project['ready_date'].isoformat() if project['ready_date'] else None
                    project['expiry_date'] = project['expiry_date'].isoformat() if project['expiry_date'] else None
                    project['created_at'] = project['created_at'].isoformat() if project['created_at'] else None
                    project['updated_at'] = project['updated_at'].isoformat() if project['updated_at'] else None
                    projects.append(project)
                return projects
    
    def get_project_by_id(self, project_id: str):
        """Get a single project by ID"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"""
                    SELECT * FROM {self._get_table_name('projects')}
                    WHERE id = %s
                """, (project_id,))
                row = cur.fetchone()
                if row:
                    project = dict(row)
                    project['start_date'] = project['start_date'].isoformat() if project['start_date'] else None
                    project['ready_date'] = project['ready_date'].isoformat() if project['ready_date'] else None
                    project['expiry_date'] = project['expiry_date'].isoformat() if project['expiry_date'] else None
                    project['created_at'] = project['created_at'].isoformat() if project['created_at'] else None
                    project['updated_at'] = project['updated_at'].isoformat() if project['updated_at'] else None
                    return project
                return None
    
    def create_project(self, project_data: dict) -> str:
        """Create a new project"""
        project_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self._get_table_name('projects')} 
                    (id, name, type, start_date, ready_date, expiry_date, status, location, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    project_id,
                    project_data['name'],
                    project_data['type'],
                    project_data['start_date'],
                    project_data.get('ready_date'),
                    project_data.get('expiry_date'),
                    project_data.get('status', 'active'),
                    project_data.get('location', ''),
                    project_data.get('notes', '')
                ))
                conn.commit()
                return project_id
    
    def update_project(self, project_id: str, project_data: dict) -> bool:
        """Update an existing project"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE {self._get_table_name('projects')} 
                    SET name = %s, type = %s, start_date = %s, ready_date = %s, expiry_date = %s, 
                        status = %s, location = %s, notes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    project_data['name'],
                    project_data['type'],
                    project_data['start_date'],
                    project_data.get('ready_date'),
                    project_data.get('expiry_date'),
                    project_data['status'],
                    project_data.get('location', ''),
                    project_data.get('notes', ''),
                    project_id
                ))
                conn.commit()
                return cur.rowcount > 0
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {self._get_table_name('projects')} WHERE id = %s", (project_id,))
                conn.commit()
                return cur.rowcount > 0
    
    def get_expiring_projects(self, days: int = 7):
        """Get projects expiring within specified days"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"""
                    SELECT * FROM {self._get_table_name('projects')}
                    WHERE status = 'active' 
                    AND expiry_date <= CURRENT_DATE + INTERVAL '%s days'
                    AND expiry_date >= CURRENT_DATE
                    ORDER BY expiry_date ASC
                """, (days,))
                projects = []
                for row in cur.fetchall():
                    project = dict(row)
                    project['start_date'] = project['start_date'].isoformat() if project['start_date'] else None
                    project['expiry_date'] = project['expiry_date'].isoformat() if project['expiry_date'] else None
                    project['created_at'] = project['created_at'].isoformat() if project['created_at'] else None
                    project['updated_at'] = project['updated_at'].isoformat() if project['updated_at'] else None
                    projects.append(project)
                return projects
    
    def get_expired_projects(self):
        """Get projects that have expired"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"""
                    SELECT * FROM {self._get_table_name('projects')}
                    WHERE status = 'active' AND expiry_date < CURRENT_DATE
                    ORDER BY expiry_date DESC
                """)
                projects = []
                for row in cur.fetchall():
                    project = dict(row)
                    project['start_date'] = project['start_date'].isoformat() if project['start_date'] else None
                    project['expiry_date'] = project['expiry_date'].isoformat() if project['expiry_date'] else None
                    project['created_at'] = project['created_at'].isoformat() if project['created_at'] else None
                    project['updated_at'] = project['updated_at'].isoformat() if project['updated_at'] else None
                    projects.append(project)
                return projects