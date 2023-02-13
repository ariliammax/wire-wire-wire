Some nice structure comments:

- branch `main` will be the final branch. PR will be PRs into this branch.
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

