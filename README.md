# Estevez.Jor ERP 📊

Estevez.Jor ERP es un sistema empresarial basado en **Odoo** y desplegado con **Docker Compose**, 
diseñado para centralizar y optimizar la gestión de procesos clave como ventas, compras, inventario, contabilidad, reclutamiento, empleados.

## 🚀 Características principales

- **Gestión empresarial:** ventas, compras, inventario, facturación y CRM.  
- **Talento humano:** empleados, asistencias y reclutamiento.  
- **Productividad y organización:** calendario, conversaciones y tareas pendientes.  
- **Plataforma digital:** sitio web, encuestas y eLearning.

## ⚙️ Requisitos previos
- [Docker](https://www.docker.com/) instalado (v20 o superior)  
- [Docker Compose](https://docs.docker.com/compose/) instalado (v1.29 o superior)  
- Al menos **2 GB de RAM disponible**  

---

## 📦 Instalación y ejecución
1. Clonar el repositorio:
   ```bas
   git clone https://github.com/project-dev-estevez/erp-estevez-docker.git
   cd erp-estevez-docker

Levantar los contenedores:

docker-compose up -d

Acceder a Odoo en el navegador:

http://localhost:8069

## 🔑 Credenciales iniciales

Usuario: admin
Contraseña: admin

## 🐳 Administración de contenedores

Comandos útiles para gestionar el sistema:

- Ver logs en tiempo real:
docker-compose logs -f

- Reiniciar los contenedores:
docker-compose restart

- Detener los contenedores:
docker-compose down

- Detenerlos sin borrar datos (manteniendo volúmenes y configuración):
docker-compose stop

- Volver a iniciarlos:
docker-compose start


## 🛠 Tecnologías utilizadas

Odoo – Plataforma ER
PostgreSQL – Base de datos relacional
Docker – Contenerización
Docker Compose – Orquestación de servicios