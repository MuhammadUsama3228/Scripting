# import subprocess
# import os
#
#
# class TerraformManager:
#     def __init__(
#             self, file, lambda_handler, lambda_path, lambda_name, lambda_name2, password,
#             priority, remote_url, branch_name, logging_log_format=None
#     ):
#         self.file = file
#         self.lambda_handler = lambda_handler
#         self.lambda_path = lambda_path
#         self.lambda_name = lambda_name
#         self.lambda_name2 = lambda_name2
#         self.priority = priority
#         self.logging_log_format = logging_log_format
#         self.password = password
#         self.remote_url = remote_url
#         self.branch_name = branch_name
#         self.return_file_name = None
#         self.new_file_path = None
#
#     def new_file_name(self):
#         s = os.path.split(self.file)
#         f = s[-1]
#         self.return_file_name = f.replace('sample', f'{self.lambda_name}')
#         self.new_file_path = os.path.join(s[0], self.return_file_name)
#
#     def make_file(self, git=False):
#         self.new_file_name()
#         print('Original file name:', self.file)
#         print('New file name:', self.return_file_name)
#         try:
#             with open(self.file, 'r') as file:
#                 content = file.read()
#
#             new_content = content.replace('<lambda_name>', self.lambda_name)
#             new_content = new_content.replace('<lambda_handler>', self.lambda_handler)
#             new_content = new_content.replace('<lambda_name2>', self.lambda_name2)
#             new_content = new_content.replace('<path>', self.lambda_path)
#             new_content = new_content.replace('<priority>', str(self.priority))
#             new_content = new_content.replace('<password>', self.password)
#
#             if self.logging_log_format is None:
#                 new_content = new_content.replace('<logging_log_format>', "")
#             else:
#                 string = f'logging_log_format = "{self.logging_log_format}"'
#                 new_content = new_content.replace('<logging_log_format>', string)
#
#             with open(self.new_file_path, 'w') as file:
#                 file.write(new_content)
#
#             subprocess.run(['git', 'add', self.new_file_path], check=True, shell=True)
#
#             if git:
#                 self.push_repository(
#                     remote_url=self.remote_url,
#                     message=f'Adding new lambda {self.lambda_name}',
#                     branch_name=self.branch_name,
#                 )
#
#         except FileNotFoundError:
#             print("File not found.")
#         except Exception as e:
#             print(f"An error occurred while processing the file: {e}")
#
#     def push_repository(self, message, remote_url, branch_name):
#         try:
#             if not os.path.exists('.git'):
#                 subprocess.run(['git', 'init'], check=True, shell=True)
#
#             remote_check = subprocess.run(
#                 ['git', 'remote', 'get-url', 'origin'],
#                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
#             )
#             if remote_check.returncode != 0:
#                 subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True, shell=True)
#             subprocess.run(['git', 'commit', '-m', message], check=True, shell=True)
#             subprocess.run(['git', 'push', '-u', 'origin', branch_name], check=True, shell=True)
#
#         except subprocess.CalledProcessError as e:
#             print(f"Git command failed: {e}")
#         except Exception as e:
#             print(f"An error occurred during the Git process: {e}")
#
#
# obj = TerraformManager(
#     file=r"C:\Users\Usama-Java\PycharmProjects\PythonProject\sample_tarraform.tf",
#     lambda_handler='com.haloconnect.communicationswidget.CommunicationsWidgetHandler::handleRequest',
#     lambda_name='communications_widget-new',
#     lambda_name2='communications-widget',
#     lambda_path='["/communications-widget", "/communications-widget/*"]',
#     priority=19,
#     password='tmp-lambda_communications_widget_db_user-password',
#     remote_url="https://github.com/MuhammadUsama3228/Scripting.git",
#     branch_name='main',
#     logging_log_format="JSON"
# )
# obj.make_file(git=True)

import os

def is_git_repo():
    return os.path.isdir('.git')