FROM odoo:18.0

USER root
RUN apt-get update && apt-get install -y python3-pandas
RUN apt-get update && apt-get install -y python3-xlsxwriter
RUN apt-get update && apt-get install -y python3-holidays
RUN apt-get update && apt-get install -y python3-docx
# Dependencias de odoo_mcp_manager (pydantic v2 y mcp no están en apt de Ubuntu 24.04)
# cryptography fijado a la versión de Ubuntu: versiones nuevas rompen el pyOpenSSL del sistema que usa Odoo
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed pydantic mcp "cryptography==41.0.7"
USER odoo