#!/bin/bash
set -e

LOGFILE="/tmp/deploy-erp.log"

echo "Directorio actual:"        | tee "$LOGFILE"
pwd                             | tee -a "$LOGFILE"

echo "📁 Listando contenido del directorio actual:" | tee -a "$LOGFILE"
ls -la                          | tee -a "$LOGFILE"

echo "📁 Listando contenido del home de odoo18:"   | tee -a "$LOGFILE"
sudo su - odoo18 -c 'ls -la $HOME' | tee -a "$LOGFILE"

echo "==== CONTENIDO DEL LOG ===="
cat "$LOGFILE"