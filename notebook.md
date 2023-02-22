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

Now, it's Ari's turn to start scribing. ~ _LM_

...

Hey, Ari here!

We were looking at the benefits/drawbacks of using processes vs. threads
to handle multiple clients, in a non-blocking way. We decided to use
threads, since that is more commonly used for server-client models and will
allow us to easily access the shared server state without the use of a 
socket or pipe, since threads are created in the same address space.

One observation we made is that we don't have to keep track of the threads
since the clients are stateless.

After a little trial and error, we were succesfully able to achieve multiple 
connections without blocking, using threads.

Now we're deciding what to do next:

- We understand there will have to be a shared state in the server that has to
be 'locked'.

- We are thinking of representing our database as global array of structs in
memory.

- We want to decide what our data structures are tonight.

###### Shared resource testing

We quickly want to test how multiple threads interact with a shared resource. 
Liam suggested that in the past he's discovered, depending on the library, 
threads might make copies of shared resources instead of accessing the same
shared  resource... 

Looks like this library does not make a copy, which is what we want!

We're debating the differences between coarse grained and fine grained lock.
We've decied that the granularity of the lock will depend on the action.

_"That's all for now folks!"_ ~ _AT_

#### Towards object, data models and the protocol

We'd like to get an outline of our relevant (data, object) models, the
operations, and the wire protocol. We recall the specification given:

1. Create an account. You must supply a unique user name.

2. List accounts (or a subset of the accounts, by text wildcard)

3. Send a message to a recipient. If the recipient is logged in, deliver
immediately; otherwise queue the message and deliver on demand.
If the message is sent to someone who isn't a user, return an error message

4. Deliver undelivered messages to a particular user.

5. Delete an account. You will need to specify the semantics of what happens
if you attempt to delete an account that contains undelivered message.

##### Data models

This is pretty simple, there's just two primitives, and these are their
fields:

1. `Account`: `username : str` (self explanatory), `logged_in : bool`,
dictates whether sent messages are to be delivered immediately or not.

After some debate, we don't include a `connection`, since the gRPC will not
use exactly that (it's wire specific). We will eventually have an extension
`WireAccount` that includes one (and similarly, perhaps a `gRPCAccount`.

2. `Message`: `sender_username : str`, `recipient_username : str`,
`message : str`, `time : int`, and `delivered : bool`.

Not much to be said about that, except that `time` is a nice UI perk.
Saying something would be a waste (this is a quine).

Now, we will need object models. There was some debate whether we use the
data models (and make attributes optional or not depending on whether the
operation/object uses the field), or create different object models for each
operation's request and response to clearly illustrate the specific wire
protocol.

For the sake of clarity, at the cost of verbosity, we opt to create separate
models for each operation's request and response. So it will be useful to
review the operations.

###### Operations

We replace the `Response` vs `Request` tedium with "gets" and "gives".

1a. `CreateAccount`: gives `Account.username`, gets maybe error `str`.

1b. `LogInAccount`: gives `Account.username`, gets maybe error `str`.

Max has the point these are the same, but we decided it was most readable to
disentangle them.

2. `ListAccounts`: gives `str`, gets `[Account]`.

3. `SendMessage`: gives `Message.` everything except `.time` and `.delivered`,
gets maybe error `str`.

4. `DeliverUndeliveredMessages`: gives `Account.username`, gets `[Message.`
everything except `.delivered` `]`.

5. `DeleteAccount`: gives `Account.username`, gets maybe error `str`.

Liam will make nice auto-generating code for this and the data models, so
it will be explicit but not verbose (and will make the overall wire protocol
self contained hopefully).

Our next steps will be actually building these object models,
their (de)serialization, object to data transformations,
a 'database' of the data models, and then the logic on both ends.

The last one depends on the preceeding two, the penultimate doesn't depend
on the object models. So Liam will do the autogenerating object models,
Max and Ari will do the database, they will reconvene to do the other
outstanding (de)serialization and logic on both ends later.

Now it is Liam's bedtime.

...

### 2023.02.15

Ari, here. Let's get a-rockin' !

As a summary, this is what we have now re. functionality: 
    - A client can connect to the server
    - A client can make a request and the server will echo the request back
    - We can also support multiple clients

We want to start building out the 'database', the datastructures kept on the server. So 
we're gonna begin by supporting client requests to create a User. The payload of the request 
should include simply the username. 

When the server gets the client's request, the server will add the message-- the username--
to a list of usernames.

We want to prompt the client when it connects for a username, so we will use python's
`input()` command.

We decide to transition to using a set instead of a list so someone logging in with the same
username will not create two copies of the username in the datastructure.

Everything is working as expected, so now as we prepare to support more functions, we will
start creating opcodes for the multiple operations. The opcodes will be one byte and
represented as an enum.

OK, now it's Max's turn to start scribin'

_"See ya soon!"_ ~ _AT_

...

We are currently refactoring the code to be extensible to both parts I and II:
I) Wire Protocol
II) GRPC

Even though serialization is different between parts I and II, some logic is shared:
- On both clients, the read-execute-print-loop logic should behave similarly.
- On both servers, database transactions should behave similarly.

Every operation has its own:
- argument types
- database transaction
- description
- opcode
- response types

In both parts, we invert control to common code that is shared between them.

_"Arf, she said."_ - Frank Zappa ~ _MS_

### 2023.02.21

The semantics of deleting an account containing undeliverered messages is that those messages are deleted.

_"Arf, she said."_ - Frank Zappa ~ _MS_
