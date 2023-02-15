from setuptools import setup

setup(name='chat',
      version='0.1',
      packages=['common',
                'wire',
                'wire.client',
                'wire.server',
                'grpc'],
      package_dir={'common': 'chat/common/',
                   'wire': 'chat/wire/',
                   'grpc': 'chat/grpc'},
      install_requires=['grpcio',
                        'grpcio-tools'])
