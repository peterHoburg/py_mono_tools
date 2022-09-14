resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "main"
    env  = "test"
  }
}

resource "aws_default_security_group" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_flow_log" "main" {
  iam_role_arn    = ""
  log_destination = aws_cloudwatch_log_group.vpc_main.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id
}

resource "aws_cloudwatch_log_group" "vpc_main" {
  name              = "vpc_main"
  retention_in_days = 180
  kms_key_id        = aws_kms_key.cloudwatch.arn
}

resource "aws_kms_key" "cloudwatch" {
  description             = "KMS key for CloudWatch Logs"
  deletion_window_in_days = 10
  is_enabled              = true
  # This will fail checkov, tfsec, and terrascan
#  enable_key_rotation     = true
}

# This will fail terraform fmt -check
resource "aws_iam_role" "vpc_logging" {
  name               = "vpc_logging"
    assume_role_policy = data.aws_iam_policy_document.vpc_logging.json
}

resource "aws_iam_role_policy" "vpc_logging" {
  name   = "vpc_logging"
  role   = aws_iam_role.vpc_logging.id
  policy = data.aws_iam_policy_document.vpc_logging.json
}

data "aws_iam_policy_document" "vpc_flow_logs_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }
  }
}

# This is missing a permission for the KMS key
data "aws_iam_policy_document" "vpc_logging" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams"
    ]
    resources = [
      aws_cloudwatch_log_group.vpc_main.arn
    ]
  }
}
