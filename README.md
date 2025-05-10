# installation

1. download climateNA 7.50 and climateBC 7.50

2. extract to C:\ and normalize directory names to:
   - C:\ClimateNA_v7.50
   - C:\ClimateBC_v7.50

3. clone `rogerlew/cliamtena-bc-fastapi` in `C:\ClimateNA_v7.50`

4. Test in VS Code and generate `api/.env` file

`api/.env`
```
JWT_SECRET=
ROOT_JWT=
WC_TOKEN=
API_BASE=https://climate-ca.bearhive.duckdns.org
```


# installing as a service
### in admin cmd

```
(climateBC-NA) C:\ClimateNA_v7.50\api>python climate_ca_api_service.py install
Installing service Climate_ca_API
Service installed

(climateBC-NA) C:\ClimateNA_v7.50\api>python climate_ca_api_service.py  --startup auto start
Starting service Climate_ca_API

(climateBC-NA) C:\ClimateNA_v7.50\api>
```