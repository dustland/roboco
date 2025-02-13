from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess

class CustomInstall(install):
    def run(self):
        # Build studio frontend before installation
        subprocess.run(['pnpm', 'install'], cwd='studio', check=True)
        subprocess.run(['pnpm', 'build'], cwd='studio', check=True)
        super().run()

setup(
    name='roboco',
    cmdclass={'install': CustomInstall},
    package_data={'roboco': ['studio/.next/**/*']},
    include_package_data=True,
)
