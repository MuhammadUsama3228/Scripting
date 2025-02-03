# Terraform Lambda Manager

This Python script helps automate the process of creating a Terraform configuration file for managing AWS Lambda functions and their associated resources. The script allows you to customize key attributes such as Lambda handler, function name, VPC settings, logging format, and more. It can also commit and push changes to a GitHub repository after generating the necessary configuration file.

## Features

- Generate a Terraform configuration file (`.tf`) for managing AWS Lambda functions.
- Dynamically replace placeholders with user inputs (e.g., Lambda function names, handler, paths, etc.).
- Optionally configure Git user credentials and push changes to a remote repository.
- Handle Lambda configuration for IAM roles, security groups, and VPC settings.
- Generate and manage paths for routing Lambda traffic using AWS ALB.
- Supports logging configuration for Lambda functions.

## Prerequisites

- Python 3.x
- Git
- Terraform
- An AWS account and permissions to manage Lambda, IAM, and related resources.
- A GitHub repository to commit and push changes (optional but recommended).

## Setup

1. **Clone or download the repository containing the script.**
   
   ```bash
   git clone https://github.com/your-username/terraform-lambda-manager.git
   cd terraform-lambda-manager