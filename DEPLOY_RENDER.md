# Instrucciones de Deployment en Render

## Pasos para desplegar en Render

### 1. Crear cuenta en Render
- Ir a https://render.com
- Registrarse con GitHub

### 2. Conectar repositorio
- Dashboard → New Web Service
- Conectar tu repositorio de GitHub (lujanf483/TUT0Hub)
- Seleccionar repositorio y rama `main`

### 3. Configurar servicio
- **Name**: tut0hub
- **Runtime**: Python 3.11
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn run:app`
- **Plan**: Free (o Starter si necesitas mejor performance)

### 4. Variables de entorno
En Settings → Environment, agregar todas las variables de `.env.example`:

```
SECRET_KEY=<genera-una-clave-segura>
JWT_SECRET_KEY=<genera-otra-clave-segura>
YOUTUBE_API_KEY=<tu-api-key-youtube>
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/tut0hub?retryWrites=true&w=majority
MONGODB_DBNAME=tut0hub
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=<tu-email>
MAIL_PASSWORD=<tu-app-password>
MAIL_DEFAULT_SENDER=<tu-email>
RECAPTCHA_PUBLIC_KEY=<tu-recaptcha-public>
RECAPTCHA_PRIVATE_KEY=<tu-recaptcha-private>
```

### 5. Base de datos
- Usa MongoDB Atlas: https://www.mongodb.com/cloud/atlas
- Crea un cluster gratuito
- Obtén la URI de conexión
- Agrega la URI en `MONGODB_URI`

### 6. Deploy
- Haz click en "Create Web Service"
- Render detectará automáticamente `render.yaml`
- El deployment comienza automáticamente

### 7. Verificar
- Ir a https://tut0hub.onrender.com (o tu dominio)
- Revisar logs en Render dashboard si hay errores

## Problemas comunes

**Error: "gunicorn not found"**
- Asegurar que `requirements.txt` tenga `gunicorn==20.1.0`

**Error: "Cannot connect to MongoDB"**
- Verificar MONGODB_URI
- Agregar IP de Render a MongoDB whitelist (0.0.0.0)

**Error: "Module not found"**
- Ejecutar: `pip freeze > requirements.txt` localmente
- Hacer git push

**Error 500 en deployment**
- Revisar logs en Render
- Verificar que todas las variables de entorno estén configuradas
