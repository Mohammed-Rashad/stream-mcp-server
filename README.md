# Stream MCP Server

An [MCP](https://modelcontextprotocol.io/) server for the **Stream** (streampay.sa) payment platform, built with [FastMCP](https://github.com/jlowin/fastmcp).

Exposes **27 tools** across six resource domains — payment links, customers, products, coupons, invoices, and payments — plus a read-only OpenAPI documentation resource.

---

## Quick Start

### 1. Install

```bash
# Clone & install in editable mode
git clone <repo-url> stream-mcp-server && cd stream-mcp-server
pip install -e ".[dev]"
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your Stream API key:
#   STREAM_API_KEY=sk_live_…
```

| Variable | Default | Description |
|---|---|---|
| `STREAM_API_KEY` | *(required)* | Your Stream API key |
| `STREAM_BASE_URL` | `https://stream-app-service.streampay.sa` | API base URL |
| `STREAM_TIMEOUT` | `30` | Request timeout (seconds) |
| `STREAM_MAX_RETRIES` | `2` | Retry count for 429 / 5xx |

### 3. Run

```bash
# stdio transport (default — for Claude Desktop / Cline)
stream-mcp

# SSE transport (for web-based agents)
stream-mcp --transport sse --port 8000
```

---

## Claude Desktop Integration

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "stream": {
      "command": "stream-mcp",
      "env": {
        "STREAM_API_KEY": "your_key_here"
      }
    }
  }
}
```

---

## Available Tools

### Payment Links
| Tool | Description |
|---|---|
| `create_payment_link` | Create a new checkout / payment link |
| `list_payment_links` | Paginated list with optional status filter |
| `get_payment_link` | Get a single payment link by ID |
| `deactivate_payment_link` | Deactivate / archive a payment link |

### Customers
| Tool | Description |
|---|---|
| `create_customer` | Create a customer with name, email, phone, metadata |
| `list_customers` | Paginated list of customers |
| `get_customer` | Get a single customer by ID |
| `update_customer` | Update customer fields |
| `delete_customer` | Soft-delete a customer |

### Products
| Tool | Description |
|---|---|
| `create_product` | Create a one-time or recurring product |
| `list_products` | List products with optional type filter |
| `get_product` | Get a single product by ID |
| `update_product` | Update product name, description, or price |
| `archive_product` | Archive a product |

### Coupons
| Tool | Description |
|---|---|
| `create_coupon` | Create a fixed or percentage discount coupon |
| `list_coupons` | List coupons with optional status filter |
| `get_coupon` | Get a single coupon by ID |
| `deactivate_coupon` | Deactivate a coupon |

### Invoices
| Tool | Description |
|---|---|
| `create_invoice` | Create a ZATCA-compliant invoice |
| `list_invoices` | List invoices with filters |
| `get_invoice` | Get a single invoice by ID |
| `send_invoice` | (Re)send an invoice via email / SMS |
| `void_invoice` | Void / cancel an unpaid invoice |

### Payments
| Tool | Description |
|---|---|
| `list_payments` | List payments with filters |
| `get_payment` | Get payment details |
| `refund_payment` | Issue a full or partial refund |

### Resources
| Resource URI | Description |
|---|---|
| `stream://docs/openapi` | Full Stream OpenAPI spec (cached, auto-refreshed) |

---

## Project Structure

```
src/stream_mcp/
├── server.py          # FastMCP app entry-point
├── config.py          # Settings from env vars
├── client.py          # Async HTTP client (auth, retries, errors)
├── models/            # Pydantic v2 request/response models
│   ├── payment_links.py
│   ├── customers.py
│   ├── products.py
│   ├── coupons.py
│   ├── invoices.py
│   └── payments.py
└── tools/             # FastMCP tool definitions
    ├── __init__.py    # Registers all tools
    ├── payment_links.py
    ├── customers.py
    ├── products.py
    ├── coupons.py
    ├── invoices.py
    ├── payments.py
    └── docs.py        # OpenAPI resource
```

**Adding a new resource domain** = add one file in `models/`, one in `tools/`, and one import line in `tools/__init__.py`.

---

## Error Handling

All tools catch `StreamAPIError` and return a structured dict instead of raising:

```json
{
  "error": true,
  "code": 422,
  "message": "Validation failed: …"
}
```

This ensures the LLM agent always receives a usable response.

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

---

## License

MIT
