resource "aws_ecs_cluster" "web_cluster" {
  name = var.web_ecs_cluster_name
  tags = merge({ Name = var.web_ecs_cluster_name, Module = "Web" }, var.tags)
}

# service discovery namespace. This is use to create a private DNS namespace.
# The private DNS namespace is used to create a service discovery service.
# The service discovery service is used to route traffic to the application.
# The service discovery service is attached to the ECS service.
# This is how the services communicate with each other.
resource "aws_service_discovery_private_dns_namespace" "web" {
  name = var.private_dns_namespace_name
  vpc  = var.vpc_id
}

# backend service discovery service
# In the application, for the frontend to communicate to the backend, it will use ```backend.aaqdemo.local```
resource "aws_service_discovery_service" "backend" {
  name = "backend"
  dns_config {
    namespace_id   = aws_service_discovery_private_dns_namespace.web.id
    routing_policy = "MULTIVALUE"
    dns_records {
      ttl  = 10
      type = "SRV"
    }
  }
  health_check_custom_config {
    failure_threshold = 1
  }
}

# frontend service discovery service
resource "aws_service_discovery_service" "admin_app" {
  name = "frontend"
  dns_config {
    namespace_id   = aws_service_discovery_private_dns_namespace.web.id
    routing_policy = "MULTIVALUE"
    dns_records {
      ttl  = 10
      type = "SRV"
    }
  }
  health_check_custom_config {
    failure_threshold = 1
  }
}


# Nginx Service with EC2 Launch Type
resource "aws_ecs_service" "nginx_service" {
  # This is a resource, which means it will create a resource in AWS
  # This resource will create an ECS service with EC2 launch type for the Nginx container
  # The ECS service will be used to route traffic to the Nginx container
  # The ECS service will be attached to the ECS cluster
  # This will be the entry point for the application
  # Service will have two tasks running at all times, nginx and certbot
  name                               = "nginx-service"
  cluster                            = aws_ecs_cluster.web_cluster.id
  task_definition                    = aws_ecs_task_definition.nginx_task.arn
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 200
  launch_type                        = "EC2"
  scheduling_strategy                = "REPLICA"
  desired_count                      = 1



  # workaround for https://github.com/hashicorp/terraform/issues/12634

  # we ignore task_definition changes as the revision changes on deploy
  # of a new version of the application
  # desired_count is ignored as it can change due to autoscaling policy
  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }
}

resource "aws_ecs_task_definition" "nginx_task" {
  # The rest of the container definitions will be added when the application is deployed. It will be added to the task definition from docker-compose.yml using the ecs-cli compose create command
  family             = "nginx-task"
  execution_role_arn = aws_iam_role.web_task_role.arn
  container_definitions = jsonencode([{
    name       = "nginx-container",
    image      = "nginx:latest",
    memory     = 512,
    cpu        = 256,
    entryPoint = ["/entrypoint.sh"],

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.nginx.name
        awslogs-stream-prefix = "ecs"
        awslogs-region        = var.aws_region
      }
    }
    },
    {
      name   = "certbot",
      image  = "certbot/certbot:latest",
      memory = 256,
      cpu    = 256,

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.nginx.name
          awslogs-stream-prefix = "ecs"
          awslogs-region        = var.aws_region
        }
      }
  }])

}


# Frontend Service with EC2 Launch Type
resource "aws_ecs_service" "admin_app_service" {
  # This is a resource, which means it will create a resource in AWS
  # This resource will create an ECS service with EC2 launch type for the Frontend container
  # The ECS service will be used to route traffic to the Frontend container
  # The ECS service will be attached to the ECS cluster
  name                               = "admin-app-service"
  cluster                            = aws_ecs_cluster.web_cluster.id
  task_definition                    = aws_ecs_task_definition.admin_app_task.arn
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 200
  launch_type                        = "EC2"
  scheduling_strategy                = "REPLICA"
  desired_count                      = 1

  service_registries {
    registry_arn   = aws_service_discovery_service.admin_app.arn
    container_name = "admin-app-container"
    container_port = 3000
  }


  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

}

resource "aws_ecs_task_definition" "admin_app_task" {
  # The rest of the container definitions will be added when the application is deployed. It will be added to the task definition from docker-compose.yml using the ecs-cli compose create command
  # The CPU and Memory may need to be adjusted based on the application usage
  family             = "admin-app-task"
  execution_role_arn = aws_iam_role.web_task_role.arn
  container_definitions = jsonencode([{
    name   = "admin-app-container",
    image  = "admin-app:latest",
    memory = 512,
    cpu    = 256,



    portMappings = [
      {
        "containerPort" : 3000,
        "hostPort" : 3000,
        "protocol" : "tcp"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.admin_app.name
        awslogs-stream-prefix = "ecs"
        awslogs-region        = var.aws_region
      }
    }
  }])

}

# Backend Service with EC2 Launch Type
resource "aws_ecs_service" "backend_service" {
  # This is a resource, which means it will create a resource in AWS
  # This resource will create an ECS service with EC2 launch type for the Backend container
  # The ECS service will be used to route traffic to the Backend container
  # The ECS service will be attached to the ECS cluster
  name                               = "backend-service"
  cluster                            = aws_ecs_cluster.web_cluster.id
  task_definition                    = aws_ecs_task_definition.backend_task.arn
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 200
  launch_type                        = "EC2"
  scheduling_strategy                = "REPLICA"
  desired_count                      = 1

  service_registries {
    registry_arn   = aws_service_discovery_service.backend.arn
    container_name = "backend-container"
    container_port = 8000
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }
}

resource "aws_ecs_task_definition" "backend_task" {
  # The rest of the container definitions will be added when the application is deployed. It will be added to the task definition from docker-compose.yml using the ecs-cli compose create command
  family             = "backend-task"
  execution_role_arn = aws_iam_role.web_task_role.arn
  container_definitions = jsonencode([{
    name   = "backend-container",
    image  = "backend:latest",
    memory = 512,
    cpu    = 256,

    portMappings = [
      {
        "containerPort" : 8000,
        "hostPort" : 8000,
        "protocol" : "tcp"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.backend.name
        awslogs-stream-prefix = "ecs"
        awslogs-region        = var.aws_region
      }
    }
  }])
}

resource "aws_cloudwatch_log_group" "admin_app" {
  name = "/ecs/admin-app-task-${var.project_name}-${var.environment}"

  tags = merge({ Name = "admin-app-task-${var.environment}", Module = "Web" }, var.tags)
}

resource "aws_cloudwatch_log_group" "backend" {
  name = "/ecs/backend-task-${var.project_name}-${var.environment}"

  tags = merge({ Name = "backend-task-${var.project_name}-${var.environment}", Module = "Web" }, var.tags)
}

resource "aws_cloudwatch_log_group" "nginx" {
  name = "/ecs/nginx-task-${var.project_name}-${var.environment}"

  tags = merge({ Name = "nginx-task-${var.project_name}-${var.environment}", Module = "Web" }, var.tags)
}
