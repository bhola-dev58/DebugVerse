variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS Region where Bedrock Claude 3.5 Sonnet is enabled"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment environment (production, staging)"
}

variable "ecr_repository_url" {
  type        = string
  default     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/debugverse-backend"
  description = "ECR repository URL for the backend Docker image"
}

variable "db_password" {
  type        = string
  default     = "DebugVerse_Secure_Prod_2026!"
  sensitive   = true
  description = "Master password for RDS PostgreSQL instance"
}

variable "redis_node_type" {
  type        = string
  default     = "cache.t4g.medium"
  description = "ElastiCache Redis node type"
}
