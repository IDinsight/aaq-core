module "vpc" {
  source                        = "./network"
  vpc_name                      = "${var.environment}-vpc"
  vpc_flow_log_name_prefix      = "${var.project_name}-${var.environment}-vpc"
  public_subnet_name            = "${var.project_name}-${var.environment}-public-subnet"
  private_subnet_name           = "${var.project_name}-${var.environment}-private-subnet"
  db_subnet_group_name          = "${var.project_name}-${var.environment}-db-subnet-group"
  elasticache_subnet_group_name = "${var.project_name}-${var.environment}-elasticache-subnet-group"
  private_route_table_name      = "${var.project_name}-${var.environment}-private-route-table"
  public_route_table_name       = "${var.project_name}-${var.environment}-public-route-table"
  tags                          = local.required_tags
  public_subnet_count           = 2
  private_subnet_count          = 2
  region                        = var.aws_region
  interface_endpoints_sg_name   = "${var.project_name}-${var.environment}-interface-endpoints-sg"
  bastion_sg_id                 = module.bastion_host.bastion_sg_id
  web_ec2_sg_id                 = module.main.web_ec2_sg_id
}
