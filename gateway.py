from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import asyncio
import os
from common_utils import (
    CorrelationIdMiddleware,
    setup_exception_handlers,
    setup_json_logger,
)

#app = FastAPI(title="HMS API Gateway")
#app.add_middleware(CorrelationIdMiddleware)


app = FastAPI(title="HMS API Gateway")

# 2. ADD THIS BLOCK IMMEDIATELY AFTER app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your React dev server to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)

logger = setup_json_logger("gateway_service")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "gateway"}

# Service URLs mapped from Docker environment
SERVICES = {
    "patient": os.getenv("PATIENT_SERVICE_URL", "http://patient-service:9001/v1"),
    "patients": os.getenv("PATIENT_SERVICE_URL", "http://patient-service:9001/v1"),
    "doctor": os.getenv("DOCTOR_SERVICE_URL", "http://doctor-service:9002/v1"),
    "doctors": os.getenv("DOCTOR_SERVICE_URL", "http://doctor-service:9002/v1"),
    "appointment": os.getenv("APPOINTMENT_SERVICE_URL", "http://appointment-service:9003/v1"),
    "appointments": os.getenv("APPOINTMENT_SERVICE_URL", "http://appointment-service:9003/v1"),
    "prescription": os.getenv("PRESCRIPTION_SERVICE_URL", "http://prescription-service:9004/v1"),
    "prescriptions": os.getenv("PRESCRIPTION_SERVICE_URL", "http://prescription-service:9004/v1"),
    "billing": os.getenv("BILLING_SERVICE_URL", "http://billing-service:9005/v1"),
    "bills": os.getenv("BILLING_SERVICE_URL", "http://billing-service:9005/v1"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:9006/v1"),
    "payments": os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:9006/v1"),
    "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:9007/v1"),
    "notifications": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:9007/v1"),
}

class LoginRequest(BaseModel):
    username: str
    password: str


USERS = {
    "reception_user": {"password": "reception_pass", "role": "reception"},
    "doctor_user": {"password": "doctor_pass", "role": "doctor"},
    "billing_user": {"password": "billing_pass", "role": "billing"},
    "admin_user": {"password": "admin_pass", "role": "admin"},
}

def extract_role_from_auth_header(request: Request) -> str:
    """
    Extracts role from mock bearer token format like 'Bearer admin_test'.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise ValueError()
        role = token.split("_")[0]
        return role
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token format")

async def fetch_data(client, url, headers=None, method="GET", json=None):
    try:
        logger.info(f"Proxy request method={method} url={url}")
        response = await client.request(method, url, headers=headers, json=json)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404: return None
        raise HTTPException(status_code=e.response.status_code, detail=f"Upstream error: {e.response.text}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {url}")

router = APIRouter(prefix="/api/v1")

@router.post("/auth/login")
def login(payload: LoginRequest):
    """
    Mock login endpoint for assignment/demo.
    Returns a simple bearer token in role_test format.
    """
    user = USERS.get(payload.username)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = f"{user['role']}_test"
    logger.info(f"Successful login username={payload.username} role={user['role']}")
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"]
    }


@router.get("/auth/me")
def me(request: Request):
    """
    Returns the role extracted from the current Authorization header.
    """
    role = extract_role_from_auth_header(request)
    return {"role": role}

@router.get("/appointments/{appointment_id}")
async def get_composed_appointment(appointment_id: int, request: Request):
    role = extract_role_from_auth_header(request)
    headers = {
        "X-Correlation-ID": getattr(request.state, "correlation_id", ""),
        "Authorization": f"Bearer {role}_test",
    }

    async with httpx.AsyncClient() as client:
        appointment = await fetch_data(client, f"{SERVICES['appointment']}/appointments/{appointment_id}", headers)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        patient_task = fetch_data(client, f"{SERVICES['patient']}/patients/{appointment['patient_id']}", headers)
        doctor_task = fetch_data(client, f"{SERVICES['doctor']}/doctors/{appointment['doctor_id']}", headers)
        patient, doctor = await asyncio.gather(patient_task, doctor_task)

        return {"appointment": appointment, "patient": patient, "doctor": doctor}

@router.post("/bills/generate-from-appointment/{id}")
async def proxy_generate_bill(id: int, request: Request):
    role = extract_role_from_auth_header(request)
    headers = {
        "X-Correlation-ID": getattr(request.state, "correlation_id", ""),
        "Authorization": f"Bearer {role}_test",
    }

    async with httpx.AsyncClient() as client:
        return await fetch_data(
            client,
            f"{SERVICES['billing']}/bills/generate-from-appointment/{id}",
            headers=headers,
            method="POST"
        )
        
@router.post("/bills/handle-cancellation/{id}")
async def proxy_cancel_bill(id: int, request: Request):
    role = extract_role_from_auth_header(request)
    headers = {
        "X-Correlation-ID": getattr(request.state, "correlation_id", ""),
        "Authorization": f"Bearer {role}_test",
    }
    body = await request.json()

    async with httpx.AsyncClient() as client:
        return await fetch_data(
            client,
            f"{SERVICES['billing']}/bills/handle-cancellation/{id}",
            headers=headers,
            method="POST",
            json=body
        )

@router.api_route("/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def generic_proxy(service_name: str, path: str, request: Request):
    role = extract_role_from_auth_header(request)

    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not mapped")

    base_url = SERVICES[service_name].rstrip("/")
 
    if path:
        full_url = f"{base_url}/{path.lstrip('/')}"
    else:
        full_url = base_url

    if request.query_params:
        full_url += f"?{request.query_params}"

    headers = {
        "X-Correlation-ID": getattr(request.state, "correlation_id", ""),
        "Authorization": f"Bearer {role}_test",
    }

    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except Exception:
            pass

    logger.info(f"Routing method={request.method} service={service_name} url={full_url} role={role}")

    async with httpx.AsyncClient() as client:
        return await fetch_data(client, full_url, headers=headers, method=request.method, json=body)

app.include_router(router)