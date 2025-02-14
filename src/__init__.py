from fastapi import FastAPI
from src.bookings.routes import booking_router
from src.invoice.routes import invoice_router
from src.db.main import init_db
from src.auth.routes import auth_router
from fastapi.middleware.cors import CORSMiddleware

version = "v1"
description=""




app = FastAPI(
    title="Moving Website API",
    description=description,
    version=version,
)

# Define allowed origins (you can set "*" to allow all)
origins = [
    "http://localhost:3000",  # If you're calling from a frontend like React/Next.js
    "http://127.0.0.1:3000",
    "http://192.168.1.72:5173",
    "http://localhost:5173",
    "https://blackbrosdelivery.ca",
    "https://www.blackbrosdelivery.ca",
    "https://api.blackbrosdelivery.ca/",
    "https://yourfrontenddomain.com",  # Add your production frontend domain
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(booking_router,prefix=f"/api/{version}/bookings", tags=["Bookings"])


app.include_router(auth_router,prefix=f"/api/{version}/auth", tags=["Auth"])


app.include_router(invoice_router,prefix=f"/api/{version}/invoices", tags=["Invoices"])