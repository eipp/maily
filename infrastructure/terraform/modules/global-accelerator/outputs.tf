output "accelerator_id" {
  description = "The ID of the Global Accelerator"
  value       = aws_globalaccelerator_accelerator.maily_accelerator.id
}

output "accelerator_dns_name" {
  description = "The DNS name of the Global Accelerator"
  value       = aws_globalaccelerator_accelerator.maily_accelerator.dns_name
}

output "accelerator_ip_sets" {
  description = "The IP address set of the Global Accelerator"
  value       = aws_globalaccelerator_accelerator.maily_accelerator.ip_sets
}

output "listener_id" {
  description = "The ID of the Global Accelerator listener"
  value       = aws_globalaccelerator_listener.http_listener.id
}

output "primary_endpoint_group_id" {
  description = "The ID of the primary endpoint group"
  value       = aws_globalaccelerator_endpoint_group.primary_endpoint_group.id
}

output "secondary_endpoint_group_id" {
  description = "The ID of the secondary endpoint group"
  value       = aws_globalaccelerator_endpoint_group.secondary_endpoint_group.id
}

output "dns_record_name" {
  description = "The name of the DNS record for the Global Accelerator"
  value       = var.create_dns_record ? aws_route53_record.global_accelerator[0].name : null
}

output "dns_record_fqdn" {
  description = "The FQDN of the DNS record for the Global Accelerator"
  value       = var.create_dns_record ? aws_route53_record.global_accelerator[0].fqdn : null
}

output "primary_traffic_dial" {
  description = "The traffic dial percentage for the primary region"
  value       = var.primary_traffic_dial
}

output "secondary_traffic_dial" {
  description = "The traffic dial percentage for the secondary region"
  value       = var.secondary_traffic_dial
}

output "primary_region" {
  description = "The primary AWS region"
  value       = var.primary_region
}

output "secondary_region" {
  description = "The secondary AWS region"
  value       = var.secondary_region
}

output "availability_alarm_id" {
  description = "The ID of the availability alarm"
  value       = aws_cloudwatch_metric_alarm.accelerator_availability.id
}

output "processed_bytes_alarm_id" {
  description = "The ID of the processed bytes alarm"
  value       = aws_cloudwatch_metric_alarm.accelerator_processed_bytes.id
}
