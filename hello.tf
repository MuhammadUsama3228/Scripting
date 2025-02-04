module "lambda_communications_widget-new" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.7.1"
  function_name = "${local.base_name}-communications-widget"
  role_name     = "rol-${local.base_name}-communications-widget"
  handler       = "my_lambda_handler"
  runtime       = "java17"
  memory_size   = local.lambda_default_memory
  ignore_source_code_hash = true
  create_package          = false
  local_existing_package  = "./dummy_java_lambda.zip"
  package_type            = "Zip"
  vpc_security_group_ids        = [aws_security_group.db_access.id, aws_security_group.egress_allowed.id]
  vpc_subnet_ids                = var.app_subnet_ids
  attach_network_policy         = true
  attach_cloudwatch_logs_policy = true
  cloudwatch_logs_retention_in_days = var.retention_in_days
  
  timeout                       = 30
  attach_policy_statements = true
  policy_statements = merge({
    allowDB        = local.policy_allow_db
    allowJWTPublic = local.policy_allow_jwt_public
  }, local.lambda_default_policies)
  environment_variables = merge({
    AUD      = "c82055b4-6ac2-4d61-a5fe-62dd2c7fc737"
    ISS      = "https://login.microsoftonline.com/b22cedd0-184b-4b56-ac34-991ce150377d/v2.0"
    SIGN_KEY = "SIGN_KEY-TEST"
    JWT_PUBLIC_ARN = var.jwt_public_arn
    DB_USERNAME  = "${local.base_name}-communications-widget"
  }, local.lambda_default_envs, local.lambda_db_envs)
  tags = merge(local.standard_tags, local.lambda_tags)
}
