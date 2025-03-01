output "mesh_id" {
  description = "The ID of the App Mesh service mesh"
  value       = aws_appmesh_mesh.maily_mesh.id
}

output "mesh_name" {
  description = "The name of the App Mesh service mesh"
  value       = aws_appmesh_mesh.maily_mesh.name
}

output "api_virtual_service_name" {
  description = "The name of the API virtual service"
  value       = aws_appmesh_virtual_service.api.name
}

output "web_virtual_service_name" {
  description = "The name of the Web virtual service"
  value       = aws_appmesh_virtual_service.web.name
}

output "primary_api_virtual_node_name" {
  description = "The name of the primary API virtual node"
  value       = aws_appmesh_virtual_node.primary_api.name
}

output "primary_web_virtual_node_name" {
  description = "The name of the primary Web virtual node"
  value       = aws_appmesh_virtual_node.primary_web.name
}

output "secondary_api_virtual_node_name" {
  description = "The name of the secondary API virtual node"
  value       = aws_appmesh_virtual_node.secondary_api.name
}

output "secondary_web_virtual_node_name" {
  description = "The name of the secondary Web virtual node"
  value       = aws_appmesh_virtual_node.secondary_web.name
}

output "api_router_name" {
  description = "The name of the API virtual router"
  value       = aws_appmesh_virtual_router.api_router.name
}

output "web_router_name" {
  description = "The name of the Web virtual router"
  value       = aws_appmesh_virtual_router.web_router.name
}

output "api_route_name" {
  description = "The name of the API route"
  value       = aws_appmesh_route.api_route.name
}

output "web_route_name" {
  description = "The name of the Web route"
  value       = aws_appmesh_route.web_route.name
}

output "primary_region" {
  description = "The primary AWS region"
  value       = var.primary_region
}

output "secondary_region" {
  description = "The secondary AWS region"
  value       = var.secondary_region
}
