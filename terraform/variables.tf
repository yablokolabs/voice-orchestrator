variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "voice-orchestrator"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "voice_orchestrator"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "voice"
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "api_image_uri" {
  description = "Docker image URI for the API"
  type        = string
  default     = ""
}

variable "api_cpu" {
  description = "CPU units for API Fargate task"
  type        = number
  default     = 256
}

variable "api_memory" {
  description = "Memory (MB) for API Fargate task"
  type        = number
  default     = 512
}

variable "worker_cpu" {
  description = "CPU units for Worker Fargate task"
  type        = number
  default     = 256
}

variable "worker_memory" {
  description = "Memory (MB) for Worker Fargate task"
  type        = number
  default     = 512
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}
