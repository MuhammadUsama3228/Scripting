import subprocess
import os
import sys
import time

file_content = """module "lambda_<lambda_name>" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.7.1"
  function_name = "${local.base_name}-<lambda_name2>"
  role_name     = "rol-${local.base_name}-<lambda_name2>"
  handler       = "<lambda_handler>"
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
  <logging_log_format>
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
    DB_USERNAME  = "${local.base_name}-<lambda_name2>"
  }, local.lambda_default_envs, local.lambda_db_envs)
  tags = merge(local.standard_tags, local.lambda_tags)
}
module "lambda_<lambda_name>_paths" {
  source          = "../modules/lambda_lb_route"
  maintenance_mode_bypass_code_arn           = var.maintenance_mode_bypass_code_arn
  vpc_id          = var.vpc_id
  lb_listener_arn = module.backend_lb.listeners["https"].arn
  function_name = module.lambda_<lambda_name>.lambda_function_name
  function_arn  = module.lambda_<lambda_name>.lambda_function_arn
  priority      = <priority>
  path_patterns = <path>
  standard_tags = merge(local.standard_tags, local.lambda_tags)
}
module "lambda_<lambda_name>_paths2" {
  count           = var.create_public_endpoints ? 1 : 0
  source          = "../modules/lambda_lb_route"
  maintenance_mode_bypass_code_arn           = var.maintenance_mode_bypass_code_arn
  vpc_id          = var.vpc_id
  lb_listener_arn = aws_alb_listener.api_http.0.arn
  target_name   = "<lambda_name2>-2"
  function_name = module.lambda_<lambda_name>.lambda_function_name
  function_arn  = module.lambda_<lambda_name>.lambda_function_arn
  priority      = <priority>
  path_patterns = <path>
  standard_tags = merge(local.standard_tags, local.lambda_tags)
}
resource "postgresql_role" "lambda_<lambda_name>_db_user" {
  name  = module.lambda_<lambda_name>.lambda_function_name
  login = true
  // RDS iam takes precedence over password auth, so this is disabled immediatly
  password  = "<password>"
  superuser = false
  roles     = ["rds_iam", "pg_read_all_data", "pg_write_all_data"]
}
"""


class TerraformManager:
    def __init__(
            self, file_content, lambda_handler, lambda_path, lambda_name, lambda_name2, password,
            priority, remote_url, branch_name, logging_log_format=None
    ):
        self.file_content = file_content
        self.lambda_handler = lambda_handler
        self.lambda_path = lambda_path
        self.lambda_name = lambda_name
        self.lambda_name2 = lambda_name2
        self.priority = priority
        self.logging_log_format = logging_log_format
        self.password = password
        self.remote_url = remote_url
        self.branch_name = branch_name
        self.return_file_name = None
        self.new_file_path = None

    def typewriter(self, text, delay=0.004):
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)

    def make_file(self, out_filename, git=False):
        print('Original file content will be modified and saved as:', out_filename)

        try:
            new_content = self.file_content.replace('<lambda_name>', self.lambda_name)
            new_content = new_content.replace('<lambda_handler>', self.lambda_handler)
            new_content = new_content.replace('<lambda_name2>', self.lambda_name2)
            new_content = new_content.replace('<path>', self.lambda_path)
            new_content = new_content.replace('<priority>', str(self.priority))
            new_content = new_content.replace('<password>', self.password)

            print(f'<----------------- {out_filename} ----------------->\n\n')

            self.typewriter(new_content)

            print(f'\n')

            if self.logging_log_format is None:
                new_content = new_content.replace('<logging_log_format>', "")
            else:
                string = f'logging_log_format = "{self.logging_log_format}"'
                new_content = new_content.replace('<logging_log_format>', string)

            with open(out_filename, 'w') as file:
                file.write(new_content)

            if git:
                self.check_and_configure_git()
                self.check_branch_exists_and_push(self.remote_url, out_filename)

        except Exception as e:
            print(f"An error occurred while processing the file: {e}")

    def check_and_configure_git(self):
        """ Check if Git is configured with username and email, and if not, prompt the user to set it. """
        try:
            # Check if Git user.name and user.email are set
            username = subprocess.check_output(['git', 'config', '--get', 'user.name'], universal_newlines=True).strip()
            email = subprocess.check_output(['git', 'config', '--get', 'user.email'], universal_newlines=True).strip()

            if not username or not email:
                print("Git username or email is not set. Please provide them.")
                username = input("Enter Git username: ")
                email = input("Enter Git email: ")
                subprocess.run(['git', 'config', '--global', 'user.name', username], check=True)
                subprocess.run(['git', 'config', '--global', 'user.email', email], check=True)
            else:
                print(f"Git is configured with username: {username} and email: {email}")

        except subprocess.CalledProcessError:
            print("Git is not configured. Prompting for user credentials.")
            username = input("Enter Git username: ")
            email = input("Enter Git email: ")
            subprocess.run(['git', 'config', '--global', 'user.name', username], check=True)
            subprocess.run(['git', 'config', '--global', 'user.email', email], check=True)

    def check_branch_exists_and_push(self, remote_url, out_filename):
        """ Check if the specified branch exists and then push the file to the GitHub repository. """
        try:
            # Check if the branch exists
            result = subprocess.run(['git', 'ls-remote', '--heads', remote_url, self.branch_name], stdout=subprocess.PIPE)
            if result.stdout:
                print(f"Branch '{self.branch_name}' exists.")
            else:
                print(f"Branch '{self.branch_name}' does not exist. Creating it.")
                subprocess.run(['git', 'checkout', '-b', self.branch_name], check=True)

            # Add, commit, and push the new file to the specified branch
            modified_files = subprocess.check_output(['git', 'status', '--porcelain'], universal_newlines=True)

            if f"?? {out_filename}" in modified_files:
                subprocess.run(['git', 'add', out_filename], check=True, shell=True)
                subprocess.run(['git', 'commit', '-m', f'Adding new lambda {self.lambda_name}'], check=True, shell=True)

            # Push to the remote repository
            subprocess.run(['git', 'push', '-u', 'origin', self.branch_name], check=True, shell=True)

        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
        except Exception as e:
            print(f"An error occurred during the Git process: {e}")


