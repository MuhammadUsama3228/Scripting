import subprocess
import os


class GitManager:
    def __init__(self, remote_url, branch_name, file_name, file_content, commit_message):
        self.remote_url = remote_url
        self.branch_name = branch_name
        self.file_name = file_name
        self.file_content = file_content
        self.commit_message = commit_message

    def run_command(self, command):

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if result.returncode != 0:
            print(f"Error running command: {command}")
            print(result.stderr.decode())
            return False
        return True

    def initialize_git_repo(self):
        """Initialize the git repository and add remote if necessary."""
        if not os.path.exists('.git'):
            print("Initializing a new Git repository...")
            if not self.run_command('git init'):
                return False

        # Check if remote exists, and if not, add the remote
        remote_check = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        if remote_check.returncode != 0:
            print("No remote found. Adding the remote repository URL...")
            if not self.run_command(f'git remote add origin {self.remote_url}'):
                return False

        return True

    def pull_latest_changes(self):
        """Pull the latest changes from the remote repository."""
        print(f"Pulling the latest changes from the remote branch {self.branch_name}...")
        # Allow merging unrelated histories
        return self.run_command(f'git pull origin {self.branch_name} --allow-unrelated-histories')

    def create_or_switch_branch(self):
        """Create the branch if it doesn't exist, or switch to it."""
        print(f"Checking if branch {self.branch_name} exists...")
        branch_check = subprocess.run(
            ['git', 'rev-parse', '--verify', self.branch_name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )

        if branch_check.returncode != 0:
            print(f"Branch {self.branch_name} does not exist. Creating and switching to the new branch...")
            if not self.run_command(f'git checkout -b {self.branch_name}'):
                return False
        else:
            print(f"Branch {self.branch_name} exists. Switching to the branch...")
            if not self.run_command(f'git checkout {self.branch_name}'):
                return False

        return True

    def commit_and_push(self):
        """Add the file, commit the changes, and push to the remote branch."""
        print(f"Adding {self.file_name} to Git...")
        with open(self.file_name, 'w') as f:
            f.write(self.file_content)

        if not self.run_command(f'git add {self.file_name}'):
            return False

        print(f"Committing changes with message: '{self.commit_message}'...")
        if not self.run_command(f'git commit -m "{self.commit_message}"'):
            return False

        print(f"Pushing changes to branch {self.branch_name}...")
        if not self.run_command(f'git push -u origin {self.branch_name}'):
            return False

        print(f"Changes pushed to {self.branch_name} successfully.")
        return True


def main():
    remote_url = 'https://github.com/MuhammadUsama3228/Scripting.git'  # Replace with your actual GitHub URL
    branch_name = 'main'  # Specify your branch name
    file_name = 'output_lambda.tf'  # Specify your output file
    file_content = '''# Terraform configuration content here...'''  # Replace with the actual content of your file
    commit_message = 'Adding/Updating output_lambda.tf file'

    git_manager = GitManager(remote_url, branch_name, file_name, file_content, commit_message)

    # Step 1: Initialize the Git repository (if not already initialized)
    if not git_manager.initialize_git_repo():
        print("Failed to initialize the Git repository.")
        return

    # Step 2: Pull the latest changes from the specified branch
    if not git_manager.pull_latest_changes():
        print(f"Failed to pull the latest changes from branch {branch_name}.")
        return

    # Step 3: Create or switch to the specified branch
    if not git_manager.create_or_switch_branch():
        print(f"Failed to switch or create the branch {branch_name}.")
        return

    # Step 4: Commit and push the changes
    if not git_manager.commit_and_push():
        print("Failed to commit or push the changes.")
        return

    print("Code updated successfully on GitHub.")


if __name__ == "__main__":
    main()
