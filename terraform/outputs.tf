output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "Public application load balancer endpoint address"
}

output "rds_endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "PostgreSQL DB instance endpoint connection string"
}

output "redis_endpoint" {
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  description = "Redis ElastiCache connection host"
}
