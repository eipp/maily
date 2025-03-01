{
  "db": {
    "username": "{{ with secret "database/creds/api-service" }}{{ .Data.username }}{{ end }}",
    "password": "{{ with secret "database/creds/api-service" }}{{ .Data.password }}{{ end }}",
    "host": "{{ with secret "secret/data/api/database" }}{{ .Data.data.host }}{{ end }}",
    "port": {{ with secret "secret/data/api/database" }}{{ .Data.data.port }}{{ end }},
    "database": "{{ with secret "secret/data/api/database" }}{{ .Data.data.database }}{{ end }}"
  }
}
