# NetME

## Deploy 
1. Clone repo
2. Into terminal, launch:
```
sudo ./init.sh
```

## Re-build UI
1. Pull for changes
2. Into terminal, launch:
```
docker-compose up -d --force-recreate --no-deps --build webapp
```

--------------------------------------------------------------------------------

## Configuration
IMPORTANT:
- change BUILD and DOMAIN var [click/adimaria] if you are using <b>standalone</b>
- change BUILD var [click/adimaria] if you are using <b>above-proxy</b>
<br>
### Local (insecure)
Serving webapp in localhost, via ```ng serve```.

### Local (secure)
Serving webapp in Docker, localhost TLS by Traefik.

### Stand-alone (secure) [netme.click, netme.adimaria.site] - Contabo, INFN
Traefik TLS proxy.

### Above proxy (Pisa)
Apache-Certbot TLS proxy above Traefik on another port (not the 80).