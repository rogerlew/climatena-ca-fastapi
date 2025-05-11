# climatena-ca-fastapi

Provides self-hosted web api for [ClimateNA.ca](https://climatena.ca)  scale-free climate models.


# Installation

1. Download climateNA 7.50 and climateBC 7.50

2. Extract to C:\ and normalize directory names to:
   - C:\ClimateNA_v7.50
   - C:\ClimateBC_v7.50

3. Clone `rogerlew/cliamtena-bc-fastapi` in `C:\ClimateNA_v7.50`

4. Test in VS Code and generate `api/.env` file

`api/.env`
```
JWT_SECRET=
ROOT_JWT=
WC_TOKEN=
API_BASE=https://climatena-ca.bearhive.duckdns.org
```


# Installing as a service

### In admin cmd
```
(climateBC-NA) C:\ClimateNA_v7.50\api>python climate_ca_api_service.py  --startup auto start install
```

### start (7x slower than debug)

```
(climateBC-NA) C:\ClimateNA_v7.50\api>python climate_ca_api_service.py  start
```

### debug
```
(climateBC-NA) C:\ClimateNA_v7.50\api>python climate_ca_api_service.py  debug
```
