package kubernetes.security

# Deny containers with privileged mode
deny[msg] {
    input.kind == "Pod"
    input.spec.containers[i].securityContext.privileged == true
    msg := sprintf("Container %s in Pod %s is running in privileged mode", [input.spec.containers[i].name, input.metadata.name])
}

# Deny containers that run as root
deny[msg] {
    input.kind == "Pod"
    not input.spec.securityContext.runAsNonRoot == true
    not input.spec.containers[i].securityContext.runAsNonRoot == true
    msg := sprintf("Container %s in Pod %s is running as root", [input.spec.containers[i].name, input.metadata.name])
}

# Deny containers without resource limits
deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[i]
    not container.resources.limits
    msg := sprintf("Container %s in Pod %s does not have resource limits", [container.name, input.metadata.name])
}

# Deny containers without readiness probes
deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[i]
    not container.readinessProbe
    msg := sprintf("Container %s in Pod %s does not have a readiness probe", [container.name, input.metadata.name])
}

# Deny containers without liveness probes
deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[i]
    not container.livenessProbe
    msg := sprintf("Container %s in Pod %s does not have a liveness probe", [container.name, input.metadata.name])
}

# Deny containers with hostPath volumes
deny[msg] {
    input.kind == "Pod"
    volume := input.spec.volumes[i]
    volume.hostPath
    msg := sprintf("Pod %s uses a hostPath volume %s", [input.metadata.name, volume.name])
}

# Deny containers with hostNetwork
deny[msg] {
    input.kind == "Pod"
    input.spec.hostNetwork == true
    msg := sprintf("Pod %s uses host network", [input.metadata.name])
}

# Deny containers with hostPID
deny[msg] {
    input.kind == "Pod"
    input.spec.hostPID == true
    msg := sprintf("Pod %s uses host PID", [input.metadata.name])
}

# Deny containers with hostIPC
deny[msg] {
    input.kind == "Pod"
    input.spec.hostIPC == true
    msg := sprintf("Pod %s uses host IPC", [input.metadata.name])
}

# Deny containers with capabilities beyond default
deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[i]
    container.securityContext.capabilities.add
    msg := sprintf("Container %s in Pod %s has additional capabilities: %v", [container.name, input.metadata.name, container.securityContext.capabilities.add])
}

# Require containers to drop all capabilities
deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[i]
    not container.securityContext.capabilities.drop
    msg := sprintf("Container %s in Pod %s does not drop any capabilities", [container.name, input.metadata.name])
}

deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[i]
    not array_contains(container.securityContext.capabilities.drop, "ALL")
    msg := sprintf("Container %s in Pod %s does not drop ALL capabilities", [container.name, input.metadata.name])
}

# Deny containers with allowPrivilegeEscalation
deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[i]
    container.securityContext.allowPrivilegeEscalation == true
    msg := sprintf("Container %s in Pod %s allows privilege escalation", [container.name, input.metadata.name])
}

# Deny containers without readOnlyRootFilesystem
deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[i]
    not container.securityContext.readOnlyRootFilesystem == true
    msg := sprintf("Container %s in Pod %s does not have a read-only root filesystem", [container.name, input.metadata.name])
}

# Helper function to check if an array contains a value
array_contains(array, value) {
    array[_] == value
}
