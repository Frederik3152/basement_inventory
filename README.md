# Basement Inventory Manager

A Flask-based web application for managing home inventory with barcode scanning and stock tracking capabilities.

## Features

- **Barcode Scanning**: Camera-based barcode scanning for quick item identification
- **Stock Management**: Track current stock levels with automatic low-stock alerts
- **Multi-location Support**: Organize items by storage location (Box 1, Box 2, etc.)
- **Transaction History**: Complete audit trail of restocks and usage
- **REST API**: Full API for programmatic integration
- **Responsive Design**: Mobile-friendly interface

## Quick Start

### Prerequisites

- Docker and Docker Compose
- PostgreSQL database
- SSL certificates (for camera access)

### Deployment

1. **Clone the repository**
   ```bash
   git clone https://github.com/Frederik3152/basement_inventory.git
   cd basement_inventory
   ```

2. **Set up environment**
   Create a `.env` file:
   ```env
   DATABASE_URL=postgresql://username:password@host:port/database
   DATABASE_SCHEMA=pi_data
   ```

3. **Prepare SSL certificates**
   Place your SSL certificate files in the project directory:
   - `server.crt` - SSL certificate
   - `server.key` - Private key
   
   *Note: HTTPS is required for camera access on modern browsers*

4. **Deploy with Docker**
   ```bash
   docker build -t basement-inventory .
   docker run -d -p 443:443 \
     --env-file .env \
     -v $(pwd)/server.crt:/app/server.crt \
     -v $(pwd)/server.key:/app/server.key \
     basement-inventory
   ```

5. **Access the application**
   Open your browser to `https://your-server-ip`

## API Endpoints

### Core Operations
- `GET /api/items` - List all items
- `POST /api/items` - Create item
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item
- `GET /api/items/barcode/{barcode}` - Find by barcode

### Stock Management
- `POST /api/transactions` - Record stock transaction
- `GET /api/low-stock` - Get low-stock items

### Organization
- `GET /box/{1-4}` - Filter items by storage box
- `GET /api/categories` - List categories

## Database Schema

The application automatically creates the required PostgreSQL tables:

- **Items**: Core inventory with barcodes, stock levels, and locations
- **Categories**: Item categorization
- **Transactions**: Stock movement history (restock/usage)

## Technology Stack

- **Backend**: Flask (Python 3.11)
- **Database**: PostgreSQL
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Barcode**: HTML5-QRCode library
- **Deployment**: Docker with SSL support

## License

MIT License