# 🚀 Automated Release System

This project uses an automated release system that follows semantic versioning with a `0.minor.patch` format.

## 📋 How It Works

### **Triggers**

- ✅ **Automatically on push to main branch**
- ✅ **Manual trigger available** via GitHub Actions UI

### **Version Bumping Rules**

- **Major version**: Always stays at `0` (pre-1.0 project)
- **Minor version**: Increments for commits starting with `feat:` or `feature:`
- **Patch version**: Increments for all other commits (`fix:`, `docs:`, `chore:`, etc.)

### **What Gets Updated**

- ✅ `pyproject.toml` - Project version
- ✅ `src/agentx/__init__.py` - Package `__version__` variable
- ✅ Git tag created (e.g., `v0.10.0`)
- ✅ GitHub release with auto-generated notes
- ✅ PyPI package published automatically

## 🎯 Usage Examples

### **Feature Release (Minor Bump)**

```bash
git commit -m "feat: add new agent routing system"
git push origin main
# → Creates release 0.10.0 (if current is 0.9.3)
```

### **Bug Fix Release (Patch Bump)**

```bash
git commit -m "fix: resolve memory initialization issue"
git push origin main
# → Creates release 0.9.4 (if current is 0.9.3)
```

### **Documentation/Chore Release (Patch Bump)**

```bash
git commit -m "docs: update README with new examples"
git commit -m "chore: update dependencies"
git push origin main
# → Creates release 0.9.4 (if current is 0.9.3)
```

## 📝 Release Notes Generation

Release notes are automatically generated from commit messages and categorized:

- **✨ New Features** - `feat:` commits
- **🐛 Bug Fixes** - `fix:` commits
- **📚 Documentation** - `docs:` commits
- **🔧 Other Changes** - All other commits

Each entry includes the commit hash for reference.

## 🔄 Complete Workflow

1. **Push to main** → Auto-release workflow runs
2. **Analyzes commits** → Determines version bump type
3. **Updates versions** → Both `pyproject.toml` and `__init__.py`
4. **Commits changes** → Version bump commit pushed back
5. **Creates GitHub release** → With auto-generated notes
6. **PyPI workflow triggers** → Package published automatically

## ⚙️ Manual Release

You can also trigger a release manually:

1. Go to **Actions** tab in GitHub
2. Select **Auto Release** workflow
3. Click **Run workflow**
4. Choose the **main** branch
5. Click **Run workflow**

## 🚫 Skipping Releases

The system automatically skips releases when:

- No new commits since last release
- Only merge commits or version bump commits

## 📊 Monitoring

Check the **Actions** tab to monitor release workflows and see detailed logs of the version analysis and release process.
