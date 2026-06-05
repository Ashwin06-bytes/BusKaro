# BusKaro 🚌

**BusKaro** is a unified, real-time bus ticket aggregator, booking, and tracking system built with Django. It provides a comprehensive solution for passengers to find and book bus tickets across multiple operators (internal and external), track buses in real time, and for conductors and administrators to manage routes, tickets, schedules, and analytics.

---

## 🌟 Key Features

### 1. 🔍 Unified Bus Aggregation (`aggregator` & `search`)
*   **Concurrent Searching**: Queries internal bus schedules and mocks external services (like TNSTC, RedBus, AbhiBus) concurrently using Python's `ThreadPoolExecutor`.
*   **Smart Caching**: Implements Django's cache framework to cache search results and optimize performance.
*   **Search Logging**: Logs searches into the database for future analytics.
*   **Sort & Filters**: Searches can be filtered by route, departure time, and bus type, with automatic sorting by price.

### 2. ⚡ Tatkal Booking System (`tatkal` & `inventory`)
*   **Dynamic Windows**: Opens a tatkal booking window before the journey departs (configurable, default is 2 hours).
*   **Surcharges**: Automatically applies operator-specific or default surcharges (e.g., 25% extra) during the active tatkal window.
*   **Allocation**: Controls seat allocations specifically designated for tatkal travelers.

### 3. 🎫 Booking & Ticketing (`bookings`, `tickets`, & `payments`)
*   **Mock Razorpay Integration**: Standardized workflow for initiating payments, verifying payment signatures, and issuing tickets.
*   **QR-Coded Tickets**: Automatically generates a unique QR code image for every successfully booked ticket.
*   **PDF Downloads**: Uses `ReportLab` to compile print-ready ticket PDFs containing journey details, passenger metadata, and the QR code.
*   **Easy Cancellations**: Allows passengers to cancel tickets for long-route buses (GOVT/PRIVATE) with automatic refund initiation on Razorpay (or mock refund for local testing).

### 4. 🛰️ Real-Time Location Tracking (`tracking`)
*   **WebSockets via Django Channels**: Daphne-powered WebSocket consumers connect passengers and conductors in real time.
*   **Conductor Broadcasts**: Conductor submits coordinates from the bus, which are instantly broadcast to passengers tracking the trip via map coordinates.

### 5. 🧑‍✈️ Conductor Operations Dashboard (`conductors`)
*   **Bus Management**: Conductors log in to designate their active bus.
*   **QR Validation**: Conductor can scan passenger QR codes or submit the ticket UUID to verify legitimacy, check-in passengers, and automatically transition ticket states.
*   **Trip Termination**: Marks all active passenger tickets as `EXPIRED` once the route is completed.

### 6. 📊 Sysadmin Dashboard & Reports (`sysadmin`)
*   **Revenue & Traffic Charts**: High-level metrics showing passenger flow, total tickets, and bus-wise revenue.
*   **Data Exports**: Administrators can filter ticket sales by date range and export reports to **CSV** or styled **PDF** tables.
*   **Inventory Control**: Tools to add/remove buses, register conductors, generate static scan URLs/QR codes for buses, and monitor active Tatkal quotas.

---

## 🏗️ Architecture & Technology Stack

*   **Backend Framework**: [Django 4.2](https://www.djangoproject.com/)
*   **Asynchronous Support**: [Daphne](https://github.com/django/daphne/) & [Django Channels](https://channels.readthedocs.io/en/stable/) for WebSocket connections.
*   **Database**: SQLite (default for development), PostgreSQL-compatible via `dj-database-url`.
*   **Payment Gateway**: Razorpay API (Mocked during development).
*   **Document & Asset Generation**:
    *   `qrcode` (PIL) for generating validation QR codes.
    *   `reportlab` for compiling PDF invoices/tickets and admin reports.
*   **Frontend**: Vanilla HTML5 templates, Tailwind/Custom CSS, and JavaScript.

---

## 📁 Repository Structure

```text
├── aggregator/         # Multi-provider bus search engine & external adapters
├── bookings/           # Handles user reservations, seat inventory holds, and states
├── bus_ticket/         # Core project settings, main URL routes, and WSGI/ASGI entrypoints
├── conductors/         # Conductor dashboard, QR ticket checking, and session control
├── inventory/          # Seat definitions, layout types (2x2, 2x3, sleeper), and schedules
├── operators/          # Bus operators profile database
├── passengers/         # Passenger authentication, register/login, and home portals
├── payments/           # Razorpay order creation and webhook/verification views
├── routes/             # Routes, Stops, Bus profiles, and fare distance matrices
├── search/             # UI search views for routes and stops
├── static/             # Global CSS and Javascript static files
├── sysadmin/           # Admin panel, CSV/PDF reports export, and bus registration
├── tatkal/             # Tatkal window calculation and surcharge rates
├── templates/          # Global HTML templates structure
├── tickets/            # PDF and QR generation, cancellation logic, and ticket model
├── tracking/           # WebSockets consumers and location broadcast endpoints
├── manage.py           # Django administrative utility script
├── requirements.txt    # Project dependencies
└── .env.example        # Environment variables template file
```

---

## 🚀 Getting Started

### 📋 Prerequisites
*   Python 3.10+
*   pip / virtualenv

### ⚙️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd BusKaro
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Copy `.env.example` to `.env` and fill in the details:
    ```bash
    cp .env.example .env
    ```
    Configure:
    *   `SECRET_KEY`: A unique secret key for Django.
    *   `DEBUG`: Set to `True` for development, `False` for production.
    *   `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`: Razorpay keys (can be dummy keys for testing).

5.  **Run Database Migrations**
    ```bash
    python manage.py migrate
    ```

6.  **Create a Superuser (Administrator)**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Start the Server**
    Run the development server with ASGI enabled:
    ```bash
    python manage.py runserver
    ```
    Alternatively, use `daphne`:
    ```bash
    daphne -b 127.0.0.1 -p 8000 bus_ticket.asgi:application
    ```

    Open your browser and navigate to `http://127.0.0.1:8000/`.

---

## 🧪 How to Test

### 1. Searching & Booking
*   Visit `http://127.0.0.1:8000/` and search for routes.
*   Log in or register as a passenger using a phone number.
*   Pick a bus, select your stops, and make a simulated booking.
*   View your generated ticket with its QR code and download it as a PDF.

### 2. Conductor Dashboard
*   Log in to `http://127.0.0.1:8000/conductor/login/`.
*   Assign the conductor to an active bus.
*   Use the dashboard to verify tickets by typing the Ticket ID or submitting QR scan events.
*   Update the live location coordinates to trigger live passenger-tracking broadcasts.

### 3. Sysadmin Portal
*   Visit `http://127.0.0.1:8000/sysadmin/` (log in using your Django superuser credentials).
*   Monitor revenue streams, register new buses/conductors, configure Tatkal windows, and export PDF/CSV revenue sheets.
