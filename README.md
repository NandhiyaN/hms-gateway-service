
## Gateway Service README

```md
# Gateway Service - Hospital Management System

## 1. Overview
Gateway Service is one of the core services in the Hospital Management System. It acts as the single entry point for clients and routes requests to downstream microservices.

This service supports:
- Mock login and token generation
- Current user role lookup
- Generic proxy routing to downstream services
- Composed appointment retrieval
- Billing proxy operations
- Correlation ID propagation
- Standard error responses
- Structured JSON logging

This service follows the **API Gateway** pattern required by the assignment.

---

## 2. Assignment Mapping
This repository addresses the following assignment requirements for **Gateway Service**:

- API Gateway implementation
- Central entry point for client requests
- Mock authentication support
- Request routing to downstream services
- Composed response handling
- Standard error response structure: `code`, `message`, `correlationId`
- Correlation ID propagation
- Docker containerization support
- Health endpoint
- OpenAPI 3.0 documentation
- Unit/API test cases

---

## 3. Tech Stack
- Python 3.11+
- FastAPI
- HTTPX
- AsyncIO
- Pytest
- Docker

---

## 4. Project Structure

```text
gateway-service/
│── gateway.py
│── common_utils.py
│── requirements.txt
│── Dockerfile
│── openapi_gateway.yaml
│── README.md
│── .gitignore
│── tests/
│   └── test_gateway_service.py

```

## 5. Service Responsibilities

This service does not own business data directly. It acts as a routing and orchestration layer across downstream services.

**Responsibilities**
 - Act as the central API entry point
 - Authenticate users using mock login for assignment/demo
 - Extract user role from bearer token
 - Route requests to downstream services
 - Forward authorization and correlation ID headers
 - Compose appointment details from multiple services

---

## 6. API Base URL
Local:
    http://localhost:9000

Swagger UI:
    http://localhost:9000/docs

Health:
    http://localhost:9000/health


---

## 7. API Endpoints
**Health Endpoints**

| Method | Endpoint | Description                    |
| ------ | -------- | ------------------------------ |
| GET    | /health  | Basic service health check     |

**Authentication Endpoints**

| Method | Endpoint           | Description                     |
| ------ | ------------------ | ------------------------------- |
| POST   | /api/v1/auth/login | Mock login and token generation |
| GET    | /api/v1/auth/me    | Get current authenticated role  |

**Gateway / Proxy Endpoints**

| Method | Endpoint                                     | Description                           |
| ------ | -------------------------------------------- | ------------------------------------- |
| GET    | /api/v1/appointments/{appointment_id}        | Get composed appointment details      |
| POST   | /api/v1/bills/generate-from-appointment/{id} | Proxy request to billing service      |
| POST   | /api/v1/bills/handle-cancellation/{id}       | Proxy cancellation request to billing |
| GET    | /api/v1/{service_name}/{path}                | Generic GET proxy                     |
| POST   | /api/v1/{service_name}/{path}                | Generic POST proxy                    |
| PUT    | /api/v1/{service_name}/{path}                | Generic PUT proxy                     |
| DELETE | /api/v1/{service_name}/{path}                | Generic DELETE proxy                  |


---

## 8. Supported Downstream Service Mappings

The gateway maps the following downstream service names:

| Service Key   | Target Environment Variable / Service URL |
| ------------- | ----------------------------------------- |
| patient       | PATIENT_SERVICE_URL                       |
| patients      | PATIENT_SERVICE_URL                       |
| doctor        | DOCTOR_SERVICE_URL                        |
| doctors       | DOCTOR_SERVICE_URL                        |
| appointment   | APPOINTMENT_SERVICE_URL                   |
| appointments  | APPOINTMENT_SERVICE_URL                   |
| prescription  | PRESCRIPTION_SERVICE_URL                  |
| prescriptions | PRESCRIPTION_SERVICE_URL                  |
| billing       | BILLING_SERVICE_URL                       |
| bills         | BILLING_SERVICE_URL                       |
| payment       | PAYMENT_SERVICE_URL                       |
| payments      | PAYMENT_SERVICE_URL                       |
| notification  | NOTIFICATION_SERVICE_URL                  |
| notifications | NOTIFICATION_SERVICE_URL                  |

Example:
GET /api/v1/patients/1

---

## 9. RBAC
Login request format:

POST /api/v1/auth/login

Sample users configured in gateway:

| Username       | Password       | Role      |
| -------------- | -------------- | --------- |
| reception_user | reception_pass | reception |
| doctor_user    | doctor_pass    | doctor    |
| admin_user     | admin_pass     | admin     |

Authorization header format after login:

Authorization: Bearer <role>_test

Examples:

Authorization: Bearer admin_test

Authorization: Bearer reception_test

Authorization: Bearer admin_test

---

## 10. Request and Response Examples

 ### Login

**Request**

POST /api/v1/auth/login
Content-Type: application/json
X-Correlation-ID: gateway-login-001

```json
{
  "username": "admin_user",
  "password": "admin_pass"
}
```

**Response**
```json
{
  "access_token": "admin_test",
  "token_type": "bearer",
  "role": "admin"
}
```
 ### Get Current Role

**Request**

GET /api/v1/auth/me
Authorization: Bearer admin_test
X-Correlation-ID: gateway-me-001

**Response**
``` json
{
  "role": "admin"
}
```
 ### Generic Proxy Example

**Request**

GET /api/v1/patients/1
Authorization: Bearer reception_test
X-Correlation-ID: gateway-proxy-001

**Response**
Response is proxied from the downstream patient service.

---

## 11. Standard Error Response
```json
{
  "code": "404",
  "message": "Service not mapped",
  "correlationId": "xxx"
}
```
| Status Code | Meaning                                   |
| ----------- | ----------------------------------------- |
| 401         | Missing/invalid token or login failure    |
| 404         | Service not mapped / downstream not found |
| 422         | Validation error                          |
| 500         | Internal error                            |
| 503         | Downstream service unavailable            |

---

## 12. Validation Rules
Username and password are required for login

Authorization header must follow Bearer token format

Service name must exist in configured service mapping

Gateway forwards only supported request methods and paths

---

## 13. Proxy and Composition Behavior
Gateway provides both proxying and composition behavior.

**Generic proxy flow**
 - Extract role from Authorization header
 - Resolve downstream service URL
 - Forward request method, headers, and body
 - Return downstream response

**Composed appointment flow**
 - Fetch appointment from Appointment Service
 - Fetch related patient data
 - Fetch related doctor data
 - Return combined response in a single payload

**Billing proxy flow**
 - Forward generate-bill request to Billing Service
 - Forward cancellation-handling request to Billing Service

---

## 14. Logging and Structured Output

This service uses structured JSON logging.

 - Logs are generated in JSON format for better monitoring
 - Login and proxy events are logged
 - Correlation ID is propagated across downstream calls

Example:

```json
{
  "timestamp": "2026-04-19T10:00:00Z",
  "service": "gateway_service",
  "level": "INFO",
  "message": "Routing method=GET service=patients url=http://patient-service:9001/v1/patients/1 role=reception"
}

