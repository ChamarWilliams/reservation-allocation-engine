# High-Concurrency Inventory & Allocation Engine

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

A production-grade, containerized transactional reservation and checkout service built to eliminate overselling during high-concurrency traffic spikes (e.g., flash sales, event ticket drops, and limited resource allocations).

---

## Architecture Overview

```text
                  +-----------------------------+
                  |   React + TypeScript UI     |
                  |  (Vite, Hooks, Status Poll) |
                  +--------------+--------------+
                                 |
                                 | JSON / REST
                                 v
                  +-----------------------------+
                  |       FastAPI Backend       |
                  |  (Pydantic, Asyncpg, Pool)  |
                  +--------------+--------------+
                                 |
                                 | Transactional Queries
                                 | (SELECT ... FOR UPDATE)
                                 v
                  +-----------------------------+
                  |       PostgreSQL 16         |
                  |   (ACID, Row-Level Locks)   |
                  +-----------------------------+
```

---

## Core Engineering Problem Solved

Under simultaneous checkout requests for limited stock, naive read-then-write logic introduces race conditions: multiple requests read the same remaining balance and all decrement it, driving inventory into negative numbers.

This engine guarantees inventory consistency through:

* **Pessimistic Row-Level Locking:** Acquiring a `SELECT ... FOR UPDATE` lock within an atomic transaction block so concurrent writes wait in an orderly queue.
* **Strict DB Constraints:** Enforcing PostgreSQL `CHECK (total_stock >= 0)` constraints as a hard fallback to protect transactional boundaries.
* **Defensive API Responses:** Returning clean `409 Conflict` payloads when inventory is exhausted instead of throwing unhandled exceptions or corrupting data.

---

## Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.11, FastAPI, Pydantic v2 | High-performance asynchronous REST API & schema validation |
| **Database** | PostgreSQL 16 (via Asyncpg / SQLAlchemy) | Relational modeling, ACID transactions, and row-level locking |
| **Testing** | pytest, pytest-asyncio, httpx | Automated concurrency stress tests and regression suites |
| **Frontend** | React 18, TypeScript, Vite | Client UI with real-time optimistic state and error handling |
| **DevOps** | Docker, Docker Compose | Isolated multi-container local runtime and networking |

---

## Database Schema

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(150) NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    total_stock INTEGER NOT NULL CHECK (total_stock >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'CONFIRMED',
    total_cents INTEGER NOT NULL CHECK (total_cents >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    CONSTRAINT unique_order_product UNIQUE (order_id, product_id)
);

CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
```

---

## Quickstart

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) & Docker Compose

### 1. Clone & Launch Services
```bash
git clone https://github.com/your-username/inventory-engine.git
cd inventory-engine
docker compose up --build
```

### 2. Access the Application
* **Interactive API Documentation (Swagger):** `http://localhost:8000/docs`
* **Web Client Dashboard:** `http://localhost:3000`
* **PostgreSQL Database:** `localhost:5432`

---

## Running the Automated Test Suite

The integration test suite validates schema constraints, Pydantic input payloads, and concurrent load behaviors.

Run the test suite directly inside the running API container:

```bash
docker compose exec api pytest -v
```

### Verified Test Scenarios
1. **Input Validation:** Verifies that malformed payloads or invalid emails return HTTP `422 Unprocessable Entity`.
2. **Atomic Deductions:** Verifies that a valid checkout creates an order and atomically decrements product stock by the exact requested amount.
3. **Out-of-Stock Handling:** Verifies that attempting to purchase more units than available returns HTTP `409 Conflict`.
4. **Concurrency Race Conditions:** Launches simultaneous async checkout requests against a single inventory item to prove zero double-booking occurs.

---

## Project Structure

```text
inventory-engine/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers and endpoints
│   │   ├── core/         # DB connection setup and configuration
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   └── main.py       # FastAPI application entrypoint
│   ├── tests/            # pytest integration and concurrency tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/              # React components and dashboard UI
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```