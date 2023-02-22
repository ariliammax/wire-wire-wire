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

## Running

To run the client / server using the wire protocol / gRPC, run

```bash
python -m chat.[wire|grpc].[client|server].main \
    [--host=HOST] \
    [--port=PORT]
```

If one port doesn't work, try another!

## Linting

To lint the source code, run

```bash
source lint.sh
```

## Testing

To run the tests, run

```bash
source test.sh
```

## Documentation

To view the documentation (in `man`), run

```bash
source docs.sh
```

To view it on [`localhost:1234/chat`](localhost:1234/chat), run

```bash
souce docshtml.sh
```
