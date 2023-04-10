# Design exercises: Replication
## Ari Troper, Liam McInroy, Max Snyder

### 2023.04.07

#### First notes

Initial setup of project. We're continuing off of the
[`wire`](https://github.com/ariliammax/wire) repo from the first design
exercise. There's some implementation notes there, which we won't duplicate
here for the most part, which are interesting.

One important note from that repo for the purposes of this exercise is:

- there is a singleton `Database` instance in the non-replicated version.
This exercise will make that persistent (we just write to a plain text file)
and replicated (this will require some server communication).

Our perspective is that this exercise is basically about implementing a
distributed database, so we will just make the `Database` singleton have the
ability to communicate to other servers. These servers will be behind the
"trust boundary"; they will have their own socket connections to each other
(rather than say, mimicking a replica as a "man in the middle" client, and
implicitly trusting clients). Another nice implementation benefit of this
decision is that it will limit any edits outside of the implementation of
`Database`.

There's now a bunch to unwind for the actual design, originating from this
first decision. So strap in.

#### Design of replication protocol

- (i) We want 2-fault tolerance, and we only want to support up to fail-stop
and crash failure; so three machines will suffice, and if a machine ever fails
then we can safely assume it has failed for eternity (unless the entire system
is restarted).

On the second point: in the case of any failure, the other machines will
communicate the failure and will ignore that machine for the remainder of
eternity; since we are not dealing with byzantine failures, then we assume
messages indicating another machine have failed will always be truthful.

- (ii) Now, we will make the assertion that "correctness" is determined by the
client; if any request by a client is given a response, then whatever
data changes prerequisite to that response has been replicated across the
system. As a simple example: a client says "send 'hi' to 'max'" then gets the
response "ok"; all of the (non-failed) replicas have persisted the
"'hi' to 'max'" message. As a more complicated example: the client sends a
message, a replication fails, that machine is deemed failed by (i), but the
replication still "succeeds" (in the sense that it is now 1-fault tolerant),
and so the client still gets a request.

The natural question is: when does a client get a failure? This will be
answered in (iii).

- (iii) We don't want to set up some complicated system to tell clients which
replica to connect to, nor do we want a single intermediate machine which just
"forwards" requests and response along to the replicas (that is now 0-fault
tolerant if the intermediary fails). So we'll allow clients to directly connect
to any replica they'd like.

To answer the question of (ii): a client gets a failure when there is a failure
of the replica which the client is connected to! This requires some client-side
logic to then know to move onto a new replica.

NB: There is a chance the machine "fails" from the perspective of inside the
trust boundary, so there might be "byzantine-esqe" behavior from the
perspective of the client in this case. We will incorporate some logic
inside of the trust boundary to tell a machine it's considered dead (so fail
all responses to clients) to handle this case; see (TODO) for details.

- With (i-iii), we have described all behavior relating to the outside
of the trust boundary. In (iv) onwards, we will look at the design within the
trust boundary.

- (iv) We would like the entire system to be a state machine. Any change in
state is caused by a client connection (this is the only time the database will
be modified). A modification of a database (on any replica) must trigger a
synchronization across all of the replicas before a gesponse is given to the
client by (ii).

Rather than implement some sort of complicated distributed consensus (paxos),
we are opting for a "primary" replica which triggers the synchronizations to
the "secondary" (or "tertiary") replicas.

- (v) Since any replica can receive database updates, but we want the "primary"
replica to trigger the synchronization to the other replicas by (iv), then we
will introduce a "queue" message for the non-primary replicas to send to the
primary replica to indicate incoming database updates.

The primary replica in turn triggers "synchronization" messages to each of the
non-primary replicas. Upon successful "synchronization", the primary replica
will respond to the "queue" message, and the non-primary replica (which the
client is connected to) may continue. This ensures that updates are atomic
and transactional.

If the client is connected to the primary replica, then any database update
simply triggers the "synchronization" step (we don't "queue" updates to the
primary replica from the primary replica). To maintain the atomic and
transactional updates, we add a lock to this step and the "queue" receiving.

This fully describes the replication process; we still need the 2-fault
tolerance protocol.

- (vi) Suppose the primary replica fails; the non-primary replicas will observe
this behavior by (i). Rather than implement a consensus algorithm (paxos) for
which replica will become the new primary replica, we assume that every replica
has access to both a "replica priority" ordering and the knowledge of its and
other replica's names; this means there is a "secondary" and "tertiary"
replica, and both replicas will know that the "secondary" replica becomes the
primary replica if the original primary fails, and so on.

