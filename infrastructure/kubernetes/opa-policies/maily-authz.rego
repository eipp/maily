package maily.authz

# Default deny
default allow = false

# Allow access if the user has the required role
allow {
    # Check if the user has the admin role
    has_role(input.user, "admin")
}

# Allow access if the user is the owner of the resource
allow {
    # Check if the resource has an owner field
    input.context.resource_owner

    # Check if the user is the owner
    input.context.resource_owner == input.user.sub
}

# Allow access based on specific resource and action combinations
allow {
    # Public resources that anyone can read
    input.action == "read"
    input.resource == "public_content"
}

# Allow users to read their own data
allow {
    input.action == "read"
    input.resource == "user_data"
    input.resource_id == input.user.sub
}

# Allow users to update their own data
allow {
    input.action == "update"
    input.resource == "user_data"
    input.resource_id == input.user.sub
}

# Allow users with the "editor" role to create and update content
allow {
    has_role(input.user, "editor")
    input.action in ["create", "update"]
    input.resource in ["content", "campaign", "template"]
}

# Allow users with the "viewer" role to read content
allow {
    has_role(input.user, "viewer")
    input.action == "read"
    input.resource in ["content", "campaign", "template", "analytics"]
}

# Allow users with the "analyst" role to read analytics
allow {
    has_role(input.user, "analyst")
    input.action == "read"
    input.resource == "analytics"
}

# Helper function to check if a user has a specific role
has_role(user, role) {
    # Check in the roles claim
    user.roles[_] == role
}

has_role(user, role) {
    # Check in the permissions claim
    user.permissions[_] == role
}

has_role(user, role) {
    # Check in the Auth0 custom namespace
    user["https://maily.com/roles"][_] == role
}

# Endpoint for getting allowed resources
allowed_resources[resource_id] {
    # Get all resources of the specified type
    resource_id := data.resources[input.resource][_].id

    # Check if the user has permission to access the resource
    allow with input as {
        "user": input.user,
        "action": input.action,
        "resource": input.resource,
        "resource_id": resource_id,
        "context": input.context
    }
}

# Endpoint for bulk permission checking
decisions[key] = decision {
    # For each permission in the input
    permission := input.permissions[_]

    # Create a key for the permission
    key := concat(":", [permission.action, permission.resource, permission.resource_id])

    # Check if the user has permission
    decision := allow with input as {
        "user": input.user,
        "action": permission.action,
        "resource": permission.resource,
        "resource_id": permission.resource_id,
        "context": input.context
    }
}