def main():
    print("Welcome to the Terraform Lambda Manager!")

    out_filename = input("Enter the desired output file name (e.g., output_lambda.tf): ")
    while not out_filename.strip():
        print("The output file name cannot be empty.")
        out_filename = input("Enter the desired output file name (e.g., output_lambda.tf): ")

    if not out_filename.endswith('.tf'):
        out_filename = out_filename + '.tf'

    lambda_handler = input(
        "Enter the Lambda handler (e.g., com.**********.communicationswidget.CommunicationsWidgetHandler::handleRequest): ")
    while not lambda_handler.strip():
        print("The Lambda handler cannot be empty.")
        lambda_handler = input(
            "Enter the Lambda handler (e.g., com.*********.communicationswidget.CommunicationsWidgetHandler::handleRequest): ")

    lambda_name = input("Enter the Lambda function name: ")
    while not lambda_name.strip():
        print("The Lambda function name cannot be empty.")
        lambda_name = input("Enter the Lambda function name: ")

    lambda_name2 = input("Enter a secondary Lambda function name: ")
    while not lambda_name2.strip():
        print("The secondary Lambda function name cannot be empty.")
        lambda_name2 = input("Enter a secondary Lambda function name: ")

    lambda_path = input("Enter the Lambda path (e.g., [\"/communications-widget\", \"/communications-widget/*\"]): ")
    while not lambda_path.strip():
        print("The Lambda path cannot be empty.")
        lambda_path = input("Enter the Lambda path (e.g., [\"/communications-widget\", \"/communications-widget/*\"]): ")

    while True:
        try:
            priority = int(input("Enter the priority number (e.g., 19): "))
            break
        except ValueError:
            print("Priority should be an integer. Please enter a valid number.")

    password = input("Enter the password for the Lambda function: ")
    while not password.strip():
        print("The password cannot be empty.")
        password = input("Enter the password for the Lambda function: ")

    remote_url = input("Enter the Git repository URL (e.g., https://github.com/your-username/your-repository.git): ")
    while not remote_url.strip():
        print("The Git repository URL cannot be empty.")
        remote_url = input("Enter the Git repository URL (e.g., https://github.com/your-username/your-repository.git): ")

    branch_name = input("Enter the Git branch name (e.g., main): ")
    while not branch_name.strip():
        print("The Git branch name cannot be empty.")
        branch_name = input("Enter the Git branch name (e.g., main): ")

    logging_log_format = input("Enter the logging log format (e.g., JSON) or press enter to skip: ")
    if logging_log_format.strip() == "":
        logging_log_format = None

    obj = TerraformManager(
        file_content=file_content,
        lambda_handler=lambda_handler,
        lambda_path=lambda_path,
        lambda_name=lambda_name,
        lambda_name2=lambda_name2,
        priority=priority,
        password=password,
        remote_url=remote_url,
        branch_name=branch_name,
        logging_log_format=logging_log_format
    )

    obj.make_file(out_filename, git=True)


if __name__ == "__main__":
    main()
