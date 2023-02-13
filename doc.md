Some nice structure comments:

- branch `main` will be the final branch. Final PR will be PRs into `main`.
- branch `common` will be the PR of code that is shared in `wire` and `grpc`.
- branch `wire` has the first part of the design exercise: the wire protocol.
- branch `grpc` has the second part: the gRPC implementation.

Notes for Ari, Liam, and Max while working:

- when updating `common`, then afterwards go to each of `wire` and `grpc` and

```bash
git checkout [wire|grpc]
git rebase common
```

to get any updates from `common` branch.

We shouldn't want to deal with the hassle of adding a new git account to our
command line (at least, Liam doesn't), so just use your personal account to
make the changes on each of `common`, `wire`, and `grpc`, then the
`ariliammax` account will make the final brush-ups and PRs etc.

