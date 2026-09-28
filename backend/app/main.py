from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import bobinas, rotulado, pesos, pesos_enfardadora, auth, vision, informe, dashboard, bodega, validacion, mantenimiento, trazabilidad, estiba, calidad, mermas, oee

app = FastAPI(
    title="Molinos del Atlántico - Formatos Digitales",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "http://192.168.88.12:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/api/auth",      tags=["Autenticación"])
app.include_router(bobinas.router,   prefix="/api/bobinas",   tags=["Bobinas"])
app.include_router(rotulado.router,  prefix="/api/rotulado",  tags=["Rotulado"])
app.include_router(pesos.router,     prefix="/api/pesos",     tags=["Pesos"])
app.include_router(pesos_enfardadora.router, prefix="/api/pesos-enfardadora", tags=["Control de Peso Enfardadoras"])
app.include_router(vision.router,    prefix="/api/vision",    tags=["Vision IA"])
app.include_router(informe.router,   prefix="/api/informes",  tags=["Informes de Turno"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(bodega.router,    prefix="/api/bodega",    tags=["Bodega"])
app.include_router(validacion.router, prefix="/api/validacion", tags=["Validación Cruzada"])
app.include_router(mantenimiento.router, prefix="/api/mantenimiento", tags=["Mantenimiento"])
app.include_router(trazabilidad.router, prefix="/api/trazabilidad", tags=["Trazabilidad de Lote"])
app.include_router(estiba.router, prefix="/api/estiba", tags=["Estibas"])
app.include_router(calidad.router, prefix="/api/calidad", tags=["Muestreo de Calidad"])
app.include_router(mermas.router, prefix="/api/mermas", tags=["Control de Mermas"])
app.include_router(oee.router, prefix="/api/oee", tags=["OEE y Paros de Máquina"])

@app.get("/")
def root():
    return {"status": "ok", "app": "Molinos del Atlántico v2"}