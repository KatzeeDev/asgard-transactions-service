# Asgard Transactions API

![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
![Flask](https://img.shields.io/badge/flask-3.1-black?style=flat-square)
![MySQL](https://img.shields.io/badge/mysql-8.0-blue?style=flat-square)

> **v1 Flask MVP** — API REST para transacciones de pago con idempotencia automática

Servicio de transacciones que implementa el flujo AUTH → CAPTURE → REFUND con arquitectura en 3 capas, validación de reglas de negocio e idempotencia basada en fingerprint temporal.

---

## Inicio Rápido

**Prerequisitos:** Docker 20.10+ y Docker Compose 1.29+

```bash
git clone https://github.com/KatzeeDev/asgard-transactions-api-rest.git
cd asgard-transactions-api-rest
cp env.template .env  # Generar archivo de entorno
docker-compose up -d
```

API disponible en `http://localhost:5001`

**Verificar:**

```bash
curl http://localhost:5001/transactions
```

---

## API Endpoints

| Método   | Endpoint            | Descripción       |
| -------- | ------------------- | ----------------- |
| `POST`   | `/transactions`     | Crear transacción |
| `GET`    | `/transactions`     | Listar todas      |
| `GET`    | `/transactions/:id` | Obtener por ID    |
| `PATCH`  | `/transactions/:id` | Actualizar status |
| `DELETE` | `/transactions/:id` | Eliminar          |

### Crear AUTH

```json
POST /transactions
{
  "type": "AUTH",
  "amount": 150000,
  "currency": "CLP",
  "merchant_id": "MERCH_001",
  "order_reference": "ORDER_001",
  "country_code": "CL",
  "metadata": {
    "customer_email": "user@example.com",
    "product": "Laptop"
  }
}
```

**Respuesta:**

```json
{
    "id": "01KA24B5K02M1P121JGF8P6DR4",
    "message": "transaction created successfully",
    "status": "PENDING"
}
```

### Crear CAPTURE

```json
POST /transactions
{
  "type": "CAPTURE",
  "amount": 150000,
  "currency": "CLP",
  "merchant_id": "MERCH_001",
  "order_reference": "ORDER_001_CAP",
  "country_code": "CL",
  "parent_id": "01KA24B5K02M1P121JGF8P6DR4"
}
```

### Crear REFUND

```json
POST /transactions
{
  "type": "REFUND",
  "amount": 50000,
  "currency": "CLP",
  "merchant_id": "MERCH_001",
  "order_reference": "ORDER_001_REF",
  "country_code": "CL",
  "parent_id": "01KA23Y6PQ3W1F45GWEBPPZVRN",
  "metadata": {
    "reason": "customer_request"
  }
}
```

### Actualizar Status

```json
PATCH /transactions/01KA24B5K02M1P121JGF8P6DR4
{
  "status": "APPROVED"
}
```

---

## Tipos de Transacciones

| Tipo      | Requiere Padre      | Descripción                          |
| --------- | ------------------- | ------------------------------------ |
| `AUTH`    | No                  | Autorización inicial, reserva fondos |
| `CAPTURE` | Sí (AUTH)           | Captura fondos autorizados           |
| `REFUND`  | Sí (AUTH o CAPTURE) | Devolución de fondos                 |

**Estados:** `PENDING`, `PROCESSING`, `APPROVED`, `DECLINED`, `EXPIRED`, `CANCELLED`, `FAILED`
**Monedas:** `CLP`, `USD`, `EUR`, `GBP`
**Países:** `CL`, `US`, `ES`, `GB`, `SE`, `BR`, `AR`, `MX`, `CO`, `PE`, `UY`

---

## Idempotencia

El sistema genera automáticamente un **fingerprint** basado en:

```
merchant_id + order_reference + amount + currency + type + country_code + ventana_temporal
```

**Ventana temporal:** 5 minutos

**Comportamiento:**

-   Requests idénticas dentro de 5 min → retorna transacción existente
-   Mismo order pero diferente monto → crea nueva transacción
-   Retry después de 5 min → crea nueva transacción

**Ejemplo - Duplicado detectado:**

```bash
# Request 1
POST {merchant: "X", order: "O1", amount: 1000}
→ 201 Created: id=ABC123

# Request 2 (30 seg después, valores idénticos)
POST {merchant: "X", order: "O1", amount: 1000}
→ 200 OK: id=ABC123, message="transaction already exists"
```

**Ejemplo - Monto diferente:**

```bash
# Request 1
POST {merchant: "X", order: "O1", amount: 1000}
→ 201 Created: id=ABC123

# Request 2 (mismo order, diferente monto)
POST {merchant: "X", order: "O1", amount: 500}
→ 201 Created: id=DEF456
```

---

## Manejo de Errores

### Respuestas HTTP

| Código | Significado                             |
| ------ | --------------------------------------- |
| `200`  | Operación exitosa o duplicado detectado |
| `201`  | Transacción creada                      |
| `400`  | Error de validación                     |
| `404`  | Transacción no encontrada               |
| `500`  | Error interno del servidor              |

### Errores de Validación (400)

```json
{
    "error": "amount must be greater than zero"
}
```

**Errores comunes:**

-   `"invalid json"` - JSON malformado
-   `"type is required"` - Campo obligatorio faltante
-   `"currency must be one of CLP, USD, EUR, GBP"` - Moneda inválida
-   `"country_code must be one of CL, US, ES, ..."` - País no soportado
-   `"CAPTURE requires parent_id"` - Falta referencia a transacción padre
-   `"parent transaction not found"` - Parent ID inválido
-   `"capture must reference an auth transaction"` - Padre incorrecto
-   `"auth cannot have parent_id"` - AUTH no puede tener padre

### Errores de Negocio (404)

```json
{
    "error": "transaction 01KA24B5... not found"
}
```

### Campo error_code (Opcional)

Al crear una transacción puedes incluir `error_code` para tracking:

```json
POST /transactions
{
  "type": "AUTH",
  "amount": 1000,
  "currency": "USD",
  "merchant_id": "MERCH_001",
  "order_reference": "ORDER_FAILED",
  "country_code": "US",
  "error_code": "INSUFFICIENT_FUNDS"
}
```

**Códigos estándar recomendados:**

-   `INSUFFICIENT_FUNDS` - Fondos insuficientes
-   `CARD_EXPIRED` - Tarjeta expirada
-   `INVALID_CARD` - Tarjeta inválida
-   `DECLINED_BY_ISSUER` - Rechazada por banco emisor
-   `NETWORK_ERROR` - Error de red/comunicación
-   `FRAUD_SUSPECTED` - Fraude detectado
-   `LIMIT_EXCEEDED` - Límite excedido
-   `AUTHENTICATION_FAILED` - Fallo de autenticación

---

## Schema de Base de Datos

```sql
CREATE TABLE transactions (
  id CHAR(26) PRIMARY KEY,                    -- ULID
  idempotency_key VARCHAR(64) UNIQUE NOT NULL,-- Hash SHA256
  type ENUM('AUTH','CAPTURE','REFUND'),
  status ENUM('PENDING','PROCESSING','APPROVED','DECLINED',
              'EXPIRED','CANCELLED','FAILED') DEFAULT 'PENDING',
  amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
  currency ENUM('CLP','USD','EUR','GBP') NOT NULL,
  merchant_id VARCHAR(32) NOT NULL,
  order_reference VARCHAR(128) NOT NULL,
  parent_id CHAR(26) NULL,
  country_code CHAR(2) NOT NULL CHECK (country_code REGEXP '^[A-Z]{2}$'),
  metadata JSON NULL,
  error_code VARCHAR(64) NULL,
  created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  status_updated_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  processed_at TIMESTAMP(3) NULL,

  FOREIGN KEY (parent_id) REFERENCES transactions(id) ON DELETE RESTRICT
);
```

**Características:**

-   IDs usando ULID (26 chars, ordenables, URL-friendly)
-   Timestamps con precisión de milisegundos
-   Validaciones a nivel DB (CHECKs)
-   Idempotencia por fingerprint único
-   Jerarquía con FK para integridad referencial

---

## Arquitectura

```
src/
├── app.py                      # Punto de entrada Flask
├── exceptions.py               # Excepciones personalizadas
├── routes/
│   └── transactions.py         # Endpoints HTTP
├── services/
│   └── transaction_service.py  # Lógica de negocio
├── db/
│   ├── connection.py           # Connection pool
│   └── queries.py              # Queries SQL
└── utils/
    ├── helpers.py              # ULID, fingerprint
    └── json_utils.py           # Serialización ISO 8601
```

**Flujo de capas:**

```
HTTP Request → Routes → Services → DB Queries → MySQL
             ↓          ↓           ↓
          Validación  Reglas de   Connection
           de input   negocio      Pool
```

---

## Comandos Útiles

```bash
# Ver logs
docker-compose logs -f app

# Detener
docker-compose down

# Reconstruir
docker-compose up -d --build

# Limpiar volúmenes
docker-compose down -v

# MySQL CLI (Docker)
docker exec -it asgard_db mysql -uasgard_user -pasgard_pass -D asgard_transactions

# Ejecutar tests (requiere .venv activado y Docker corriendo)
DB_HOST=localhost .venv/bin/pytest tests/ -v

# Tests con cobertura (87%)
DB_HOST=localhost .venv/bin/pytest tests/ --cov=src --cov-report=term-missing
```

---

## Stack Tecnológico

| Componente       | Tecnología  | Versión |
| ---------------- | ----------- | ------- |
| Lenguaje         | Python      | 3.11+   |
| Framework        | Flask       | 3.1.2   |
| Base de Datos    | MySQL       | 8.0     |
| ID Generation    | python-ulid | 3.0.0   |
| Containerización | Docker      | 20.10+  |

---

## Completado

-   [x] Arquitectura en 3 capas (routes/services/db)
-   [x] CRUD completo de transacciones
-   [x] Validación de reglas de negocio (AUTH→CAPTURE→REFUND)
-   [x] Idempotencia automática con fingerprint temporal (5 min)
-   [x] IDs usando ULID (ordenables, 26 chars)
-   [x] Timestamps con milisegundos (ISO 8601)
-   [x] Connection pooling con singleton
-   [x] Manejo de errores estructurado
-   [x] Validaciones a nivel DB (CHECKs)
-   [x] Serialización JSON custom (remove nulls)
-   [x] Docker Compose ready
-   [x] Tests unitarios

---

<div align="center">

**v1 Flask MVP**

[Ver proyecto](../../tree/main) · [Issues](../../issues)

</div>