A failure of the primary replica is observed by a failure of the "queueing"
process; we don't need to check failures of the "syncing" messages, since a
failure of these would cause a failure of the "queueing" message as well.

A failure of a non-primary replica is observed by the primary replica by a
failure of the "syncing" messages. Then future "synchronizations" will not be
sent to the failed non-primary replica from the primary replica. If the primary
changes, this failure will be observed by the new primary as well by (i).

A failure of any replica is observed by the client by any failure to respond.
Upon such failures, the client will simply change its connection to another
replica; it doesn't matter which other replica by (iii), and if that replica is
failed then the next will be tried.

- (vii) Since fail-stop failures are a subset of crash failures (and we aren't
considering byzantine failures), we will define a "failure" as any failure of
communication along a socket. We observe such failures by either (vii-a) an
unexpected dropped connection, or (vii-b) a timeout of an expected response.
In implementation, (vii-a) is observed a little differently than (vii-b), but
for our purposes of this design specification, we'll consider requests to
always be communicated so any error is observed as a timeout (it may just be
observed instantly if the connection is dropped).

For convenience to represent the three kinds of messages, we use three sockets
on each replica; for the client, queueing, and synchronization (there are
actually five sockets; there are two queueing and synchronization sockets to
clearly indicate which pair of replicas the socket is between). There
may be failures at each level which dictate further behavior and communication.
This means that (vii-1) with the (iii) interpretation that a client expects a
failure only if the replica it is speaking to is dead, then the client timeout
should be longest; (vii-2) the (vi) interpretation that a queue failure
indicates a change in the primary replica, and then repeating behavior with the
new primary replica that depends on the synchronization socket; so the queueing
timeout should be longer than the synchronization but shorter than the client.

We'll use an order of magnitude between each timeout.

#### Design of persistence protocol

Suppose now that replication is perfect (well, at least 2-fault tolerant).
Persistence of a single replica is implicitly covered in (ii); once a replica
is dead, it is dead to the other alive replicas. This doesn't implement
"system-wide" persistence; i.e. we kill all of the replicas and then bring them
back to life.

As an example: suppose that two replicas fail (the first and second priority
replicas, for instance). The third replica has the most up-to-date persisted
data, so the system-wide "startup" should account for this. This is relatively
easy to handle:

- (viii) On all replicas "startup", the replicas communicate whether they were
ever the primary. The lowest priority replica then communicates their locally
persisted state to the primary replica (which in turn synchronizes it to the
others). The system is not considered "alive" and won't accept client
connections until this "startup" is concluded (the replicas will accept
"synchronize" messages).

We are happy to make the assumption that a failure will not occur during the
startup protocol, but it is an unnecessarily strong assumption; we assume only
that the initial "I was primary or not" and "this was my last state" messages
have no failures (if a synchronization fails after this part, this is handled
in the replication protocol).

#### Accumulative assumptions

For the reader's sake, here are all of the crucial assumptions in the design
of both the replication and persistence protocols.

- (A1) The startup protocol from a well-formed state succeeds without failures,
and this startup will terminate before client connections are requested.

- (A2) Each replica knows its name, the addresses of the other replicas, and
then may deduce their name and state. There is also a predetermined "primary
priority" ordering on the names of replicas, so that replicas may deduce
whether they should become primary when a new failure is observed. The clients
also know the addresses of all replicas.

- (A3) Failures are limited to crash failures, which may be observed by
timeouts / disconnections on the sockets. To avoid byzantine failures, we
assume all replicas are behind the trust boundary and may only communicate if
they have not failed.

- (A4) Failed replicas only come back to life on an entire system restart.

With (A1-4), then (i-viii) ensure that the system is both 2-fault tolerant and
persistent (to system-wide restarts).

### 2023.04.08

#### Implementation notes

We're now to the implementing steps (which require much less explanation than
the design notes).

- Apparently. If you try to retry a `connection` on a `socket`, you must
recreate a new instance of the `socket`, otherwise you some dumb error on
retries. _Sigh_

### 2023.04.09

#### Implementation notes

- We sometimes forgot whether to `sendall` on the `connection` or `socket`;
this led to a bit of confusion for a little while.

- Accidentally inverted the value of the `was_primary` booleans in the startup
protocol... chaos insued.

- There seems to be some instability in the startup protocol if there are
not persisted data (or it is empty) and one or more of the was primary files
is missing. Basically the forced sync of startup seems to be blocking.

- There is some pain in trying to integration test, since our database
singleton is really a class instance.

...

