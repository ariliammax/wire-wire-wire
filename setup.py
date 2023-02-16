from setuptools import setup

setup(name='chat',
      version='0.1',
      packages=['common',
                'wire'],  # eventually also 
      package_dir={'common': 'chat/common/',
                   'wire': 'chat/wire/'},
      install_requires=['flake8'])
