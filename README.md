<div align="center">

# Asgard Transactions API

### MVP Experimental · Laboratorio de Aprendizaje

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-MVP_Experimental-orange?style=for-the-badge)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-000000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1.svg?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)

**Microservicio experimental para aprender arquitecturas REST antes de construir el proyecto definitivo**

[El Plan](#-el-plan) · [Roadmap](#-roadmap) · [Stack](#-stack-tecnológico) · [Inicio Rápido](#-inicio-rápido)

---

</div>

## El Plan

Este proyecto es un **MVP experimental** diseñado para aprender construyendo el mismo servicio múltiples veces con diferentes tecnologías.

### ¿Por qué hacer esto?

**Objetivo principal:** Entender a fondo sistemas de transacciones y APIs REST experimentando con diferentes stacks tecnológicos antes de tomar decisiones para el proyecto definitivo.

**Estrategia:**
1. Construir el mismo servicio de transacciones 3-4 veces
2. Cada iteración usa una tecnología diferente (Flask → FastAPI → Go/Java/Rust)
3. Documentar aprendizajes, comparar rendimiento y complejidad
4. Identificar trade-offs de cada approach

**¿Qué pasa después?**
Una vez completadas las iteraciones y con el conocimiento adquirido, este componente se integrará como parte de un **ecosistema de microservicios mayor en AWS** (proyecto Asgard), aplicando las mejores prácticas aprendidas.

> **Nota importante:** Este NO es el proyecto final. Es un laboratorio de experimentación. El código aquí sirve para aprender, no para producción.

---

## ¿Qué es este servicio?

API REST para gestión de transacciones de pago que maneja operaciones básicas:

- **AUTH**: Autorización de pago
- **CAPTURE**: Captura de fondos autorizados
- **REFUND**: Devolución de transacciones

Incluye validación de reglas de negocio, idempotencia, y manejo de estados.

## Roadmap

El plan es iterar sobre el mismo servicio con diferentes tecnologías. **Este roadmap puede cambiar** según lo aprendido en cada fase.

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'fontSize':'16px'}}}%%
graph LR
    A[📦 Fase 1<br/>Flask + MySQL] --> B[⚡ Fase 2<br/>FastAPI + Async]
    B --> C[🔧 Fase 3<br/>Go/Java/Rust]
    C --> D[☁️ Fase 4<br/>Integración AWS]

    style A fill:#48bb78,stroke:#2f855a,stroke-width:3px,color:#000
    style B fill:#4299e1,stroke:#2b6cb0,stroke-width:2px,color:#000
    style C fill:#ed8936,stroke:#c05621,stroke-width:2px,color:#000
    style D fill:#9f7aea,stroke:#6b46c1,stroke-width:2px,color:#000
