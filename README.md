# Infinitools API

API REST para ejecutar comandos de la herramienta Infinitools.

## Endpoints disponibles

### ToBeta
Mover empresas entre entornos usando el comando `tobeta`:
- `POST /to_beta` - Mover empresas al entorno beta
- `POST /to_master` - Mover empresas al entorno master

## Instalación

### 1. Crear y activar entorno virtual (recomendado)

```bash
cd infinitools-api

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate

# En Windows:
# venv\Scripts\activate
```

### 2. Copiar archivos de configuración

```bash
cp .env.example .env
```

### 3. Configurar variables de entorno

Edita el archivo `.env`:

```bash
# Requerido: Tu API Key secreta
API_KEY=tu-clave-secreta-aqui

# Ambiente (dev o prod)
ENV=dev

# Ruta al proyecto Go (para desarrollo)
GO_PROJECT_PATH=../infinitools
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Uso

### Iniciar el servidor

```bash
# Desarrollo
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Uso de la API

### Health Check

```bash
GET /
GET /health
```

Respuesta:
```json
{
  "status": "healthy",
  "environment": "dev"
}
```

---

### ToBeta - Mover empresas entre entornos

#### POST /to_beta

**Headers:**
- `X-API-Key`: Tu API Key (requerido)
- `Content-Type`: application/json

**Body:**
```json
{
  "ids": "123,456,789",
  "git_user": "github-actions",
  "motive": "Automated deployment"
}
```

**Parámetros:**
- `ids` (string, requerido): IDs de empresas separados por comas
- `git_user` (string, opcional): Usuario GitHub (default: "github-actions")
- `motive` (string, opcional): Motivo del cambio (default: "Automated deployment")

**Respuesta exitosa:**
```json
{
  "message": "Processed 3 company(ies) to beta environment",
  "total": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "success": true,
      "cpn": 123,
      "country_code": "CL",
      "output": "Empresa movida exitosamente..."
    },
    {
      "success": true,
      "cpn": 456,
      "country_code": "AR",
      "output": "Empresa movida exitosamente..."
    },
    {
      "success": false,
      "cpn": 789,
      "error": "Error al mover empresa..."
    }
  ]
}
```

#### POST /to_master

Mismos parámetros y formato que `/to_beta`.

#### Ejemplos de uso

**Con curl:**

```bash
# Mover a beta
curl -X POST http://localhost:8000/to_beta \
  -H "X-API-Key: tu-clave-secreta" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": "123,456",
    "git_user": "github-actions",
    "motive": "Deploy to beta"
  }'

# Mover a master
curl -X POST http://localhost:8000/to_master \
  -H "X-API-Key: tu-clave-secreta" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": "123,456",
    "motive": "Deploy to production"
  }'
```

**Desde GitHub Actions:**

```yaml
name: Deploy to Beta

on:
  workflow_dispatch:
    inputs:
      company_ids:
        description: 'Company IDs (comma-separated)'
        required: true
        type: string

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Move companies to beta
        run: |
          curl -X POST ${{ secrets.INFINITOOLS_API_URL }}/to_beta \
            -H "X-API-Key: ${{ secrets.INFINITOOLS_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d "{
              \"ids\": \"${{ github.event.inputs.company_ids }}\",
              \"git_user\": \"${{ github.actor }}\",
              \"motive\": \"Deployment via GitHub Actions\"
            }"
```

---

## Documentación interactiva

Una vez iniciado el servidor, puedes acceder a la documentación interactiva:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Estructura del proyecto

```
infinitools-api/
├── main.py           # Aplicación FastAPI y endpoints
├── config.py         # Configuración y variables de entorno
├── utils.py          # Utilidades y ejecución de comandos
├── requirements.txt  # Dependencias Python
├── .env.example      # Ejemplo de configuración
└── README.md         # Esta documentación
```

## Configuración para producción

1. **Variables de entorno:**
```bash
ENV=prod
API_KEY=clave-super-secreta-produccion
PROD_EXECUTABLE_PATH=/app/infinitools
PROD_EXECUTABLE_NAME=infinitools
```

2. **Ejecutar con múltiples workers:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

3. **Usar con Docker (opcional):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Manejo de errores

- `401 Unauthorized`: API Key inválida o faltante
- `422 Unprocessable Entity`: Datos de entrada inválidos
- `500 Internal Server Error`: Error en la ejecución del comando

## Desarrollo

Para desarrollo local:

1. Activa el entorno virtual: `source venv/bin/activate` (si lo creaste)
2. Asegúrate de tener el proyecto Go en la ruta correcta (configurada en `GO_PROJECT_PATH`)
3. El API usará `go run main.go` para ejecutar comandos
4. Usa `--reload` en uvicorn para hot-reloading
