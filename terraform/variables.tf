variable "aws_region" {
  type        = string
  description = "AWS deployment region"
  default     = "us-east-1"
}

variable "db_password" {
  type        = string
  description = "RDS Postgres master password"
  sensitive   = true
}

variable "openai_api_key" {
  type        = string
  description = "OpenAI security API key"
  sensitive   = true
}

variable "secret_key" {
  type        = string
  description = "Backend JWT secret passphrase"
  sensitive   = true
}

variable "ecr_backend_url" {
  type        = string
  description = "ECR Docker repository URL for Backend"
}

variable "ecr_frontend_url" {
  type        = string
  description = "ECR Docker repository URL for Frontend"
}
