# Especificación — Infraestructura de producción del ERP

> Fuente de verdad para modernizar la infraestructura (SDD). Cada criterio tiene un ID
> `INFRA-NN` y se valida con una prueba o un procedimiento medible. **Prioridad del
> proyecto: ninguna otra mejora del ERP que toque el esquema se despliega hasta cerrar la fase 4.**

## 0. Retomar aquí

- **Estado (2026-11-02):** especificación escrita; nada construido todavía.
- **Siguiente acción:** fase 0. Respaldar la producción actual y reunir los datos de la sección 7.
- **Trabajo bloqueado por esta especificación:** el paso 2 de `auth_estevez`, guardado en
  `docs/wip/auth_estevez-paso2-backend.patch` (ver `custom_addons/auth_estevez/docs/spec.md`, sección 6).

## 1. Situación actual

| Aspecto | Hoy |
|---|---|
| Servidor | VM de Compute Engine, Odoo 18 en un venv de Python bajo systemd (`odoo18`, usuario `odoo18`) |
| Código en el servidor | `/opt/odoo18/odoo-erp-docker` (clon del repo) → `rsync` a `/opt/odoo18/odoo-erp/custom-addons/` |
| Deploy | `.github/workflows/deploy-erp.yml`: **cada push a `main`** → SSH → `git pull` → `rsync` (sin `--delete`) → `systemctl restart odoo18` |
| Base de datos | PostgreSQL; ubicación y versión **sin confirmar** (sección 7) |
| Respaldos | Ninguno automatizado conocido |
| DNS | GoDaddy |
| Local | Docker Compose (Odoo 18 + PostgreSQL 15 + pgAdmin): distinto a producción |

**Riesgos actuales:**
- R1. El deploy no respalda nada antes de cambiar el código.
- R2. El deploy no ejecuta `-u`: campos nuevos, vistas XML, datos y migraciones no se aplican.
  Si un cambio agrega campos, el ERP puede caerse.
- R3. Un push a `main` llega a producción sin pruebas ni aprobación.
- R4. Local y producción son distintos (Docker contra venv + systemd): "funciona en mi máquina".
- R5. La autenticación de GitHub con GCP usa una llave JSON de cuenta de servicio guardada como secreto.

## 2. Requisitos del negocio

| Requisito | Valor |
|---|---|
| Usuarios simultáneos | ~100 |
| Base de datos | Cloud SQL, empezar pequeño y escalar |
| Ventana para el cambio de servidor | Un día sin operación |
| DNS | Se queda en GoDaddy |
| Pérdida de datos aceptable (RPO) | Base: ≤ 5 min. Filestore: ≤ 24 h (más el respaldo previo a cada deploy) |
| Tiempo máximo de recuperación (RTO) | ≤ 1 h |

## 3. Arquitectura objetivo

```
Usuarios ──HTTPS──► IP estática ──► VM (Compute Engine, Docker Compose)
                                     ├─ caddy  : TLS automático; /websocket → odoo:8072, resto → odoo:8069
                                     └─ odoo   : imagen del repo (Artifact Registry), workers
                                         │  ├─ /var/lib/odoo ← disco persistente aparte (filestore)
                                         │  └─ IP privada (VPC)
                                         ▼
                                     Cloud SQL for PostgreSQL (sin IP pública, PITR)

GitHub Actions ─► pruebas ─► imagen:<sha> en Artifact Registry ─► deploy.sh en la VM (vía IAP)
Respaldos ─► Cloud SQL (automáticos + bajo demanda) · filestore en Cloud Storage · snapshots del disco
```

## 4. Decisiones

