from setuptools import setup

setup(name='chat',
      version='0.1',
      packages=['common',
                'wire'],  # maybe wire.client, wire.server
      package_dir={'common': 'chat/common/',
                   'wire': 'chat/wire/'},
      install_requires=[])