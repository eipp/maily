{
  "redis": {
    "host": "{{ with secret "secret/data/redis" }}{{ .Data.data.host }}{{ end }}",
    "port": {{ with secret "secret/data/redis" }}{{ .Data.data.port }}{{ end }},
    "password": "{{ with secret "secret/data/redis" }}{{ .Data.data.password }}{{ end }}",
    "database": {{ with secret "secret/data/redis" }}{{ .Data.data.database }}{{ end }}
  }
}
