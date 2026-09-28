# Molinos del Atlántico — Sistema de Trazabilidad de Producción

Sistema web de control de producción para una planta de molienda y empaque de
harinas. Reemplaza los formatos de control en papel (peso, rotulado,
mermas, mantenimiento) por planillas digitales que los operarios llenan
desde tabletas en piso de planta, con un panel administrativo centralizado
para supervisión, indicadores en tiempo real y trazabilidad de lotes de
exportación.

**Stack:** FastAPI + PostgreSQL (backend) · Angular 17 + Tailwind CSS (frontend)

---

## Funcionalidades principales

**Planillas digitales de piso de planta** (uso en tableta)
- Control de material de empaque (bobinas), con cálculo automático de
  consumo y detección de valores atípicos al pesar.
- Rotulado y sellado: verificación de fechado por hora, con lectura óptica
  (OCR) opcional de la fecha impresa en el empaque.
- Control de peso de empacadoras y de enfardadoras, con matriz de muestreo
  por hora y semáforo de cumplimiento contra rangos mínimos/máximos.
- Registro de mermas por causa raíz (bolsa rota, defecto de sellado, scrap).

**Panel administrativo**
- Dashboard con indicadores de producción, desperdicio, cumplimiento de
  meta y alertas de inventario en tiempo real.
- Informes de turno consolidados por máquina, con generación de PDF en el
  servidor (renderizado headless, no depende del navegador de quien lo pide).
- Gestión de inventario de empaque (bodega), con solicitudes de salida y
  cobertura estimada en días.
- Mantenimiento preventivo: cronograma, notificaciones de vencimiento y
  solicitudes de reparación desde piso de planta.
- Trazabilidad de lote: vincula cada planilla (empaque, rotulado, peso) al
  número de orden de producción y lote de un embarque de exportación.
- Muestreo de calidad con selección aleatoria de unidades y catálogo de
  referencias validado contra lo realmente producido ese día.
- OEE y registro de paros de máquina.
- Gestión de usuarios y roles (administrador, calidad, bodega, operario),
  con firma digital reutilizable por cuenta.

**Automatización**
- Generación de PDF en servidor (Playwright) reutilizando la misma vista
  que ve el operario, para que el documento final sea idéntico al formato
  digital.
- Envío automático de los PDF de exportación a un flujo externo (n8n) o por
  correo, configurable por variables de entorno.

---

## Estructura del proyecto

```
molinos-project/
├── backend/
│   ├── app/
│   │   ├── main.py              # registro de rutas
│   │   ├── database.py
│   │   ├── auth.py               # JWT + roles
│   │   ├── pdf_render.py         # PDF server-side (Playwright)
│   │   ├── email_sender.py       # envío por correo (opcional)
│   │   ├── n8n_sender.py         # envío a flujo externo (opcional)
│   │   ├── models/models.py
│   │   ├── schemas/
│   │   └── routers/
│   │       ├── auth.py, bobinas.py, rotulado.py, pesos.py,
│   │       │   pesos_enfardadora.py, vision.py, informe.py,
│   │       │   dashboard.py, bodega.py, validacion.py,
│   │       │   mantenimiento.py, trazabilidad.py, estiba.py,
│   │       │   calidad.py, mermas.py, oee.py
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    └── src/app/
        ├── components/    # una carpeta por pantalla/formato
        ├── services/
        └── models/
```

---

## Configuración inicial (una sola vez)

### 1. Crear la base de datos en PostgreSQL

```sql
CREATE DATABASE molinos_db;
```

### 2. Configurar variables de entorno

Dentro de `backend/`, copia `.env.example` a `.env` y completa tus datos
(base de datos, clave de firma de sesión, y opcionalmente OCR/envío de PDF).

---

## Levantar el proyecto (dos terminales)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium   # una sola vez, para el PDF en servidor
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

Abre **http://localhost:4200** en el navegador.

---

## Documentación de la API

Documentación interactiva (Swagger) generada automáticamente:
**http://localhost:8000/docs**
