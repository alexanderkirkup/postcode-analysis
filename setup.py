from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='postcode_analysis',
    version='0.1',
    description='UK property analysis by postcode.',
    long_description=readme,
    author='Alexander Kirkup',
    url='https://github.com/alexanderkirkup/postcode-analysis',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)