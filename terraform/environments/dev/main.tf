terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "voice-orchestrator-tfstate"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "voice-orchestrator-tflock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = var.app_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  app_name    = "voice-orchestrator"
  environment = "dev"
}

module "vpc" {
  source = "../../modules/vpc"

  app_name    = local.app_name
  environment = local.environment
  vpc_cidr    = var.vpc_cidr
}

module "rds" {
  source = "../../modules/rds"

  app_name              = local.app_name
  environment           = local.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  ecs_security_group_id = module.ecs.ecs_security_group_id
  instance_class        = var.db_instance_class
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
}

module "redis" {
  source = "../../modules/redis"

  app_name              = local.app_name
  environment           = local.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  ecs_security_group_id = module.ecs.ecs_security_group_id
  node_type             = var.redis_node_type
}

module "s3" {
  source = "../../modules/s3"

  app_name       = local.app_name
  environment    = local.environment
  aws_account_id = data.aws_caller_identity.current.account_id
}

module "ecs" {
  source = "../../modules/ecs"

  app_name           = local.app_name
  environment        = local.environment
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  image_uri          = var.api_image_uri
  api_cpu            = 256
  api_memory         = 512
  worker_cpu         = 256
  worker_memory      = 512
  api_desired_count  = 1
  worker_desired_count = 1
  database_url       = module.rds.database_url
  redis_url          = module.redis.redis_url
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.ecs.alb_dns_name
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.endpoint
}

output "s3_bucket" {
  description = "Audio S3 bucket"
  value       = module.s3.bucket_name
}
