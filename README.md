# Setup and scripts

All scripts mentioned in this document should be ran in the main directory
(i.e. where you currently are, i.e. [wire/](./)).

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
    [--port=PORT] \
    [--verbose]   \
    [--shiny]
```

- `verbose` on a `server` will add logging output of packet sizes.

- `shiny` is an experimental client UI.

If one port doesn't work, try another!

### With packet sizes

For wire, start the server with

```bash
python -m chat.wire.server.main \
    [--host=HOST] \
    [--port=PORT] \
    --verbose
```


For gRPC, start the server with

```bash
GRPC_VERBOSITY=DEBUG \
    GRPC_TRACE=http \
    python -m chat.grpc.server.main \
    [--host=HOST] \
    [--port=PORT]
```

As a note on some packet sizes between the two

| operation | wire | grpc |
| --------- | ---- | ---- |
| log in request | 4B | 4B |
| log in response | 2B | 0B |
| create request | 4B | 4B |
| create response | 2B | 0B |
| list request | 2B | 0B |
| list response | 7B | 8B |
| send request | 10B | 12B |
| send response | 2B | 0B |
| deliver request | 5B | 4B |
| deliver response | 20B | 22B |
| ack request | 19B | 22B |
| ack response | 2B | 0B |
| log out request | 4B | 4B |
| log out response | 2B | 0B |
| delete request | 4B | 4B |
| delete response | 2B | 0B |

Some of the differences are because our wire protocol doesn't use `set` bits,
for some decreases, but we also have to include `opcode`s which increase
some request sizes, and we give an empty error on response rather than no
response, which we have to encode the length of the empty string using some
bytes.

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

To view it on [`localhost:1234/chat`](http://localhost:1234/chat), run

```bash
souce docshtml.sh
```
