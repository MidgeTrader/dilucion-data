# Configuración de la IA

Guía para poner **tus** claves y elegir el proveedor. Si has hecho un fork o una copia de este
repositorio, aquí empieza todo: el proyecto **no trae claves** y no funcionará con las de nadie.

---

## 1. Qué hace la IA dentro del proyecto

Hay **dos piezas distintas**, y conviene no confundirlas porque pueden usar proveedores diferentes:

| Pieza | Para qué | Variable de clave | Endpoint |
|---|---|---|---|
| **Chat (LLM)** | Responder preguntas, resumir filings, extraer eventos, redactar reportes | `LLM_API_KEY` | `LLM_BASE_URL` |
| **Embeddings** | Convertir el texto de los filings en vectores para poder buscar dentro de ellos | `OPENAI_API_KEY` | `EMBEDDING_BASE_URL` |

El RAG necesita **las dos**. Si falta una, el motor no arranca (`validate_rag_keys`).

Por debajo: LangChain + ChromaDB para el almacén vectorial, y el cliente `ChatOpenAI` para el chat —
que habla el **protocolo de OpenAI**, así que sirve cualquier proveedor compatible.

---

## 2. Lo mínimo para arrancar

```sh
cp backend/.env.example backend/.env
chmod 600 backend/.env
```

Y rellena estas dos:

```ini
LLM_API_KEY=tu_clave_del_chat
OPENAI_API_KEY=tu_clave_de_openai
```

Con eso y nada más ya funciona: el resto de valores tienen un defecto sensato y el chat apunta a
DeepSeek.

Comprobación rápida:

```sh
cd backend
.venv/bin/python main.py rag AAPL --prompt warrants
```

Si responde con citas, está bien montado.

---

## 3. Recetas por proveedor

### DeepSeek (lo que viene por defecto)

```ini
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
LLM_REASONING_MODEL=deepseek-reasoner
LLM_API_KEY=sk-tu_clave_deepseek
OPENAI_API_KEY=sk-tu_clave_openai      # los embeddings siguen en OpenAI
```

Si prefieres la variable antigua, `DEEPSEEK_API_KEY` sigue funcionando como atajo de `LLM_API_KEY`.

### OpenAI para todo

```ini
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_REASONING_MODEL=gpt-4o
LLM_API_KEY=sk-tu_clave_openai
OPENAI_API_KEY=sk-tu_clave_openai      # la misma clave sirve para las dos piezas
```

Con `LLM_API_KEY` y `OPENAI_API_KEY` iguales, todo va a OpenAI.

### Groq

```ini
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_REASONING_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_tu_clave_groq
OPENAI_API_KEY=sk-tu_clave_openai      # Groq no da embeddings: siguen en OpenAI
```

### Ollama (local, sin coste)

```ini
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.1
LLM_REASONING_MODEL=llama3.1
LLM_API_KEY=ollama                     # Ollama no valida la clave, pero el campo no puede ir vacío

EMBEDDING_BASE_URL=http://localhost:11434/v1
EMBEDDING_MODEL=nomic-embed-text
OPENAI_API_KEY=ollama
```

Todo queda en tu máquina: útil si no quieres enviar filings a un tercero.

> Los endpoints de Groq, Together y compañía cambian de vez en cuando. Si un `base_url` deja de
> responder, compruébalo en la documentación del proveedor antes de tocar el código.

---

## 4. Variables, una por una

| Variable | Obligatoria | Defecto | Qué hace |
|---|---|---|---|
| `LLM_API_KEY` | Sí* | — | Clave del chat. *Si está vacía se usa `DEEPSEEK_API_KEY` |
| `LLM_BASE_URL` | No | `https://api.deepseek.com/v1` | Endpoint compatible con OpenAI |
| `LLM_MODEL` | No | `deepseek-chat` | Modelo para el trabajo normal |
| `LLM_REASONING_MODEL` | No | `deepseek-reasoner` | Modelo para convertibles, donde importa el razonamiento |
| `DEEPSEEK_API_KEY` | No | — | Atajo heredado de `LLM_API_KEY` |
| `OPENAI_API_KEY` | Sí | — | Embeddings |
| `EMBEDDING_MODEL` | No | `text-embedding-3-small` | Modelo de embeddings |
| `EMBEDDING_BASE_URL` | No | (OpenAI) | Servidor de embeddings alternativo |

## 5. Coste aproximado

El gasto real está en los **embeddings** y en el tamaño de los filings, no en las preguntas:

- Un filing de 8-K típico son 5–15 chunks. Con `text-embedding-3-small` eso son **céntimos de dólar
  por cada centenar de filings**.
- El chat solo se invoca al preguntar o al generar un reporte.
- Todo el resultado se cachea en SQLite (`data/api_cache.sqlite`) y en ChromaDB: **repetir una
  consulta no vuelve a costar**.

Si estás probando, usa `LLM_MODEL` barato y no lances el monitor RSS en bucle.

## 6. Errores comunes

| Síntoma | Causa |
|---|---|
| `LLM_API_KEY (or DEEPSEEK_API_KEY) is required` | Falta la clave del chat |
| `OPENAI_API_KEY is required for embeddings` | Falta la clave de embeddings |
| `401 Invalid API key` | Clave de otro proveedor, o `base_url` que no corresponde a esa clave |
| `404 model not found` | El `LLM_MODEL` no existe en ese proveedor |
| Respuestas vacías o `[]` | El modelo no devuelve JSON válido. Prueba uno más grande |
| Todo va lentísimo | Modelo local sin GPU, o proveedor con rate limit |

## 7. Seguridad de las claves

- `backend/.env` está en `.gitignore`. **No lo quites de ahí.**
- `chmod 600 backend/.env` — que solo lo pueda leer tu usuario.
- Nunca pegues claves en un commit, en un issue ni en una captura.
- Si una clave se te escapa: **rótala en el panel del proveedor**. Borrarla del repo no basta, porque
  el historial de git y las copias que otros tengan seguirán teniéndola.
- Antes de publicar un fork:

  ```sh
  git log -p | grep -iE "api_key|token|secret|sk-" | head
  ```
