# Asgard Transactions API

![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
![Flask](https://img.shields.io/badge/flask-3.1-black?style=flat-square)
![MySQL](https://img.shields.io/badge/mysql-8.0-blue?style=flat-square)

> **v1 Flask MVP** — Primera iteración del servicio de transacciones usando Flask + MySQL

API REST para gestión de transacciones de pago que implementa el flujo AUTH → CAPTURE → REFUND con idempotencia y validación de reglas de negocio.

**Parte de un experimento** donde construyo el mismo servicio con diferentes tecnologías (Flask, FastAPI, Go) para comparar enfoques arquitectónicos.

---

## Tabla de Contenidos

- [Características](#características)
- [Inicio Rápido](#inicio-rápido)
- [Uso de la API](#uso-de-la-api)
- [Reglas de Negocio](#reglas-de-negocio)
- [Arquitectura](#arquitectura)
- [Estado del Proyecto](#estado-del-proyecto)
- [Stack Tecnológico](#stack-tecnológico)
- [Comandos Útiles](#comandos-útiles)
- [Aprendizajes](#aprendizajes)

---

## Características

**Operaciones soportadas:**
- **AUTH** — Autorización de pago (reserva fondos)
- **CAPTURE** — Captura de fondos autorizados
- **REFUND** — Devolución de transacciones

**Features implementados:**
- Validación de flujo de transacciones
- Idempotencia basada en `merchant_id + order_reference`
- Connection pooling con singleton pattern
- Arquitectura en 3 capas (routes → services → db)
- Manejo de errores con excepciones personalizadas
- Docker ready

---

## Inicio Rápido

**Prerequisitos:**
- Docker 20.10+
- Docker Compose 1.29+

**Instalación con Docker (recomendado):**
```bash
git clone https://github.com/KatzeeDev/asgard-transactions-api-rest.git
cd asgard-transactions-api-rest
git checkout v1-flask-mvp

docker-compose up -d
```

La API estará disponible en `http://localhost:5001`

**Verificar:**
```bash
curl http://localhost:5001/transactions
```

**Instalación local (sin Docker):**

Si prefieres correr la aplicación sin Docker:

```bash
# Clonar repositorio
git clone https://github.com/KatzeeDev/asgard-transactions-api-rest.git
cd asgard-transactions-api-rest
git checkout v1-flask-mvp

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de MySQL

# Ejecutar la aplicación
cd src
python app.py
```

> **Nota:** Necesitarás una instancia de MySQL corriendo localmente. Configurar host, usuario, contraseña y base de datos en `.env`

---

## Uso de la API

**Endpoints disponibles:**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/transactions` | Crear nueva transacción |
| `GET` | `/transactions` | Listar todas las transacciones |
| `GET` | `/transactions/:id` | Obtener transacción por ID |
| `PATCH` | `/transactions/:id` | Actualizar estado de transacción |
| `DELETE` | `/transactions/:id` | Eliminar transacción |

**Ejemplo 1: Crear AUTH**
```json
POST http://localhost:5001/transactions

{
  "type": "AUTH",
  "amount": 15000.50,
  "currency": "CLP",
  "merchant_id": "MCH_001",
  "order_reference": "ORDER_2025_001",
  "metadata": {
    "product": "Laptop Dell XPS 15"
  }
}
```

**Ejemplo 2: Crear CAPTURE**
```json
POST http://localhost:5001/transactions

{
  "type": "CAPTURE",
  "amount": 15000.50,
  "currency": "CLP",
  "merchant_id": "MCH_001",
  "order_reference": "CAPTURE_001",
  "parent_transaction_id": "TXN_20251110_220654_AUTH_a1b341c7"
}
```

**Ejemplo 3: Actualizar estado**
```json
PATCH http://localhost:5001/transactions/TXN_20251110_220654_AUTH_a1b341c7

{
  "status": "APPROVED"
}
```

**Estados válidos:** `PENDING`, `APPROVED`, `DECLINED`
**Monedas soportadas:** `CLP`, `USD`, `EUR`

---

## Reglas de Negocio

**Flujo de transacciones:**
```
AUTH (inicio) → CAPTURE (captura fondos) → REFUND (devuelve fondos)
```

**Tipos de transacción:**

- **AUTH** — Primera transacción en el flujo. No requiere transacción padre.
- **CAPTURE** — Requiere transacción AUTH como padre. Captura fondos previamente autorizados.
- **REFUND** — Requiere transacción AUTH o CAPTURE como padre. Devuelve fondos al cliente.

**Idempotencia:**

Las transacciones son idempotentes basadas en `merchant_id + order_reference`. Si se intenta crear una transacción con la misma combinación, se retorna la existente en lugar de crear un duplicado.

> **Nota:** Actualmente implementado a nivel de aplicación. Falta agregar índice único en la base de datos para garantizarlo a nivel de DB.

---

## Arquitectura

**Estructura del proyecto:**
```
src/
├── app.py                      # Punto de entrada Flask
├── exceptions.py               # Excepciones personalizadas
├── routes/
│   └── transactions.py         # Endpoints HTTP
├── services/
│   └── transaction_service.py  # Lógica de negocio y validaciones
├── db/
│   ├── connection.py           # Connection pool (singleton)
│   └── queries.py              # Queries SQL
└── utils/
    └── helpers.py              # Funciones auxiliares
```

**Capas de la aplicación:**
```
┌─────────────────────────────────────┐
│         HTTP Layer (Flask)          │  ← routes/
├─────────────────────────────────────┤
│    Business Logic & Validation      │  ← services/
├─────────────────────────────────────┤
│       Data Access Layer (SQL)       │  ← db/
├─────────────────────────────────────┤
│           MySQL Database            │
└─────────────────────────────────────┘
```

**Patrones implementados:**
- **Separation of Concerns** — Cada capa tiene una responsabilidad única
- **Singleton Pattern** — Connection pool reutilizable
- **Dependency Flow** — Unidireccional (routes → services → db)

---

## Estado del Proyecto

**Completado:**
- [x] Estructura base con arquitectura en capas
- [x] Configuración Docker Compose
- [x] Schema de base de datos MySQL
- [x] CRUD completo de transacciones
- [x] Validación de reglas de negocio
- [x] Idempotencia (a nivel de aplicación)
- [x] Connection pooling con singleton pattern
- [x] Manejo de errores estructurado
- [x] Logging

**Pendiente:**
- [ ] Tests unitarios con pytest
- [ ] Índice único compuesto en BD para idempotencia
- [ ] Métricas básicas (contadores por tipo/estado)
- [ ] Dashboard web para visualización
- [ ] Optimización de queries

**Deliberadamente no implementado:**

Estas features se implementarán en la **Fase 2 (FastAPI)** donde son nativas:
- OpenAPI/Swagger automático
- Pydantic schemas para validación
- Validación declarativa de requests
- Type hints avanzados

---

## Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Lenguaje | Python | 3.11+ |
| Framework Web | Flask | 3.1.2 |
| Base de Datos | MySQL | 8.0 |
| Containerización | Docker | 20.10+ |
| Orquestación | Docker Compose | 1.29+ |

---

## Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f app

# Detener servicios
docker-compose down

# Reconstruir contenedores
docker-compose up -d --build

# Limpiar volúmenes (borra datos)
docker-compose down -v

# Acceder al contenedor
docker exec -it asgard_api bash

# Conectar a MySQL
docker exec -it asgard_db mysql -u root -p
```

---

## Aprendizajes

**Arquitectura en capas**

Separar en routes/services/db simplificó el debugging y mantenimiento. Al principio tenía todo en un solo archivo y cada cambio afectaba múltiples responsabilidades. Con la separación, cada capa tiene un propósito claro.

**Connection pooling**

Implementé un pool de 5 conexiones MySQL reutilizables usando singleton pattern. La diferencia de latencia vs crear conexiones nuevas en cada request fue notable, especialmente en operaciones repetitivas.

**Validación centralizada**

Toda la lógica de negocio (AUTH → CAPTURE → REFUND) vive en la capa de services. Los routes solo manejan HTTP. Esto garantiza que las validaciones sean consistentes sin importar desde dónde se invoquen.

**Idempotencia a nivel de aplicación**

Valido `merchant_id + order_reference` antes de insertar. Funcional pero no ideal. Falta agregar un índice único en la BD para garantizarlo a nivel de base de datos y prevenir race conditions.

**Flask para MVPs**

Setup directo, documentación clara, y con Docker el deployment es simple. Perfecto para entender fundamentos antes de saltar a frameworks más complejos.

**Próximo experimento:**

Reimplementar este mismo servicio con FastAPI para comparar:
- Performance async vs sync
- Developer experience con features automáticas (OpenAPI, Pydantic)
- Tiempo de desarrollo

---

<div align="center">

**v1 Flask MVP** · Fase 1 de 4

[Ver proyecto completo](../../tree/main) · [Issues](../../issues)

</div>
