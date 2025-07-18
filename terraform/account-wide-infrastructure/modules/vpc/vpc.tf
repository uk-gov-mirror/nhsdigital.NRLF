resource "aws_vpc" "app_vpc" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_hostnames = var.enable_dns_hostnames

  tags = {
    Name = "${var.name_prefix}-vpc"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.app_vpc.id

  tags = {
    Name = "${var.name_prefix}-igw"
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.app_vpc.id
  cidr_block              = var.vpc_public_subnets_cidr_block
  map_public_ip_on_launch = true
  availability_zone       = var.aws_azs

  tags = {
    Name = "${var.name_prefix}-pubsubnet"
  }
}

resource "aws_subnet" "private_subnet" {
  vpc_id            = aws_vpc.app_vpc.id
  cidr_block        = var.vpc_private_subnets_cidr_block
  availability_zone = var.aws_azs

  tags = {
    Name = "${var.name_prefix}-privsubnet"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.app_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table" "private_rt" {
  vpc_id = aws_vpc.app_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }
}

resource "aws_eip" "natgw-ip" {
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.natgw-ip.id
  subnet_id     = aws_subnet.public_subnet.id

  tags = {
    Name = "${var.name_prefix}-nat"
  }
}

resource "aws_route_table_association" "public_rt_asso" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "private_rt_asso" {
  subnet_id      = aws_subnet.private_subnet.id
  route_table_id = aws_route_table.private_rt.id
}

resource "aws_security_group" "powerbi_gw_sg" {
  name        = "powerbi-gw-sg"
  description = "Only allow egress traffic"
  vpc_id      = aws_vpc.app_vpc.id

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}
