# Setup and scripts

All scripts mentioned in this document should be ran in the main directory
(i.e. where you currently are, i.e. [wire/](../wire)).

## Module installation and gRPC build

First, you should (preferably) setup a `virtualenv`. This isn't required,
but best practice.

Anyways, once that is configured, then use

```bash
source install.sh
```

to install a local version of the modules in the project and autogenerate
the gRPC code from `grpcio`.

You could optionally use

```bash
pip install -e ./
```

to just install the modules, and

```bash
source grpcio_install.sh
```

to just autogenerate the gRPC code.

## Configuring IP

To get the IP address of the host, run

```bash
ipconfig getifaddr en0
```

Then put that into `chat/common/config.py` under

```python
class Config:
    HOST = 'xxx.xx.x.x'  # <- put the target IP of the server here.
    MAX_WORKERS = 10
    PORT = 8080
    TIMEOUT = 1
```

Sometimes, the port also gets blocked up. Change the target port of the server
in this file also.

## Linting

To lint the source code, run

```bash
source lint.sh
```