```
---

## 15. Correlation ID Support
Client-provided X-Correlation-ID propagated

Auto-generated if missing

Returned in response headers

Forwarded to downstream services for tracing

---

## 16. Local Setup Instructions

 ### Step 1: Clone the repository
    ```bash
    git clone https://github.com/NandhiyaN/hms-gateway-service
    cd gateway-service
    ```
 ### Step 2: Create virtual environment
    ```bash
    python -m venv venv
    ```
 ### Step 3: Activate environment

    Windows:
        venv\Scripts\activate
    Linux/Mac:
        source venv/bin/activate

 ### Step 4: Install dependencies
    ```bash
    pip install -r requirements.txt
    pip install uvicorn
    ```

 ### Step 5: Run the service
    ```bash
    python -m uvicorn gateway:app --reload --port 9000
    ```
 ### Step 6: Open Swagger UI
    http://localhost:9000/docs

---

## 17. Running Tests
Run:
python -m pytest tests/test_gateway_service.py -v

Covers health, login success/failure, and current user role lookup.

---

## 18. Bruno API Collection
Bruno collection can be added under bruno/ for manual API validation and demo execution.

---

## 19. OpenAPI Specification

File: openapi_gateway.yaml

This file documents:
- Health API
- Authentication APIs
- Composed appointment API
- Billing proxy APIs
- Generic proxy endpoints
- Standard error responses

---

## 20. Docker Support
Build: docker build -t gateway-service .

Run: docker run -p 9000:9000 gateway-service

Verify: curl http://localhost:9000/health

---

## 21. Kubernetes Readiness
Supports containerized startup, environment-based downstream service URL configuration, and health verification through /health.

Future manifests can be added under k8s/.

---

## 22. Important Design Decisions
API Gateway pattern

Centralized mock authentication

Structured logging

Correlation ID propagation

Generic proxy routing

Composed response support for appointment view

---

## 23. Future Improvements
JWT-based authentication

Rate limiting

Circuit breaker / retry support

Service discovery

Prometheus metrics

CI/CD pipeline

Kubernetes manifests

API gateway policies

---

## 24. Author / Contribution
Scope: Gateway routing, mock authentication, role extraction, downstream proxying, composed response handling, tests, Docker setup, and OpenAPI documentation.
