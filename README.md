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
| `STREAM_API_KEY` | *(required for stdio mode)* | Your Stream API key |
| `STREAM_BASE_URL` | `https://stream-app-service.streampay.sa` | API base URL |
| `STREAM_TIMEOUT` | `30` | Request timeout (seconds) |
| `STREAM_MAX_RETRIES` | `2` | Retry count for 429 / 5xx |

### 3. Run

#### Local stdio mode (recommended)

```bash
stream-mcp
```

#### Remote HTTP mode (URL clients)

```bash
# No STREAM_API_KEY needed on the server process in remote mode
HOST=0.0.0.0 PORT=8000 stream-mcp-remote
```

Endpoint:

```text
http://localhost:8000/sse
```

---

## MCP Client Configuration (Claude Desktop / Cursor / VS Code)

Use one of these two patterns in your MCP config file (`claude_desktop_config.json` or `mcp.json`).

### Option A: stdio

```json
{
  "mcpServers": {
    "stream": {
      "command": "stream-mcp",
      "env": {
        "STREAM_API_KEY": "sk_live_your_key_here"
      }
    }
  }
}
```

### Option B: remote URL (`stream-mcp-remote`)

```json
{
  "mcpServers": {
    "stream": {
      "url": "http://localhost:8000/sse",
      "headers": {
        "Authorization": "Bearer sk_live_your_key_here"
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

## Remote Deployment (Hosted URL)

You can deploy the MCP server as a **hosted URL** so users connect to it remotely.

Each user passes their own Stream API key as a Bearer token.

### 1. Run locally (remote mode)

```bash
# No STREAM_API_KEY needed — each user provides their own
stream-mcp-remote
# → Listening on http://0.0.0.0:8000

# Custom host/port
HOST=0.0.0.0 PORT=3000 stream-mcp-remote
```

### 2. Deploy with Docker

```bash
docker build -t stream-mcp .
docker run --rm -p 8000:8000 stream-mcp
```

### 3. How users connect (remote)

Users add this to their MCP client config:

**Claude Desktop / VS Code:**
```json
{
  "mcpServers": {
    "stream": {
      "url": "https://your-domain.com/sse",
      "headers": {
        "Authorization": "Bearer sk_live_YOUR_STREAM_API_KEY"
      }
    }
  }
}
```

> Each user passes their **own** Stream API key as the Bearer token.
> The server never stores keys — they are used only for the duration of the session.

---

## Project Structure

```
src/stream_mcp/
├── server.py          # FastMCP app entry-point (local + remote modes)
├── config.py          # Settings from env vars
├── client.py          # Async HTTP client (auth, retries, errors)
├── auth.py            # Bearer token middleware (remote mode)
├── helpers.py         # get_client() — resolves per-request StreamClient
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
