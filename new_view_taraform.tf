module "lambda_new_view" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.7.1"
  function_name = "${local.base_name}-new_view"
  role_name     = "rol-${local.base_name}-new_view"
  handler       = "testHandler"
  runtime       = "java17"
  memory_size   = local.lambda_default_memory
  // Terraform shouldn't manage code deploys
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
  },local.lambda_default_policies)
  environment_variables = merge({
    AUD      = "c82055b4-6ac2-4d61-a5fe-62dd2c7fc737"
    ISS      = "https://login.microsoftonline.com/b22cedd0-184b-4b56-ac34-991ce150377d/v2.0"
    SIGN_KEY = "SIGN_KEY-TEST"
    JWT_PUBLIC_ARN = var.jwt_public_arn
    DB_USERNAME  = "${local.base_name}-new_view"
  }, local.lambda_default_envs, local.lambda_db_envs)
  tags = merge(local.standard_tags, local.lambda_tags)
}
resource "postgresql_role" "lambda_new_view_db_new_view" {
  name  = module.lambda_new_view.lambda_function_name
  login = true
  // RDS iam takes precedence over password auth, so this is disabled immediatly
  password  = "tmp-lambda-new_view-secure-password"
  superuser = false
  roles     = ["rds_iam", "pg_read_all_data", "pg_write_all_data"]
}
module "lambda_new_view_paths" {
  source          = "../modules/lambda_lb_route"
  maintenance_mode_bypass_code_arn           = var.maintenance_mode_bypass_code_arn
  vpc_id          = var.vpc_id
  lb_listener_arn = module.backend_lb.listeners["https"].arn
  function_name = module.lambda_new_view.lambda_function_name
  function_arn  = module.lambda_new_view.lambda_function_arn
  priority      = 42
  path_patterns = ["/<lambda_path>/*", "/<lambda_path>"]
  standard_tags = merge(local.standard_tags, local.lambda_tags)
}
module "lambda_new_view_paths2" {
  count           = var.create_public_endpoints ? 1 : 0
  source          = "../modules/lambda_lb_route"
  maintenance_mode_bypass_code_arn           = var.maintenance_mode_bypass_code_arn
  vpc_id          = var.vpc_id
  lb_listener_arn = aws_alb_listener.api_http.0.arn
  target_name   = "new_view-2"
  function_name = module.lambda_new_view.lambda_function_name
  function_arn  = module.lambda_new_view.lambda_function_arn
  priority      = 42
  path_patterns = ["/new_path/*", "/new_path"]
  standard_tags = merge(local.standard_tags, local.lambda_tags)
}






