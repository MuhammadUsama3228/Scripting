import subprocess
import os
import time
import sys

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
            priority, git_name, git_email, remote_url, branch_name, logging_log_format=None
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
        self.git_email = git_email
        self.git_name = git_name
        self.return_file_name = None
        self.new_file_path = None

    def typewriter(self, text, delay=0.004):
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)


    def configure_github(self):
        subprocess.run(["git", "config", "user.name", self.git_name])

        subprocess.run(
            ["git", "config", "user.email", self.git_email],)

        print("Git user configuration updated successfully!")

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

                self.configure_github()

                modified_files = subprocess.check_output(['git', 'status', '--porcelain'], universal_newlines=True)

                if f"?? {out_filename}" in modified_files:
                    subprocess.run(['git', 'add', out_filename], check=True, shell=True)

                # if "?? script.py" in modified_files or "M script.py" in modified_files:
                #     print("Skipping update of private file script.py")

                print(f'<----------------- Updating GitHub ----------------->\n\n')
                self.push_repository(
                    remote_url=self.remote_url,
                    message=f'Adding new lambda {self.lambda_name}',
                    branch_name=self.branch_name,
                )

        except Exception as e:
            print(f"An error occurred while processing the file: {e}")

    def push_repository(self, message, remote_url, branch_name):
        try:
            if not os.path.exists('.git'):
                subprocess.run(['git', 'init'], check=True, shell=True)

            remote_check = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            if remote_check.returncode != 0:
                subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True, shell=True)
            subprocess.run(['git', 'commit', '-m', message], check=True, shell=True)
            subprocess.run(['git', 'push', '-u', 'origin', branch_name], check=True, shell=True)

        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
        except Exception as e:
            print(f"An error occurred during the Git process: {e}")


def main():
    print("Welcome to the Terraform Lambda Manager!")

    while True:  # Keep the program running until 'q' is pressed
        out_filename = input("Enter the desired output file name (e.g., output_lambda.tf) or press 'q' to quit: ")

        if out_filename.lower() == 'q':
            print("Exiting the program.")
            break  # Exit the loop and the program

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

        lambda_path = input(
            "Enter the Lambda path (e.g., [\"/communications-widget\", \"/communications-widget/*\"]): ")
        while not lambda_path.strip():
            print("The Lambda path cannot be empty.")
            lambda_path = input(
                "Enter the Lambda path (e.g., [\"/communications-widget\", \"/communications-widget/*\"]): ")

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

        git_name = input("Enter the Git name: ")
        while not git_name.strip():
            print("The Git name cannot be empty.")
            git_name = input(
                "Enter the Git name: ")

        git_email = input("Enter the Git email: ")
        while not git_email.strip():
            print("The Git email cannot be empty.")
            git_email = input(
                "Enter the Git email: ")

        remote_url = input(
            "Enter the Git repository URL (e.g., https://github.com/your-username/your-repository.git): ")
        while not remote_url.strip():
            print("The Git repository URL cannot be empty.")
            remote_url = input(
                "Enter the Git repository URL (e.g., https://github.com/your-username/your-repository.git): ")

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
            git_name=git_name,
            git_email=git_email,
            remote_url=remote_url,
            branch_name=branch_name,
            logging_log_format=logging_log_format
        )

        obj.make_file(out_filename, git=True)


if __name__ == "__main__":
    main()
