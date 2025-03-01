package kubernetes.gdpr

import data.kubernetes.namespaces

# Deny deployments without data protection labels
deny[msg] {
    input.kind == "Deployment"
    not input.metadata.labels["data-protection"]
    msg := sprintf("Deployment %s in namespace %s does not have a data-protection label", [input.metadata.name, input.metadata.namespace])
}

# Deny services exposing PII without proper protection
deny[msg] {
    input.kind == "Service"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["encryption"] == "enabled"
    msg := sprintf("Service %s in namespace %s contains PII but does not have encryption enabled", [input.metadata.name, input.metadata.namespace])
}

# Deny pods with PII data that don't have data retention policies
deny[msg] {
    input.kind == "Pod"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["data-retention-policy"]
    msg := sprintf("Pod %s in namespace %s contains PII but does not have a data retention policy", [input.metadata.name, input.metadata.namespace])
}

# Deny persistent volumes without encryption for PII data
deny[msg] {
    input.kind == "PersistentVolumeClaim"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["encryption"] == "enabled"
    msg := sprintf("PersistentVolumeClaim %s in namespace %s contains PII but does not have encryption enabled", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without data subject rights handling
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["data-subject-rights"]
    msg := sprintf("Deployment %s in namespace %s contains PII but does not handle data subject rights", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without data processing agreement reference
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["dpa-reference"]
    msg := sprintf("Deployment %s in namespace %s contains PII but does not reference a Data Processing Agreement", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without data breach notification mechanism
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["breach-notification"]
    msg := sprintf("Deployment %s in namespace %s contains PII but does not have a breach notification mechanism", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without data minimization
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["data-minimization"] == "implemented"
    msg := sprintf("Deployment %s in namespace %s contains PII but does not implement data minimization", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without purpose limitation
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["purpose-limitation"]
    msg := sprintf("Deployment %s in namespace %s contains PII but does not specify purpose limitation", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without lawful basis for processing
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["lawful-basis"]
    msg := sprintf("Deployment %s in namespace %s contains PII but does not specify lawful basis for processing", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without data accuracy measures
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["data-accuracy"] == "implemented"
    msg := sprintf("Deployment %s in namespace %s contains PII but does not implement data accuracy measures", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without storage limitation
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["storage-limitation"]
    msg := sprintf("Deployment %s in namespace %s contains PII but does not specify storage limitation", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without integrity and confidentiality measures
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["integrity-confidentiality"] == "implemented"
    msg := sprintf("Deployment %s in namespace %s contains PII but does not implement integrity and confidentiality measures", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without accountability measures
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["accountability"] == "implemented"
    msg := sprintf("Deployment %s in namespace %s contains PII but does not implement accountability measures", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without data protection impact assessment
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    input.metadata.labels["high-risk"] == "true"
    not input.metadata.labels["dpia-reference"]
    msg := sprintf("High-risk Deployment %s in namespace %s contains PII but does not reference a Data Protection Impact Assessment", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without data protection officer contact
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    not input.metadata.labels["dpo-contact"]
    msg := sprintf("Deployment %s in namespace %s contains PII but does not provide Data Protection Officer contact", [input.metadata.name, input.metadata.namespace])
}

# Deny deployments without cross-border transfer safeguards
deny[msg] {
    input.kind == "Deployment"
    input.metadata.labels["contains-pii"] == "true"
    input.metadata.labels["cross-border-transfer"] == "true"
    not input.metadata.labels["transfer-safeguards"]
    msg := sprintf("Deployment %s in namespace %s contains PII with cross-border transfer but does not implement transfer safeguards", [input.metadata.name, input.metadata.namespace])
}