```

### Fase 1: Flask + MySQL (En Progreso)

**Stack:** ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white) ![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=mysql&logoColor=white)

**Objetivo:** Establecer la base funcional del servicio y comprender fundamentos de APIs REST de transacciones.

**Alcance:**
- Operaciones CRUD para transacciones
- Validación de reglas de negocio
- Idempotencia y manejo de estados
- Containerización básica

**Aprendizajes esperados:**
- Diseño de APIs REST
- Flujos de transacciones
- Patrones de validación
- Arquitectura de capas

---

### Fase 2: FastAPI + Async

**Stack:** ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)

**Objetivo:** Reescribir completamente el servicio para explorar programación asíncrona y comparar con el approach síncrono.

**Alcance:**
- Migración completa a FastAPI
- Operaciones async/await
- Validación con Pydantic
- Documentación OpenAPI automática
- Migración de MySQL a PostgreSQL

**Aprendizajes esperados:**
- Programación asíncrona en Python
- Diferencias de rendimiento sync vs async
- Trade-offs de validación con tipado fuerte
- Generación automática de docs

**Métricas a comparar:** Latencia, throughput, uso de recursos, complejidad del código

---

### Fase 3: Lenguaje Compilado

**Stack:** ![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white) o ![Java](https://img.shields.io/badge/Java-ED8B00?style=flat&logo=openjdk&logoColor=white) o ![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white)

**Objetivo:** Salir del ecosistema Python para entender trade-offs de lenguajes compilados.

**Alcance:**
- Reescritura completa en Go (o Java Spring Boot, o Rust)
- Explorar patrones de concurrencia nativos
- Optimización de recursos y latencia
- Comparativa con implementaciones Python

**Aprendizajes esperados:**
- Concurrencia nativa (goroutines, threads, async runtime)
- Gestión de memoria manual vs GC
- Ecosistema de herramientas
- Trade-offs de productividad vs performance

**Métricas a comparar:** Tiempo de desarrollo, curva de aprendizaje, rendimiento, tamaño de binarios

---

### Fase 4: Integración en Ecosistema AWS

**Stack:** ![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat&logo=amazon-aws&logoColor=white) ![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=flat&logo=terraform&logoColor=white) ![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)

**Objetivo:** Integrar el servicio (en la tecnología elegida) como componente del proyecto mayor Asgard con arquitectura de dominios.

**Alcance:**
- Arquitectura de microservicios en AWS
- Implementación de bounded contexts (DDD)
- Despliegue en ECS/EKS/Lambda
- API Gateway + Event-driven architecture
- Infraestructura como código (Terraform)
- CI/CD completo
- Observabilidad (CloudWatch, X-Ray, métricas)

**Aprendizajes esperados:**
- Domain-Driven Design en práctica
- Arquitectura distribuida
- Infraestructura cloud
- DevOps y automatización

**Resultado final:** Servicio de transacciones como componente productivo dentro del ecosistema Asgard

---

## Stack Tecnológico

### Actual (Fase 1)

<div align="center">

| Componente | Tecnología |
|:-----------|:----------:|
| **Lenguaje** | ![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat&logo=python&logoColor=white) |
| **Framework Web** | ![Flask](https://img.shields.io/badge/Flask_3.1.2-000000?style=flat&logo=flask&logoColor=white) |
| **Base de Datos** | ![MySQL](https://img.shields.io/badge/MySQL_8.0-4479A1?style=flat&logo=mysql&logoColor=white) |
| **Containerización** | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white) ![Compose](https://img.shields.io/badge/Compose-2496ED?style=flat&logo=docker&logoColor=white) |
| **Workflow** | ![Git](https://img.shields.io/badge/Git-F05032?style=flat&logo=git&logoColor=white) ![GitFlow](https://img.shields.io/badge/GitFlow-F05032?style=flat&logo=git&logoColor=white) |

</div>

### Tecnologías Futuras Contempladas

<details>
<summary><b>Ver roadmap de tecnologías</b></summary>

<br>

**Fase 2 - FastAPI:**
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat)

**Fase 3 - Lenguaje Compilado:**
![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)
![Java](https://img.shields.io/badge/Java-ED8B00?style=flat&logo=openjdk&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-6DB33F?style=flat&logo=spring-boot&logoColor=white)
![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white)

**Fase 4 - Cloud & DevOps:**
![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat&logo=amazon-aws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=flat&logo=terraform&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)

</details>

---

## Estado Actual

**Fase:** 1 - Flask MVP
**Progreso:** ![](https://img.shields.io/badge/Completado-45%25-yellow?style=flat)

### Implementado

- [x] Estructura base del proyecto
- [x] Configuración Docker Compose
- [x] Schema de base de datos
- [x] Endpoint POST `/transactions` (AUTH, CAPTURE, REFUND)
- [x] Validación de reglas de negocio
- [x] Idempotencia (`merchant_id` + `order_reference`)
- [x] Connection pooling MySQL

### Pendiente

- [ ] Endpoints GET (consulta de transacciones)
- [ ] Endpoints PATCH (actualización de estado)
- [ ] Tests unitarios y de integración
- [ ] Documentación OpenAPI
- [ ] Logging estructurado
- [ ] Manejo avanzado de errores

---

## Inicio Rápido

### Prerequisitos

![Docker](https://img.shields.io/badge/Docker-20.10+-2496ED?style=flat&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-1.29+-2496ED?style=flat&logo=docker&logoColor=white)

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/KatzeeDev/asgard-transactions-api-rest.git
cd asgard-transactions-api-rest

# Levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f app

# Verificar estado
docker-compose ps
```

---

## Estructura del Proyecto

```
asgard-transactions-api-rest/
│
├── src/                    # Código fuente
│   ├── app.py             # Aplicación Flask y rutas
│   ├── db.py              # Capa de acceso a datos
│   └── utils.py           # Utilidades
│
├── db/                     # Scripts de base de datos
│   └── init.sql           # Schema DDL
│
├── docker-compose.yml      # Orquestación de servicios
├── Dockerfile             # Imagen Docker
└── requirements.txt       # Dependencias Python
```

---

## Workflow de Desarrollo

**Estrategia:** GitFlow

| Branch | Propósito |
|:-------|:----------|
| `main` | Releases estables |
| `develop` | Desarrollo activo |
| `feature/*` | Nuevas funcionalidades |
| `hotfix/*` | Correcciones urgentes |

---

<div align="center">

**Proyecto experimental de aprendizaje**

![Made with](https://img.shields.io/badge/Made_with-Python-3776AB?style=flat&logo=python&logoColor=white)
![Built with](https://img.shields.io/badge/Built_with-Flask-000000?style=flat&logo=flask&logoColor=white)
![Powered by](https://img.shields.io/badge/Powered_by-Docker-2496ED?style=flat&logo=docker&logoColor=white)

</div>
