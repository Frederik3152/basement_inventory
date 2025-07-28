# Basement Inventory Manager - Complete Documentation

A modern, comprehensive inventory management application designed for tracking basement storage items with PostgreSQL database integration, barcode scanning, and real-time management capabilities.

## 📋 Table of Contents

- [Quick Start Guide](./QUICK_START.md)
- [Installation & Setup](./INSTALLATION.md)
- [Database Configuration](./DATABASE.md)
- [API Documentation](./API.md)
- [User Guide](./USER_GUIDE.md)
- [Development Guide](./DEVELOPMENT.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Deployment Guide](./DEPLOYMENT.md)

## 🚀 Overview

The Basement Inventory Manager is a full-stack web application that provides:

- **PostgreSQL Database Integration**: Persistent storage with schema support
- **Multi-Barcode Support**: Handle multiple barcodes per item
- **Real-time Barcode Scanning**: Use your phone camera for quick item identification
- **Category Management**: Organize items into logical categories
- **Stock Tracking**: Monitor inventory levels with low-stock alerts
- **Transaction History**: Complete audit trail of all inventory movements
- **Modern Web Interface**: Responsive design that works on all devices
- **RESTful API**: Complete REST API for programmatic access

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Frontend      │◄──►│   Flask API     │◄──►│   PostgreSQL    │
│   (HTML/JS)     │    │   (Python)      │    │   Database      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
    Browser                  API Server              Network DB
  Barcode Scanner           REST Endpoints           Schema Support
```

## ✨ Key Features

### Database Integration
- **PostgreSQL Support**: Full PostgreSQL database integration
- **Schema Support**: Configure custom database schemas
- **Network Database**: Connect to PostgreSQL on remote servers
- **Automatic Setup**: Tables and schemas created automatically
- **Data Persistence**: All data permanently stored

### Inventory Management
- **Multi-Barcode Items**: Support multiple barcodes per item
- **Category Organization**: Pre-configured categories with custom support
- **Stock Tracking**: Current stock, minimum levels, and units
- **Location Tracking**: Physical location information
- **Real-time Updates**: Instant UI updates on all changes

### Barcode Scanning
- **Camera Integration**: Use device camera for barcode scanning
- **Multiple Format Support**: QR codes, UPC, EAN, and more
- **Quick Item Lookup**: Instant item identification
- **Add New Items**: Create items directly from scanned barcodes

### Transaction Management
- **Stock Operations**: Restock and usage transactions
- **Complete History**: Full audit trail of all movements
- **Quantity Tracking**: Precise quantity management
- **Notes Support**: Add context to each transaction

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Python Flask | REST API server |
| **Database** | PostgreSQL | Data persistence |
| **Frontend** | HTML5/CSS3/JavaScript | User interface |
| **Styling** | Bootstrap 5 | Responsive design |
| **Barcode** | HTML5-QRCode | Camera barcode scanning |
| **Icons** | Bootstrap Icons | UI iconography |
| **Database Driver** | psycopg2 | PostgreSQL connectivity |

## 📦 Installation Overview

1. **Clone/Download** the project files
2. **Install Dependencies** using pip
3. **Configure Database** connection in `.env`
4. **Run Application** with Python
5. **Access Interface** via web browser

> See [Installation Guide](./INSTALLATION.md) for detailed steps.

## 🗄️ Database Schema

The application uses a PostgreSQL database with the following schema:

```sql
-- Categories table
home_inventory.categories (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
)

-- Items table  
home_inventory.items (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    barcodes TEXT[],
    category_id VARCHAR(50) REFERENCES categories(id),
    current_stock INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 0,
    unit VARCHAR(50) NOT NULL,
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Transactions table
home_inventory.transactions (
    id VARCHAR(36) PRIMARY KEY,
    item_id VARCHAR(36) REFERENCES items(id) ON DELETE CASCADE,
    type VARCHAR(20) CHECK (type IN ('restock', 'usage')),
    quantity INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## 🔧 Configuration

The application is configured via environment variables in the `.env` file:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database
DATABASE_SCHEMA=home_inventory
```

## 📱 Usage Examples

### Adding a New Item
1. Click "Add Item" button
2. Fill in item details (name, category, stock)
3. Add multiple barcodes if needed
4. Save to database

### Scanning a Barcode
1. Click "Scan Barcode" 
2. Allow camera access
3. Point camera at barcode
4. Item automatically identified or create new

### Managing Stock
1. Find item in inventory
2. Click "Restock" or "Use" buttons
3. Enter quantity and notes
4. Transaction recorded automatically

## 🔍 API Overview

The application provides a complete REST API:

```
GET    /api/items                    # Get all items
POST   /api/items                    # Create new item
PUT    /api/items/{id}               # Update item
DELETE /api/items/{id}               # Delete item
GET    /api/items/barcode/{barcode}  # Find by barcode
POST   /api/items/{id}/barcodes      # Add barcode
DELETE /api/items/{id}/barcodes/{bc} # Remove barcode
GET    /api/categories               # Get categories
GET    /api/transactions             # Get transaction history
POST   /api/transactions             # Create transaction
GET    /api/low-stock                # Get low stock items
```

## 🚀 Getting Started

1. **Read the [Quick Start Guide](./QUICK_START.md)** for immediate setup
2. **Follow the [Installation Guide](./INSTALLATION.md)** for detailed setup
3. **Configure your [Database](./DATABASE.md)** connection
4. **Explore the [User Guide](./USER_GUIDE.md)** for feature walkthroughs
5. **Check [Troubleshooting](./TROUBLESHOOTING.md)** if you encounter issues

## 📞 Support

- Check the [Troubleshooting Guide](./TROUBLESHOOTING.md) for common issues
- Review the [API Documentation](./API.md) for integration questions
- See the [Development Guide](./DEVELOPMENT.md) for customization

## 📄 License

MIT License - Feel free to use and modify for your personal or commercial needs.

---

*This documentation covers the complete Basement Inventory Manager system with PostgreSQL database integration. Each linked document provides detailed information for specific aspects of the system.*
