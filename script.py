import base64
import json
import requests
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

class GitHubFileUploader:
    def __init__(self, repo_owner, repo_name, file_path, file_content, commit_message, token, branch='main'):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.file_path = file_path
        self.file_content = file_content
        self.commit_message = commit_message
        self.token = token
        self.branch = branch
        self.api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}'

    def upload_file(self):
        """Upload the file to the specified GitHub repository."""
        encoded_content = base64.b64encode(self.file_content.encode()).decode()

        data = {
            'message': self.commit_message,
            'content': encoded_content,
            'branch': self.branch
        }

        headers = {
            'Authorization': f'token {self.token}',
        }

        # Check if the file already exists on GitHub
        response = requests.get(self.api_url, headers=headers)

        if response.status_code == 200:
            # The file exists, retrieve its sha for updating
            file_sha = response.json()['sha']
            data['sha'] = file_sha  # Add the sha to update the file

        # Make the request to either create or update the file
        response = requests.put(self.api_url, headers=headers, data=json.dumps(data))

        # Check the response
        if response.status_code == 201 or response.status_code == 200:
            print(f"File uploaded successfully to {self.branch} branch!")
        else:
            print(f"Error uploading file: {response.status_code} - {response.text}")
            print(f"Response body: {response.text}")


class TerraformManager:
    def __init__(
            self, file_content, lambda_handler, lambda_path, lambda_name, lambda_name2, password,
            priority, branch_name, repo_owner, repo_name, file_path, commit_message, token, logging_log_format=None
    ):
        self.file_content = file_content
        self.lambda_handler = lambda_handler
        self.lambda_path = lambda_path
        self.lambda_name = lambda_name
        self.lambda_name2 = lambda_name2
        self.priority = priority
        self.logging_log_format = logging_log_format
        self.password = password
        self.branch_name = branch_name
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.file_path = file_path
        self.commit_message = commit_message
        self.token = token
        self.return_file_name = None
        self.new_file_path = None

    def typewriter(self, text, delay=0.004):
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)

    def make_file(self, out_filename):
        """Modify the file content and save it with the given output filename."""
        print('Original file content will be modified and saved as:', out_filename)

        try:
            new_content = self.file_content.replace('<lambda_name>', self.lambda_name)
            new_content = new_content.replace('<lambda_handler>', self.lambda_handler)
            new_content = new_content.replace('<lambda_name2>', self.lambda_name2)
            new_content = new_content.replace('<path>', self.lambda_path)
            new_content = new_content.replace('<priority>', str(self.priority))
            new_content = new_content.replace('<password>', self.password)

            if self.logging_log_format is None:
                new_content = new_content.replace('<logging_log_format>', "")
            else:
                string = f'logging_log_format = "{self.logging_log_format}"'
                new_content = new_content.replace('<logging_log_format>', string)

            print(f'<----------------- {out_filename} ----------------->\n\n')
            self.typewriter(new_content)

            with open(out_filename, 'w') as file:
                file.write(new_content)

            uploader = GitHubFileUploader(
                repo_owner=self.repo_owner,
                repo_name=self.repo_name,
                file_path=self.file_path,
                file_content=new_content,
                commit_message=self.commit_message,
                token=self.token,
            )
            uploader.upload_file()

        except Exception as e:
            print(f"An error occurred while processing the file: {e}")


def main():
    print("Welcome to the Terraform Lambda Manager!")

    while True:
        out_filename = input("Enter the desired output file name (e.g., output_lambda.tf) or press 'q' to quit: ")

        if out_filename.lower() == 'q':
            print("Exiting the program.")
            break

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

        branch_name = input("Enter the Branch name: ")
        while not branch_name.strip():
            print("The Branch name cannot be empty.")
            branch_name = input(
                "Enter the Branch name: ")

        repo_owner = input("Enter the repo owner (Username): ")
        while not repo_owner.strip():
            print("The repo owner cannot be empty.")
            repo_owner = input(
                "Enter the repo owner: ")

        repo_name = input(
            "Enter the Git repository name: ")
        while not repo_name.strip():
            print("The Git repository name cannot be empty.")
            repo_name = input(
                "Enter the Git repository name: ")

        commit_message = input(f"Enter commit message 'Adding Terraform configuration {out_filename}': ")
        if not commit_message.strip():
            commit_message = f"Adding Terraform configuration {out_filename}"

        token = input(f"Enter repo token '{repo_owner}/{repo_name}': ")
        while not token.strip():
            print("Repo token cannot be empty.")
            token = input(
                f"Enter repo token '{repo_owner}/{repo_name}': ")

        logging_log_format = input("Enter the logging log format (e.g., JSON) or press enter to skip: ")
        if logging_log_format.strip() == "":
            logging_log_format = None

        manager = TerraformManager(
            file_content=file_content,
            lambda_handler=lambda_handler,
            lambda_path=lambda_path,
            lambda_name=lambda_name,
            lambda_name2=lambda_name2,
            password=password,
            priority=priority,
            branch_name=branch_name,
            repo_owner=repo_owner,
            repo_name=repo_name,
            file_path=out_filename,
            commit_message=commit_message,
            token=token,
            logging_log_format=logging_log_format
        )

        manager.make_file(out_filename)


if __name__ == "__main__":
    main()
