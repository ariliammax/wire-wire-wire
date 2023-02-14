# Design exercises: wire protocol
## Ari Troper, Liam McInroy, Max Snyder

### 2023.02.13

#### First notes

Initial setup of project. We will be using `python`, since it will be readable
to reviewers et al, makes setup easy on different environments thanks to
`setuptools` and `pip` package management tools, and has `socket` a nice
library for the wire protocol and `grpcio`

There's some organizational notes that we think will make the development
process scale easier. Some of these (relating to the organization of the
`git` branches) can be found in [`doc.md`](doc.md). The other follow from
using `setuptools` to have different packages:

- All of the source is under the [`chat/`](chat/) folder.

- Common code (not wire protocol or gRPC dependent, e.g. UI) may be found
under the [`chat/common`](chat/common/) folder or the `chat.common` module.

- The wire protocol specific code is under the [`chat/wire`](chat/wire/)
folder or the `chat.wire` module. This also has the subfolders and submodules
of [`chat/wire/server`](chat/wire/server/) (`chat.wire.server` module?) and
[`chat/wire/client`](chat/wire/client/) (`chat.wire.client` module?).

- The gRPC specific code is under the [`chat/grpc`](chat/grpc/)
folder or the `chat.grpc` module. This also has the subfolders and submodules
of [`chat/grpc/server`](chat/grpc/server/) (`chat.grpc.server` module?) and
[`chat/grpc/client`](chat/grpc/client/) (`chat.grpc.client` module?).

- Eventually, tests will span both server and client within the `chat.wire`
or `chat.grpc` modules (the tests will be on a single machine, _good enough_).

#### Implementation / debugging notes

##### First socket (one-to-one)

Now for notes during implementation (we are focusing on the `chat.wire`
module). We are making the design choice to use the `socket` package.

On the server:

- `socket.socket.bind` creates the host (given a host IP and port)

- `.listen()` starts listening for a client, `.accept` accepts it.

On the client:

- `socket.socket.connect` connects to the host (given IP, port)

On both:

- `socket.connection.sendall` sends along the socket.
It also requires a `bytes-like object`.
So in the case of `str` the `b'...'` syntax will be helpful.

- `socket.connection.recv` receives (given size of packet it is receiving).

##### Some networking troubles

All of this so far works nicely on `localhost`, but when trying our public
IP address then the server gets an `OSError: Can't assign requested address`
during a `.bind`.

This seems to be a firewall issue on first guess, but supposedly the test
machine's firewall is already off. But then it seemed like the public IP
address had changed since we last checked it (head scratch moment).
Things got more confusing when we got another IP that worked on a different
project, and then we noticed the public IP changed again. Thanks, Harvard.

After resetting the WiFi connection, the public IP stabilized, but same issue
(the `OSError`), so that was all a big red herring. We also fiddled with
other random ports (we'd been using 8080, 65432, maybe others?).

So back to IPs, after searching for the error online more. Now, rather than
using some other website, we run

```bash
ipconfig getifaddr en0
```

then it worked on the test machine (with port 8080).

So onto testing across machines, and it works nicely too.

###### Multiple connections

We need to accept multiple clients on the server. So the socket either
can't block on accepting a connection until ending it, or we need some
asynchronous code, or we need to poll, or...

We'll try not blocking first:

- We found a `.setblocking(False)` flag we can set (after the `.listen`, since
`.accept` blocks) so that the server can continue to listen for new
connections -- at least supposedly. This wasn't working (with the error
`Resource temporarily unavailable`), so we will try polling.

Onto polling:

- We get a `.connection` and `.address` from `.socket.accept`, so we'll
keep polling for connections (with a timeout using `.socket.settimeout`).

- On accepting a connection, we'll start a new thread to handle that
connection (`.recv`, `.send`/`.sendall`, etc.). When the connection ends,
we'll terminate the thread. (Since sockets keep order, we won't have to worry
about interweaving too, too much).

- We were prototyping without threading, but that got annoying on telling
when/if clients disconnected. So we'll just do threading now.

Now, it's Ari's turn to start scribing. ~ _Liam_
