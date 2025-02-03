# Terraform Manager Script

This repository contains a Python script designed to automate the management of Terraform files. The `TerraformManager` class can be used to edit and update Terraform configuration files based on dynamic input parameters, such as Lambda function details, priority, logging settings, and more. The script also allows you to push the updated Terraform files to a remote Git repository (like GitHub).

## Features

- Edit Terraform files to customize parameters dynamically.
- Replace placeholders in Terraform configuration files with real values such as Lambda name, handler, password, etc.
- Optional Git integration: Automatically commit and push the changes to a Git repository.
- Allows you to specify logging format and priority for Lambda functions in the Terraform script.

## Prerequisites

Before running the script, ensure you have the following installed on your system:

1. **Python 3.x**: Make sure Python is installed. You can download it from [python.org](https://www.python.org/downloads/).
2. **Git**: The script uses Git for version control. Make sure Git is installed. You can download it from [git-scm.com](https://git-scm.com/).
3. **Terraform**: The script modifies Terraform files, so you must have Terraform installed on your machine. You can download it from [terraform.io](https://www.terraform.io/downloads.html).

## Setup

1. Clone this repository to your local machine.

    ```bash
    git clone https://github.com/your-username/your-repository.git
    ```

2. Install any dependencies (if any). In this case, there are no external dependencies, but make sure Python and Git are available on your system's PATH.

## Script Explanation

The core of the script is the `TerraformManager` class, which is responsible for:

1. **Reading an existing Terraform file** (`sample_tarraform.tf`).
2. **Replacing placeholders** in the Terraform file with the appropriate dynamic values:
    - `<lambda_name>`
    - `<lambda_handler>`
    - `<lambda_name2>`
    - `<password>`
    - `<priority>`
    - `<logging_log_format>`
3. **Saving the modified file** under a new name (based on the Lambda function name).
4. **Optionally pushing the modified file to a Git repository**.

The `TerraformManager` can be used in two ways:
- **Without Git integration**: You can simply create and modify the Terraform file.
- **With Git integration**: The modified file will be automatically committed and pushed to a Git repository.

## How to Run the Script

### 1. Modify the Script

Before running the script, ensure that you have the correct input parameters. Open the script and adjust the following values:

- **file**: Path to your Terraform file (e.g., `sample_tarraform.tf`).
- **lambda_handler**: The Lambda handler name.
- **lambda_name**: The name of the Lambda function.
- **lambda_name2**: A secondary name for the Lambda function.
- **lambda_path**: The paths associated with your Lambda function.
- **priority**: Set the priority value.
- **password**: Specify the password for the Lambda function.
- **remote_url**: URL of your Git repository (if you want to push changes to Git).
- **branch_name**: The branch of the repository where changes will be pushed.

Example of how to initialize the class:

```python
obj = TerraformManager(
    file=r"C:\path\to\your\sample_tarraform.tf",
    lambda_handler='com.example.handler.MyLambdaHandler::handleRequest',
    lambda_name='my_lambda_function',
    lambda_name2='my-lambda-function',
    lambda_path='["/lambda-path", "/lambda-path/*"]',
    priority=10,
    password='my-secret-password',
    remote_url="https://github.com/your-username/your-repository.git",
    branch_name='main',
    logging_log_format="JSON"
)
obj.make_file(git=True)