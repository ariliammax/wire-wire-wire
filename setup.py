from setuptools import setup

setup(name='chat',
      version='0.1',
      packages=['common',
                'wire',
                'wire.client',
                'wire.server'],  # eventually also 
      package_dir={'common': 'chat/common/',
                   'wire': 'chat/wire/'},
      install_requires=[])
