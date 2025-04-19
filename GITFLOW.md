# 🌀 GitFlow Workflow for Skaven Soundscape

We follow the **GitFlow** branching model to ensure a clean, maintainable, and release-ready codebase at all times.

---

## 🧱 Branch Types

| Branch Type     | Prefix      | Purpose                                    |
|-----------------|-------------|--------------------------------------------|
| `main`          | —           | Always deployable. Tagged releases only.   |
| `develop`       | —           | Integration branch. All features merge here. |
| Feature branch  | `feature/`  | New functionality and enhancements         |
| Bugfix branch   | `fix/`      | Non-hotfix bug corrections                 |
| Hotfix branch   | `hotfix/`   | Emergency fix for `main`                   |
| Release branch  | `release/`  | Final polishing before tagging             |

---

## 🛠 Workflow Summary

1. **New work?**

   ```bash
   git checkout develop
   git pull
   git checkout -b feature/<thing>
   ```

2. **Complete your work, commit regularly**, referencing an issue (e.g. `fixes #42`).

3. **Open a PR against `develop`**.
   - Must pass all CI checks
   - Must link a GitHub Issue via PR sidebar (enforced by workflow)

4. **Prepare a release**:

   ```bash
   git checkout develop
   git checkout -b release/v0.1.0
   # Optional: update version or docs
   git push origin release/v0.1.0

   ```

   Merge into `main`, tag it, and let GitHub Actions handle the release.

5. **Hotfixes** go directly from `main`:

   ```bash
   git checkout main
   git checkout -b hotfix/serious-bug
   ```

---

## 🧪 PR & Commit Rules

✅ All commits must include an issue reference: `fixes #123`
✅ PRs must target `develop`, not `main`
✅ PRs must use sidebar **Linked Issues** field (required, enforced)
✅ PRs require review and passing CI
✅ `main` and `develop` are protected branches

---

## 🧙‍♂️ The Council of Thirteen Demands Order

This structure ensures:

- Clean history
- Safe deployment
- Clear changelogs
- Happy contributors 🐀
