# Nginx and Certbot

Nginx has two scripts running. One is the entrypoint which creates a dummy certificate and starts the service while the other is a script that will reload nginx when a new certificate is created by certbot.
Certbot and Nginx have access to the bound volume where the certificates are saved, therefore Nginx will be notified when a certificate is renewed.