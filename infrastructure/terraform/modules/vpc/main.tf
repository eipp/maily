resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "maily-vpc-${var.environment}"
    Environment = var.environment
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.cidr_block, 8, count.index)
  availability_zone = var.azs[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name        = "maily-public-subnet-${count.index + 1}-${var.environment}"
    Environment = var.environment
    Tier        = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.cidr_block, 8, count.index + length(var.azs))
  availability_zone = var.azs[count.index]

  map_public_ip_on_launch = false

  tags = {
    Name        = "maily-private-subnet-${count.index + 1}-${var.environment}"
    Environment = var.environment
    Tier        = "private"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# Database Subnets
resource "aws_subnet" "database" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.cidr_block, 8, count.index + 2 * length(var.azs))
  availability_zone = var.azs[count.index]

  map_public_ip_on_launch = false

  tags = {
    Name        = "maily-database-subnet-${count.index + 1}-${var.environment}"
    Environment = var.environment
    Tier        = "database"
  }
}

# Elasticache Subnets
resource "aws_subnet" "elasticache" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.cidr_block, 8, count.index + 3 * length(var.azs))
  availability_zone = var.azs[count.index]

  map_public_ip_on_launch = false

  tags = {
    Name        = "maily-elasticache-subnet-${count.index + 1}-${var.environment}"
    Environment = var.environment
    Tier        = "elasticache"
  }
}

# MQ Subnets
resource "aws_subnet" "mq" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.cidr_block, 8, count.index + 4 * length(var.azs))
  availability_zone = var.azs[count.index]

  map_public_ip_on_launch = false

  tags = {
    Name        = "maily-mq-subnet-${count.index + 1}-${var.environment}"
    Environment = var.environment
    Tier        = "mq"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "maily-igw-${var.environment}"
    Environment = var.environment
  }
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  count = length(var.azs)
  vpc   = true

  tags = {
    Name        = "maily-nat-eip-${count.index + 1}-${var.environment}"
    Environment = var.environment
  }
}

# NAT Gateway
resource "aws_nat_gateway" "main" {
  count         = length(var.azs)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name        = "maily-nat-gateway-${count.index + 1}-${var.environment}"
    Environment = var.environment
  }

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "maily-public-route-table-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_route_table" "private" {
  count  = length(var.azs)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name        = "maily-private-route-table-${count.index + 1}-${var.environment}"
    Environment = var.environment
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "database" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "elasticache" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.elasticache[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "mq" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.mq[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# VPC Flow Logs
resource "aws_flow_log" "main" {
  log_destination      = aws_cloudwatch_log_group.flow_log.arn
  log_destination_type = "cloud-watch-logs"
  traffic_type         = "ALL"
  vpc_id               = aws_vpc.main.id

  tags = {
    Name        = "maily-vpc-flow-log-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "flow_log" {
  name              = "/aws/vpc/flowlogs-maily-${var.environment}"
  retention_in_days = 30

  tags = {
    Name        = "maily-vpc-flow-log-group-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_iam_role" "flow_log" {
  name = "maily-vpc-flow-log-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "maily-vpc-flow-log-role-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "flow_log" {
  name = "maily-vpc-flow-log-policy-${var.environment}"
  role = aws_iam_role.flow_log.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}
