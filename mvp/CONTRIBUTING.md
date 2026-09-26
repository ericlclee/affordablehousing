# Maria's contribution workflow

The official team repository is `ericlclee/affordablehousing`. Maria's fork is `mparanzales/affordablehousing`.

1. Fetch the latest official `main` before starting a task.
2. Create a new branch from that baseline, such as `maria/proposal106-updates`.
3. Copy in the intended updates, preserve source files, and review the difference.
4. Run relevant checks and test the browser preview.
5. Push the branch to Maria's fork (`origin`).
6. Open a pull request from that branch to the official repository's `main`.
7. The team reviews and merges. Keep unfinished work in a draft PR.

Do not push directly to the official `main` or force-push over teammates' work. A fork is created once; subsequent tasks use new branches in the same fork.

The local working copy used for this contribution sets `origin` to Maria's fork and `upstream` to the official repository, with upstream pushes disabled. Those local settings do not automatically transfer to other clones. Claude and Codex should follow the same branch-and-PR workflow and avoid editing the same file simultaneously.

The Proposal 106 snapshot is in [`proposal106/`](proposal106/README.md); the original MVP remains in `dist/`.
