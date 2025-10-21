FROM odoo:18.0

USER root
RUN apt-get update && apt-get install -y python3-pandas
RUN apt-get update && apt-get install -y python3-xlsxwriter
USER odoo