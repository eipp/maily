pid_file = "/vault/agent-data/vault-agent.pid"

vault {
  address = "https://vault:8200"
  tls_skip_verify = true  # Only for testing, remove in production
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path = "/vault/agent-config/role-id"
      secret_id_file_path = "/vault/agent-config/secret-id"
      remove_secret_id_file_after_reading = false
    }
  }

  sink "file" {
    config = {
      path = "/vault/agent-data/token"
    }
  }
}

cache {
  use_auto_auth_token = true
}

listener "tcp" {
  address = "0.0.0.0:8100"
  tls_disable = true  # Only for internal use
}

template {
  source      = "/vault/agent-config/templates/db-creds.tpl"
  destination = "/vault/agent-data/db-creds.json"
  perms       = 0400
}

template {
  source      = "/vault/agent-config/templates/redis-creds.tpl"
  destination = "/vault/agent-data/redis-creds.json"
  perms       = 0400
}