| ID | Decisión | Motivo | Alternativa descartada |
|---|---|---|---|
| D1 | Compute Engine + Docker Compose | Misma tecnología que en local; Odoo necesita filestore persistente, crons siempre activos y websockets | Cloud Run (sin disco persistente, crons y websockets forzados); GKE Autopilot (demasiado costo y complejidad para un solo ERP) |
| D2 | Cloud SQL for PostgreSQL, edición Enterprise, zonal, **2 vCPU / 8 GB** para empezar, SSD con aumento automático | Respaldos administrados y PITR; escalar es un cambio de tier con un reinicio corto | Instancias de núcleo compartido (sin SLA, poco para 100 usuarios); 1 vCPU (justo para 100 usuarios). Alta disponibilidad: activar después, es una opción |
| D3 | Conexión a Cloud SQL por IP privada (VPC), sin IP pública, `db_sslmode=require` | Sin exposición a internet y sin un contenedor extra | Cloud SQL Auth Proxy (opción válida si se prefiere autenticación por IAM) |
| D4 | VM `e2-standard-4` (4 vCPU / 16 GB), `workers = 9`, `max_cron_threads = 2` | Regla de Odoo: unos 6 usuarios activos por worker y `workers ≈ 2·CPU + 1`. Se valida con prueba de carga (INFRA-11); escalar es cambiar el tipo de máquina | — |
| D5 | Filestore en un disco persistente separado del de arranque, con snapshots diarios (14 días) | Sobrevive a reconstruir la VM; restauración rápida | Cloud Storage montado con FUSE (lento y frágil con Odoo) |
| D6 | Caddy como proxy inverso | HTTPS automático (Let's Encrypt) con configuración mínima | Nginx + certbot (más piezas) |
| D7 | Imagen Docker inmutable por commit (`:<sha>`) que incluye `custom_addons` y `third_party_addons` | Lo que se probó es exactamente lo que se despliega; rollback = imagen anterior | `git pull` + `rsync` en el servidor |
| D8 | GitHub → GCP con Workload Identity Federation; SSH por IAP | Sin llaves JSON de larga duración; SSH sin puerto 22 abierto | Llave JSON en secretos (situación actual) |
| D9 | Secretos en Secret Manager, inyectados por `deploy.sh` | Nada sensible en el repo ni en la imagen | `.env` copiado a mano |
| D10 | Infraestructura como código con Terraform (`infra/terraform/`) | Reproducible, revisable en PR, `plan` muestra el cambio antes de aplicarlo | Scripts `gcloud` (más simples, pero sin detectar diferencias) |
| D11 | El DNS se queda en GoDaddy; un registro A apunta a la IP estática de la VM | No hace falta migrar el dominio | Cloud DNS (opcional a futuro) |
| D12 | La misma versión mayor de PostgreSQL en local y en Cloud SQL (propuesta: 16; `pg_restore` exige destino ≥ origen) | Paridad entre entornos | — |
| D13 | `docker-compose.yml` sigue siendo el de desarrollo; `docker-compose.prod.yml` agrega lo de producción (Caddy, sin `--dev`, sin pgAdmin, workers) | Un solo Dockerfile, diferencias explícitas | Dos stacks separados |

## 5. Criterios de aceptación

### 5.1 Plataforma

- **INFRA-01 — Reproducible.** Todos los recursos de GCP (VPC, VM, disco, IP, Cloud SQL, bucket,
  Artifact Registry, cuentas de servicio, reglas de firewall) están en Terraform; tras `apply`,
  un `terraform plan` no muestra cambios.
- **INFRA-02 — Paridad.** Local y producción usan el mismo Dockerfile y las mismas versiones de
  Odoo, PostgreSQL (mayor) y dependencias de Python (`pandas`, `xlsxwriter`, `holidays`, …).
- **INFRA-03 — Red mínima.** Cloud SQL no tiene IP pública; la VM solo expone 80 y 443;
  SSH solo desde el rango de IAP (`35.235.240.0/20`).
- **INFRA-04 — HTTPS y websockets.** `http://` redirige a `https://`; el certificado es válido y se
  renueva solo; las notificaciones en tiempo real (Discuss) funcionan a través de `/websocket`.
- **INFRA-05 — Sin secretos expuestos.** Ninguna contraseña ni llave en el repo, en la imagen o en
  los logs; la llave JSON actual (`GCP_SA_KEY`) se elimina.
- **INFRA-06 — Odoo configurado para producción.** Sin `--dev`; `list_db = False`; `dbfilter`
  fijo a la base; `admin_passwd` fuerte; `proxy_mode = True`; `workers` según D4.

### 5.2 Despliegue

- **INFRA-07 — Respaldo antes de cada deploy.**
  Dado un deploy, antes de cambiar nada se crea un respaldo bajo demanda de Cloud SQL y un `tar`
  del filestore en Cloud Storage, ambos con el SHA del commit en el nombre o la descripción.
  Si cualquiera falla, el deploy se aborta sin tocar producción.
- **INFRA-08 — Actualización de módulos.**
  El deploy ejecuta `-u` de los módulos de `custom_addons`/`third_party_addons` que cambiaron
  desde el último SHA desplegado (guardado en la VM). Si `-u` falla, la versión nueva no se
  levanta, se vuelve a levantar la anterior y el deploy termina en error.
- **INFRA-09 — Verificación de salud.** Después de levantar, `/web/health` responde 200 en ≤ 120 s;
  si no, se vuelve a la imagen anterior y el deploy termina en error.
- **INFRA-10 — Pruebas antes de desplegar.** Los módulos con `tests/` se prueban en CI en cada PR
  y push a `main`; una prueba en rojo bloquea el deploy. (Las pruebas en rojo esperadas del
  refactor de `auth_estevez` se resuelven o se marcan antes de activar el bloqueo.)
- **INFRA-11 — Capacidad.** Una prueba de carga con 100 usuarios simulados (login, listas y
  formularios de empleados y asistencia) da p95 < 2 s, 0 errores 5xx y CPU de la VM < 70 %.

### 5.3 Datos y recuperación

- **INFRA-12 — Respaldos continuos.** Cloud SQL: respaldo automático diario (retención 14 días)
  y PITR (7 días). Filestore: snapshot diario (14 días). Semanalmente, un `pg_dump` lógico en
  Cloud Storage (portable, sirve para restaurar en local). Cloud Storage con reglas de ciclo de
  vida (30 días).
- **INFRA-13 — Recuperación probada.** Existe un procedimiento escrito para restaurar (PITR y
  filestore), y un simulacro restaura en un entorno aparte con tiempo medido ≤ 1 h.
- **INFRA-14 — Entornos de ensayo neutralizados.** Toda copia de producción fuera de producción se
  neutraliza (`odoo neutralize -d <db>`): sin correos, crons ni integraciones hacia usuarios reales.

### 5.4 Operación

- **INFRA-15 — Monitoreo.** Uptime check sobre `/web/health` y alertas por correo para: servicio
  caído, disco > 80 %, CPU de Cloud SQL > 80 % y fallo de respaldo. Logs de los contenedores en
  Cloud Logging (Ops Agent).

### 5.5 Migración desde la VM actual

- **INFRA-16 — Migración ensayada.** Al menos un ensayo completo (respaldo de la VM vieja →
  restauración en Cloud SQL y en el disco → `-u` → checklist funcional) con tiempos medidos,
  antes del día del cambio.
- **INFRA-17 — Checklist funcional.** En el entorno nuevo funcionan: login (todos los diseños de
  `auth_estevez`), empleados y organigrama, contratos, vacaciones e incapacidades, reportes XLSX de
  asistencia y nómina, reclutamiento, eLearning, adjuntos existentes (abren desde el filestore),
  Google Meet en calendario, correo saliente (solo el día del cambio) y crons.
- **INFRA-18 — Plan de retorno.** Hasta abrir el sistema a los usuarios, volver a la VM vieja
  (DNS de regreso + `systemctl start odoo18`) toma ≤ 15 min sin pérdida de datos.

## 6. Plan por fases

| Fase | Contenido | Criterios | Estado |
|---|---|---|---|
| 0 | **Protección inmediata**: respaldo manual de producción (runbook 8.1) + snapshot del disco de la VM. Recomendado: cambiar el trigger del workflow actual a `workflow_dispatch` (manual) para que un push a `main` no despliegue por accidente. Reunir los datos de la sección 7 | — | ⏳ |
| 1 | **Base de la plataforma**: Terraform (VPC, Cloud SQL, VM, disco, IP, bucket, Artifact Registry, Workload Identity Federation, Secret Manager) | 01, 03, 05 | ⏳ |
| 2 | **Imagen y stack**: Dockerfile con addons, `docker-compose.prod.yml`, Caddy, `odoo.conf` de producción, PostgreSQL local a la versión de D12 | 02, 04, 06 | ⏳ |
| 3 | **Pipeline**: CI de pruebas, build y push de la imagen, `deploy/deploy.sh` (respaldo → pull → `-u` → health → registro del SHA) y rollback | 07, 08, 09, 10 | ⏳ |
| 4 | **Ensayo** en un subdominio (por ejemplo `erp-nuevo.<dominio>`) con datos de producción neutralizados; prueba de carga; simulacro de restauración; monitoreo | 11, 12, 13, 14, 15, 16, 17 | ⏳ |
| 5 | **Cambio de servidor** (runbook 8.2) | 17, 18 | ⏳ |
| 6 | **Retiro**: VM vieja apagada 2 semanas, snapshot final guardado 90 días, después borrar; eliminar el workflow viejo y la llave `GCP_SA_KEY` | 05 | ⏳ |

## 7. Datos que faltan (obtener de la VM actual)

```bash
sudo systemctl cat odoo18                         # ExecStart: venv, ruta del .conf, ¿usa -u o --dev?
sudo grep -vE "pass" <ruta del .conf>             # db_name, db_host, db_port, data_dir, workers, addons_path
psql --version; sudo -u postgres psql -c "select version();"   # ¿PostgreSQL local? versión
sudo -u postgres psql -c "\l+"                    # bases y tamaños
sudo du -sh <data_dir>/filestore/*                # tamaño del filestore
/opt/odoo18/<venv>/bin/pip freeze                 # dependencias para la paridad (INFRA-02)
ls /opt/odoo18/odoo-erp/                          # ¿dónde están los third_party_addons en producción?
gcloud compute instances list                     # nombre, zona y tipo de la VM actual
```

Y además:
- Dominio exacto del ERP y quién tiene acceso a GoDaddy.
- Servidor de correo saliente que usa Odoo (para validarlo el día del cambio).
- Proyecto de GCP y región: proponer la misma región que la VM actual.

| Dato | Valor |
|---|---|
| Proyecto / región / zona | _pendiente_ |
| Versión de PostgreSQL de producción | _pendiente_ |
| Nombre y tamaño de la base | _pendiente_ |
| Tamaño del filestore | _pendiente_ |
| `ExecStart` de `odoo18` | _pendiente_ |
| Dominio | _pendiente_ |

## 8. Runbooks

### 8.1 Respaldo manual de la producción actual (fase 0)

En la VM actual, en un horario sin operación:

```bash
TS=$(date +%Y%m%d_%H%M); DB=<db_name>; DATA=<data_dir>
sudo mkdir -p /opt/odoo18/backups && cd /opt/odoo18/backups
sudo -u postgres pg_dump -Fc --no-owner --no-acl "$DB" > "${DB}_${TS}.dump"   # ajustar si la base no es local
sudo tar czf "filestore_${DB}_${TS}.tgz" -C "$DATA/filestore" "$DB"
ls -lh *"${TS}"*                                   # verificar que no estén vacíos
gcloud storage cp *"${TS}"* gs://<bucket>/manual/  # copia fuera de la VM
```

Además, un snapshot del disco: `gcloud compute disks snapshot <disco> --zone <zona> --snapshot-names pre-infra-$TS`.
**Probar que restaura** en local (`pg_restore` en una base nueva + filestore en el volumen `odoo-data`).

### 8.2 Día del cambio (fase 5)

1. Días antes: bajar el TTL del registro A en GoDaddy al mínimo permitido; avisar a los usuarios.
2. Detener la VM vieja: `systemctl stop odoo18` (a partir de aquí nadie escribe datos).
3. Respaldo final (8.1) y copia a Cloud Storage.
4. Restaurar en Cloud SQL: crear antes las extensiones que use la base (por ejemplo `unaccent`,
   `pg_trgm`); después `pg_restore --no-owner --role=<usuario_odoo> -j 4 -d <db>`.
5. Extraer el filestore en el disco persistente de la VM nueva.
6. `odoo -u all --stop-after-init` con la imagen nueva (alinea código y base). Ajustar `web.base.url`.
7. Levantar el stack; checklist INFRA-17 completo (con el subdominio o el archivo `hosts`).
8. Cambiar el registro A en GoDaddy a la IP nueva; esperar el certificado de Caddy; checklist rápido.
9. Abrir a los usuarios. **Desde aquí, volver atrás implica perder lo capturado en el sistema nuevo.**
10. Retorno (antes del paso 9): DNS a la IP vieja + `systemctl start odoo18`.

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| La versión de producción no coincide con el `main` actual | `-u all` en el ensayo y el día del cambio (paso 6) |
| Extensiones de PostgreSQL no disponibles en Cloud SQL | Verificarlo en el ensayo; Cloud SQL admite `unaccent` y `pg_trgm` |
| Workers mal dimensionados | Prueba de carga INFRA-11; el tipo de máquina se cambia en minutos |
| Filestore con RPO de 24 h | Respaldo antes de cada deploy (INFRA-07); evaluar snapshots más frecuentes si hace falta |
| Correos o crons desde el entorno de ensayo | INFRA-14 (neutralizar) |
