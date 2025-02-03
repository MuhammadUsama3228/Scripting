import subprocess


class TerraformManager:
    def __init__(self, file, lambda_handler, lambda_path, lambda_name):
        self.file = file
        self.lambda_handler = lambda_handler
        self.lambda_path = lambda_path
        self.lambda_name = lambda_name

        self.return_file_name = None
        self.convert_func()

    def new_file_name(self):
        s = self.file.split('/')
        f = s[-1]
        self.return_file_name = f.replace('user', f'{self.lambda_name}')

    def convert_func(self):
        self.new_file_name()
        print('file name ', self.file)
        print('file name ', self.return_file_name)
        try:
            with open(self.file, 'r') as file:
                content = file.read()

            new_content = content.replace('<lambda_name>', self.lambda_name)
            new_content = new_content.replace('<lambda_handler>', self.lambda_handler)
            new_content = new_content.replace('<path>', self.lambda_path)

            # print(new_content)

            with open(f'{self.return_file_name}', 'w') as file:
                file.write(new_content)

            self.push_repository(
                remote_url='https://github.com/MuhammadUsama3228/Scripting.git',
                message=f'Adding new lambda {self.lambda_name}',
                branch_name='main'
            )

        except FileNotFoundError:
            print("File not found.")

    def push_repository(self, message, remote_url, branch_name):

        try:

            subprocess.run(['git', 'add', self.file])
            subprocess.run(['git', 'commit', '-m', f'{message}'])
            subprocess.run(['git', 'add', 'origin', remote_url])
            subprocess.run(['git', 'push', 'origin', f'{branch_name}'])

        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")


obj = TerraformManager(
    file=r"C:\Users\Usama-Java\PycharmProjects\PythonProject\user_taraform.tf",
    lambda_handler='testHandler',
    lambda_name='test_user',
    lambda_path='new_path'
)
