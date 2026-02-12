# API Documentation - Aureon SaaS Platform

**Version**: 2.3.0
**Base URL**: `https://aureon.rhematek-solutions.com/api/`
**Last Updated**: February 12, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Authentication Endpoints](#authentication-endpoints)
6. [Client Endpoints](#client-endpoints)
7. [Contract Endpoints](#contract-endpoints)
8. [Invoice Endpoints](#invoice-endpoints)
9. [Payment Endpoints](#payment-endpoints)
10. [Analytics Endpoints](#analytics-endpoints)
11. [Webhook Endpoints](#webhook-endpoints)
12. [Common Response Codes](#common-response-codes)

---

## Overview

### API Base URLs

| Environment | URL |
|-------------|-----|
| Production | `https://aureon.rhematek-solutions.com/api/` |
| Development | `http://localhost:8001/api/` |

### Interactive Documentation

| Documentation | URL |
|---------------|-----|
| Swagger UI | `/api/docs/` |
| ReDoc | `/api/redoc/` |
| OpenAPI Schema | `/api/schema/` |

### Request Format

All API requests should:
- Use HTTPS in production
- Include `Content-Type: application/json` for POST/PUT/PATCH
- Include `Authorization: Bearer <token>` for authenticated endpoints

### Response Format

All API responses are JSON with this structure:

```json
{
    "data": { ... },         // Response data (for success)
    "error": "message",      // Error message (for errors)
    "detail": "message",     // Alternative error format
    "count": 100,            // Total count (for lists)
    "next": "url",           // Next page URL (for pagination)
    "previous": "url",       // Previous page URL (for pagination)
    "results": [ ... ]       // List of items (for lists)
}
```

---

## Authentication

### JWT Token Authentication

Aureon uses JWT (JSON Web Tokens) for API authentication.

#### Token Lifecycle

| Token Type | Lifetime | Usage |
|------------|----------|-------|
| Access Token | 15 minutes | API requests |
| Refresh Token | 7 days | Obtain new access tokens |

#### Authentication Flow

```
1. Login to obtain tokens
   POST /api/auth/login/

2. Include access token in requests
   Authorization: Bearer eyJ0eXAiOiJKV1...

3. Refresh token when expired
   POST /api/auth/token/refresh/
```

#### Example: Authenticate and Use API

```bash
# Step 1: Login
curl -X POST https://aureon.rhematek-solutions.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password"}'

# Response:
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

# Step 2: Use access token
curl -X GET https://aureon.rhematek-solutions.com/api/api/clients/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Step 3: Refresh token when needed
curl -X POST https://aureon.rhematek-solutions.com/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}'
```

---

## Error Handling

### Error Response Format

```json
{
    "detail": "Error message here",
    "code": "error_code",
    "field_errors": {
        "email": ["This field is required."],
        "password": ["Password too short."]
    }
}
```

### Common Error Codes

| HTTP Code | Error | Description |
|-----------|-------|-------------|
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

### Rate Limits

| User Type | Limit | Period |
|-----------|-------|--------|
| Anonymous | 100 | per hour |
| Authenticated | 1000 | per hour |

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1703894400
```

### Rate Limit Exceeded Response

```json
HTTP 429 Too Many Requests
{
    "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

---

## Authentication Endpoints

### POST /api/auth/login/

Login and obtain JWT tokens.

**Request:**
```json
{
    "email": "user@example.com",
    "password": "your-password"
}
```

**Response (Success):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "admin"
    }
}
```

**Response (2FA Required):**
```json
{
    "requires_2fa": true,
    "message": "Two-factor authentication required"
}
```

---

### POST /api/auth/register/

Register a new user account.

**Request:**
```json
{
    "email": "newuser@example.com",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "first_name": "Jane",
    "last_name": "Doe"
}
```

**Response:**
```json
{
    "id": 2,
    "email": "newuser@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "message": "Registration successful. Please verify your email."
}
```

---

### POST /api/auth/token/refresh/

Refresh access token using refresh token.

**Request:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### GET /api/auth/user/

Get current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "admin",
    "tenant": {
        "id": 1,
        "name": "Acme Corp"
    },
    "is_2fa_enabled": true
}
```

---

### POST /api/auth/2fa/enable/

Start 2FA setup process.

**Response:**
```json
{
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code": "data:image/png;base64,...",
    "provisioning_uri": "otpauth://totp/Aureon:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Aureon"
}
```

---

### POST /api/auth/2fa/verify-setup/

Complete 2FA setup by verifying TOTP code.

**Request:**
```json
{
    "code": "123456"
}
```

**Response:**
```json
{
    "message": "Two-factor authentication enabled successfully",
    "backup_codes": [
        "ABCD-1234-EFGH",
        "IJKL-5678-MNOP",
        ...
    ]
}
```

---

### POST /api/auth/2fa/verify/

Verify 2FA code during login.

**Request:**
```json
{
    "code": "123456"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## Client Endpoints

### GET /api/api/clients/

List all clients with filtering and pagination.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number |
| page_size | int | Items per page (default: 50) |
| search | string | Search in name, email, company |
| lifecycle_stage | string | Filter by stage (lead, prospect, active, churned) |
| is_active | boolean | Filter by active status |
| ordering | string | Sort field (-created_at, first_name, etc.) |

**Example Request:**
```bash
curl -X GET "https://aureon.rhematek-solutions.com/api/api/clients/?lifecycle_stage=active&page=1" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
    "count": 150,
    "next": "https://aureon.rhematek-solutions.com/api/api/clients/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@company.com",
            "company_name": "Smith Industries",
            "lifecycle_stage": "active",
            "total_value": "50000.00",
            "outstanding_balance": "5000.00",
            "created_at": "2025-01-15T10:30:00Z"
        },
        ...
    ]
}
```

---

### POST /api/api/clients/

Create a new client.

**Request:**
```json
{
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "phone": "+1234567890",
    "company_name": "Doe Enterprises",
    "lifecycle_stage": "lead",
    "address": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "country": "US",
    "notes": "Initial contact from website"
}
```

**Response:**
```json
{
    "id": 2,
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "phone": "+1234567890",
    "company_name": "Doe Enterprises",
    "lifecycle_stage": "lead",
    "is_active": true,
    "created_at": "2025-12-29T10:00:00Z",
    "updated_at": "2025-12-29T10:00:00Z"
}
```

---

### GET /api/api/clients/{id}/

Get client details.

**Response:**
```json
{
    "id": 1,
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@company.com",
    "phone": "+1234567890",
    "company_name": "Smith Industries",
    "lifecycle_stage": "active",
    "address": "456 Corporate Blvd",
    "city": "Los Angeles",
    "state": "CA",
    "zip_code": "90001",
    "country": "US",
    "total_value": "50000.00",
    "total_paid": "45000.00",
    "outstanding_balance": "5000.00",
    "contracts_count": 3,
    "invoices_count": 12,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-12-20T14:00:00Z"
}
```

---

### PUT /api/api/clients/{id}/

Update a client.

**Request:**
```json
{
    "first_name": "John",
    "last_name": "Smith",
    "lifecycle_stage": "active",
    "phone": "+1987654321"
}
```

---

### DELETE /api/api/clients/{id}/

Delete a client.

**Response:**
```
HTTP 204 No Content
```

---

### GET /api/api/clients/stats/

Get client statistics.

**Response:**
```json
{
    "total_clients": 150,
    "active_clients": 120,
    "leads": 15,
    "prospects": 10,
    "total_value": "750000.00",
    "total_paid": "650000.00",
    "outstanding_balance": "100000.00"
}
```

---

### POST /api/api/clients/{id}/create_portal_access/

Create portal access for a client.

**Response:**
```json
{
    "detail": "Portal access created successfully.",
    "user_id": 25,
    "email": "client@example.com"
}
```

---

## Contract Endpoints

### GET /api/api/contracts/

List all contracts.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| client | int | Filter by client ID |
| status | string | Filter by status (draft, sent, signed, active, completed) |
| search | string | Search in contract number, title |

**Response:**
```json
{
    "count": 50,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "contract_number": "CTR-2025-001",
            "title": "Web Development Agreement",
            "client": {
                "id": 1,
                "name": "John Smith"
            },
            "status": "active",
            "value": "25000.00",
            "start_date": "2025-01-01",
            "end_date": "2025-06-30",
            "completion_percentage": 60,
            "created_at": "2025-01-01T09:00:00Z"
        },
        ...
    ]
}
```

---

### POST /api/api/contracts/

Create a new contract.

**Request:**
```json
{
    "client": 1,
    "title": "Marketing Services Agreement",
    "description": "Monthly marketing services including SEO and content creation",
    "value": "5000.00",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "billing_type": "monthly",
    "terms": "Payment due within 30 days of invoice...",
    "milestones": [
        {
            "title": "Initial Setup",
            "amount": "1000.00",
            "due_date": "2025-01-15"
        },
        {
            "title": "Monthly Retainer",
            "amount": "4000.00",
            "due_date": "2025-02-01"
        }
    ]
}
```

**Response:**
```json
{
    "id": 2,
    "contract_number": "CTR-2025-002",
    "title": "Marketing Services Agreement",
    "status": "draft",
    "value": "5000.00",
    "created_at": "2025-12-29T10:00:00Z"
}
```

---

### GET /api/api/contracts/{id}/

Get contract details with milestones.

**Response:**
```json
{
    "id": 1,
    "contract_number": "CTR-2025-001",
    "title": "Web Development Agreement",
    "description": "Full website redesign and development",
    "client": {
        "id": 1,
        "first_name": "John",
        "last_name": "Smith",
        "company_name": "Smith Industries"
    },
    "status": "active",
    "value": "25000.00",
    "invoiced_amount": "15000.00",
    "paid_amount": "10000.00",
    "start_date": "2025-01-01",
    "end_date": "2025-06-30",
    "completion_percentage": 60,
    "signed_by_client": true,
    "signed_by_company": true,
    "signed_at": "2025-01-02T14:00:00Z",
    "milestones": [
        {
            "id": 1,
            "title": "Design Phase",
            "amount": "5000.00",
            "status": "completed",
            "due_date": "2025-01-31",
            "completed_at": "2025-01-28T10:00:00Z"
        },
        {
            "id": 2,
            "title": "Development Phase",
            "amount": "15000.00",
            "status": "in_progress",
            "due_date": "2025-04-30"
        },
        {
            "id": 3,
            "title": "Testing and Launch",
            "amount": "5000.00",
            "status": "pending",
            "due_date": "2025-06-30"
        }
    ],
    "created_at": "2025-01-01T09:00:00Z"
}
```

---

### POST /api/api/contracts/{id}/sign/

Sign a contract.

**Request:**
```json
{
    "party": "client",
    "signature": "data:image/png;base64,..."
}
```

**Response:**
```json
{
    "id": 1,
    "signed_by_client": true,
    "signed_by_company": false,
    "message": "Contract signed by client"
}
```

---

### GET /api/api/contracts/stats/

Get contract statistics.

**Response:**
```json
{
    "total_contracts": 50,
    "active_contracts": 30,
    "draft_contracts": 10,
    "completed_contracts": 10,
    "total_value": "500000.00",
    "total_invoiced": "350000.00",
    "total_paid": "300000.00",
    "avg_completion": 65.5
}
```

---

### POST /api/api/milestones/{id}/mark_complete/

Mark a contract milestone as complete.

**Response:**
```json
{
    "id": 2,
    "title": "Development Phase",
    "status": "completed",
    "completed_at": "2025-12-29T10:00:00Z",
    "completed_by": {
        "id": 1,
        "email": "admin@example.com"
    }
}
```

---

### POST /api/api/milestones/{id}/generate_invoice/

Generate an invoice for a milestone.

**Response:**
```json
{
    "detail": "Invoice generated successfully.",
    "invoice_id": 15,
    "invoice_number": "INV-2025-015"
}
```

---

## Invoice Endpoints

### GET /api/api/invoices/

List all invoices.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| client | int | Filter by client ID |
| contract | int | Filter by contract ID |
| status | string | Filter by status (draft, sent, paid, overdue, cancelled) |
| issue_date_after | date | Filter by issue date |
| issue_date_before | date | Filter by issue date |
| due_date_after | date | Filter by due date |
| due_date_before | date | Filter by due date |

**Response:**
```json
{
    "count": 100,
    "results": [
        {
            "id": 1,
            "invoice_number": "INV-2025-001",
            "client": {
                "id": 1,
                "name": "John Smith"
            },
            "status": "paid",
            "issue_date": "2025-01-15",
            "due_date": "2025-02-14",
            "subtotal": "5000.00",
            "tax": "500.00",
            "total": "5500.00",
            "paid_amount": "5500.00",
            "created_at": "2025-01-15T10:00:00Z"
        },
        ...
    ]
}
```

---

### POST /api/api/invoices/

Create a new invoice.

**Request:**
```json
{
    "client": 1,
    "contract": 1,
    "issue_date": "2025-12-29",
    "due_date": "2026-01-28",
    "notes": "Thank you for your business",
    "items": [
        {
            "description": "Web Development Services - December 2025",
            "quantity": 1,
            "unit_price": "5000.00"
        },
        {
            "description": "Hosting Setup",
            "quantity": 1,
            "unit_price": "500.00"
        }
    ],
    "tax_rate": 10.0
}
```

**Response:**
```json
{
    "id": 16,
    "invoice_number": "INV-2025-016",
    "status": "draft",
    "subtotal": "5500.00",
    "tax": "550.00",
    "total": "6050.00",
    "created_at": "2025-12-29T10:00:00Z"
}
```

---

### GET /api/api/invoices/{id}/

Get invoice details with items.

**Response:**
```json
{
    "id": 1,
    "invoice_number": "INV-2025-001",
    "client": {
        "id": 1,
        "first_name": "John",
        "last_name": "Smith",
        "company_name": "Smith Industries",
        "email": "john@smithind.com"
    },
    "contract": {
        "id": 1,
        "contract_number": "CTR-2025-001",
        "title": "Web Development Agreement"
    },
    "status": "paid",
    "issue_date": "2025-01-15",
    "due_date": "2025-02-14",
    "paid_date": "2025-01-20",
    "subtotal": "5000.00",
    "tax_rate": 10.0,
    "tax": "500.00",
    "total": "5500.00",
    "paid_amount": "5500.00",
    "notes": "Thank you for your business",
    "items": [
        {
            "id": 1,
            "description": "Web Development Services",
            "quantity": 1,
            "unit_price": "5000.00",
            "amount": "5000.00"
        }
    ],
    "payments": [
        {
            "id": 1,
            "amount": "5500.00",
            "payment_date": "2025-01-20",
            "payment_method": "card",
            "transaction_id": "ch_abc123"
        }
    ],
    "pdf_url": "/media/invoices/INV-2025-001.pdf",
    "created_at": "2025-01-15T10:00:00Z"
}
```

---

### POST /api/api/invoices/{id}/send/

Send invoice to client via email.

**Response:**
```json
{
    "id": 1,
    "status": "sent",
    "sent_at": "2025-12-29T10:00:00Z",
    "message": "Invoice sent successfully"
}
```

---

### POST /api/api/invoices/{id}/mark_paid/

Mark invoice as paid (manual payment).

**Request:**
```json
{
    "payment_amount": 5500.00,
    "payment_method": "bank_transfer",
    "payment_reference": "TRF-123456"
}
```

**Response:**
```json
{
    "id": 1,
    "status": "paid",
    "paid_amount": "5500.00",
    "paid_date": "2025-12-29"
}
```

---

### POST /api/api/invoices/{id}/generate_pdf/

Generate PDF for invoice.

**Response:**
```json
{
    "detail": "PDF generated successfully.",
    "pdf_url": "/media/invoices/INV-2025-001.pdf"
}
```

---

### GET /api/api/invoices/stats/

Get invoice statistics.

**Response:**
```json
{
    "total_invoices": 100,
    "draft_invoices": 5,
    "sent_invoices": 15,
    "paid_invoices": 75,
    "overdue_invoices": 5,
    "total_invoiced": "250000.00",
    "total_paid": "200000.00",
    "total_outstanding": "50000.00"
}
```

---

## Payment Endpoints

### GET /api/api/payments/

List all payments.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| invoice | int | Filter by invoice ID |
| status | string | Filter by status (pending, succeeded, failed, refunded) |
| payment_method | string | Filter by method (card, bank_transfer, etc.) |

**Response:**
```json
{
    "count": 200,
    "results": [
        {
            "id": 1,
            "invoice": {
                "id": 1,
                "invoice_number": "INV-2025-001"
            },
            "amount": "5500.00",
            "status": "succeeded",
            "payment_method": "card",
            "transaction_id": "pi_abc123",
            "payment_date": "2025-01-20T14:30:00Z"
        },
        ...
    ]
}
```

---

### POST /api/api/payments/{id}/refund/

Process a refund for a payment.

**Request:**
```json
{
    "refund_amount": 500.00,
    "reason": "Partial service cancellation"
}
```

**Response:**
```json
{
    "id": 1,
    "status": "refunded",
    "refunded_amount": "500.00",
    "refund_reason": "Partial service cancellation",
    "refunded_at": "2025-12-29T10:00:00Z"
}
```

---

### GET /api/api/payments/stats/

Get payment statistics.

**Response:**
```json
{
    "total_payments": 200,
    "successful_payments": 190,
    "failed_payments": 8,
    "refunded_payments": 2,
    "total_amount": "500000.00",
    "total_refunded": "5000.00"
}
```

---

### GET /api/api/payment-methods/

List saved payment methods for clients.

**Response:**
```json
{
    "results": [
        {
            "id": 1,
            "client": 1,
            "type": "card",
            "last_four": "4242",
            "brand": "visa",
            "exp_month": 12,
            "exp_year": 2027,
            "is_default": true,
            "is_active": true
        }
    ]
}
```

---

## Analytics Endpoints

### GET /api/analytics/dashboard/

Get dashboard summary metrics.

**Response:**
```json
{
    "revenue": {
        "total": "500000.00",
        "this_month": "45000.00",
        "last_month": "42000.00",
        "growth_percentage": 7.14
    },
    "clients": {
        "total": 150,
        "active": 120,
        "new_this_month": 8
    },
    "invoices": {
        "outstanding": 15,
        "overdue": 3,
        "outstanding_amount": "75000.00"
    },
    "contracts": {
        "active": 30,
        "pending_signature": 5,
        "total_value": "750000.00"
    }
}
```

---

### GET /api/analytics/revenue/

Get revenue metrics and trends.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| period | string | Time period (daily, weekly, monthly, yearly) |
| start_date | date | Start date |
| end_date | date | End date |

**Response:**
```json
{
    "mrr": "42000.00",
    "arr": "504000.00",
    "trend": [
        {"month": "2025-01", "revenue": "38000.00"},
        {"month": "2025-02", "revenue": "40000.00"},
        {"month": "2025-03", "revenue": "42000.00"},
        ...
    ],
    "by_client": [
        {"client_id": 1, "client_name": "Smith Industries", "revenue": "50000.00"},
        {"client_id": 2, "client_name": "Doe Enterprises", "revenue": "35000.00"},
        ...
    ]
}
```

---

### GET /api/analytics/clients/

Get client metrics.

**Response:**
```json
{
    "total_clients": 150,
    "by_lifecycle_stage": {
        "lead": 15,
        "prospect": 10,
        "active": 120,
        "churned": 5
    },
    "acquisition": [
        {"month": "2025-01", "new_clients": 5},
        {"month": "2025-02", "new_clients": 8},
        ...
    ],
    "top_clients": [
        {
            "id": 1,
            "name": "Smith Industries",
            "total_value": "150000.00",
            "lifetime_value": "150000.00"
        },
        ...
    ]
}
```

---

### GET /api/analytics/activity/

Get recent activity feed.

**Response:**
```json
{
    "activities": [
        {
            "type": "invoice_paid",
            "message": "Invoice INV-2025-015 paid by Smith Industries",
            "timestamp": "2025-12-29T10:30:00Z",
            "amount": "5500.00"
        },
        {
            "type": "contract_signed",
            "message": "Contract CTR-2025-010 signed by Jane Doe",
            "timestamp": "2025-12-29T09:15:00Z"
        },
        {
            "type": "client_created",
            "message": "New client: ABC Corporation",
            "timestamp": "2025-12-29T08:00:00Z"
        },
        ...
    ]
}
```

---

## Webhook Endpoints

### POST /webhooks/stripe/

Stripe webhook endpoint for payment events.

**Headers Required:**
```
Stripe-Signature: t=1234567890,v1=signature_hash
```

**Supported Events:**
| Event | Action |
|-------|--------|
| payment_intent.succeeded | Mark invoice as paid |
| payment_intent.payment_failed | Record failure, notify |
| invoice.paid | Update invoice status |
| customer.subscription.updated | Sync subscription |
| charge.refunded | Process refund |

**Response:**
```json
HTTP 200 OK
{"received": true}
```

---

### GET /webhooks/health/

Health check for webhook system.

**Response:**
```json
{
    "status": "healthy",
    "stripe_configured": true,
    "last_event_processed": "2025-12-29T10:00:00Z"
}
```

---

## Common Response Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 204 | No Content | Delete successful |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Pagination

All list endpoints support pagination:

```json
{
    "count": 150,
    "next": "https://api.example.com/endpoint/?page=2",
    "previous": null,
    "results": [...]
}
```

**Query Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| page | 1 | Page number |
| page_size | 50 | Items per page (max: 100) |

---

## Filtering and Search

Most list endpoints support:

- **search**: Full-text search across relevant fields
- **ordering**: Sort by field (prefix with `-` for descending)
- **Field filters**: Exact match filters

Example:
```
GET /api/api/invoices/?status=overdue&ordering=-due_date&search=Smith
```

---

## Support

For API support:

- **Email**: api-support@rhematek-solutions.com
- **Documentation**: https://docs.aureon.rhematek-solutions.com/api
- **Status**: https://status.aureon.rhematek-solutions.com

---

**Aureon API** - Version 2.0.0
Copyright 2025 Rhematek Solutions
