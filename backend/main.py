from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import ipaddress
from app.config import settings
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.events import startup_event, shutdown_event
from app.api import tasks, logs

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    docs_url='/api/docs',
    redoc_url='/api/redoc'
)

# Add CORS middleware - allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IP filtering middleware
@app.middleware("http")
async def ip_filter_middleware(request: Request, call_next):
    allowed_ips = settings.get_allowed_ips()
    if allowed_ips: # allowed_ips 是 ['127.0.0.1/32', '192.168.0.0/16'] 这样的格式
        client_ip = request.client.host
        # 检查IP是否匹配任一CIDR网络
        allowed = False
        for cidr in allowed_ips:
            try:
                network = ipaddress.ip_network(cidr, strict=False)
                ip = ipaddress.ip_address(client_ip)
                if ip in network:
                    allowed = True
                    break
            except ValueError as e:
                logger.warning(f"Invalid CIDR format '{cidr}': {e}")
                continue

        if not allowed:
            return JSONResponse(
                status_code=403,
                content={"detail": f"IP {client_ip} not allowed"}
            )
    response = await call_next(request)
    return response

# Register event handlers
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Register API routers
app.include_router(tasks.router, prefix='/api')
app.include_router(logs.router, prefix='/api')

# Serve static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )