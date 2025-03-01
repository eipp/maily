package kubernetes.canspam

# Deny email services without required CAN-SPAM compliance labels
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["can-spam-compliant"] == "true"
    msg := sprintf("Email service deployment %s in namespace %s is not marked as CAN-SPAM compliant", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without unsubscribe mechanism
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["unsubscribe-mechanism"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s does not implement an unsubscribe mechanism", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without physical address inclusion
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["physical-address-inclusion"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s does not implement physical address inclusion", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without clear identification
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["sender-identification"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s does not implement clear sender identification", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without honest subject lines
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["honest-subject-lines"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s does not implement honest subject line policy", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without opt-out honor mechanism
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["opt-out-honor"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s does not implement opt-out honor mechanism", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without monitoring of third-party compliance
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    input.metadata.labels["uses-third-party"] == "true"
    not input.metadata.labels["third-party-compliance-monitoring"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s uses third parties but does not monitor their compliance", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without commercial content identification
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    input.metadata.labels["commercial-content"] == "true"
    not input.metadata.labels["commercial-content-identification"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s sends commercial content but does not identify it as such", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without opt-in verification
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["opt-in-verification"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s does not implement opt-in verification", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without suppression list management
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["suppression-list-management"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s does not implement suppression list management", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without record keeping
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["record-keeping"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s does not implement record keeping", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without compliance monitoring
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["compliance-monitoring"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s does not implement compliance monitoring", [input.metadata.name, input.metadata.namespace])
}

# Deny email services without complaint handling
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["service-type"] == "email"
    not input.metadata.labels["complaint-handling"] == "implemented"
    msg := sprintf("Email service deployment %s in namespace %s does not implement complaint handling", [input.metadata.name, input.metadata.namespace])
}
