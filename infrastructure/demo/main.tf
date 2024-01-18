module "main" {
  source                      = "./main"
  rds_db_instance_identifier  = "${var.project_name}-${var.environment}-db"
  rds_db_instance_class       = "db.t4g.small"
  rds_db_name                 = "postgres"
  tags                        = local.required_tags
  db_sg_name                  = "${var.project_name}-${var.environment}-web-db-sg"
  db_subnet_group_name        = module.vpc.db_subnet_group_name
  rds_credentials_secret_name = "${var.project_name}-${var.environment}-web-db-connection-details"
  rds_master_username         = "postgres"
  bastion_sg_id               = module.bastion_host.bastion_sg_id
  ecr_repo_name               = "${var.project_name}-${var.environment}-ecr-repository"
  web_ecs_cluster_name        = "${var.project_name}-${var.environment}-ecs-cluster"
  web_task_role               = "${var.project_name}-${var.environment}-web-task-role"
  web_task_execution_role     = "${var.project_name}-${var.environment}-web-task-execution-role"
  private_subnets             = module.vpc.private_subnets
  public_subnets              = module.vpc.public_subnets
  cidr_block                  = module.vpc.cidr_block
  web_ecs_task_role_name      = "${var.project_name}-${var.environment}-web-task-role"
  web_ec2_instance_role_name  = "${var.project_name}-${var.environment}-web-instance-role"
  web_instance_profile_name   = "${var.project_name}-${var.environment}-web-instance-profile"
  web_ec2_server_name         = "${var.project_name}-${var.environment}-web-server"
  web_asg_name                = "${var.project_name}-${var.environment}-web-asg"
  vpc_id                      = module.vpc.vpc_id
  web_ec2_sg_name             = "${var.project_name}-${var.environment}-web-sg"
  interface_endpoints_sg_id   = module.vpc.interface_endpoints_sg_id
  jwt_secret_secret_name      = "${var.project_name}-${var.environment}-jwt-secret"
  content_access_secret_name  = "${var.project_name}-${var.environment}-content-access"
  whatsapp_token_secret_name  = "${var.project_name}-${var.environment}-whatsapp-token"
  aws_region                  = var.aws_region
  web_ec2_instance_type       = var.demo_ec2_instance_type # t4g.large is the only instance type that supports ARM. If this changes, the AMI should also change


}
