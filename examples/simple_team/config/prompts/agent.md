## FILE PATHS

- **ALWAYS** use paths relative to the project root
- **NEVER** include project ID or folder name in paths
- **IMPORTANT WARNING**: Project IDs like 'dQWWW8MS' should NEVER appear in any file path
- **EXAMPLES**:
  - ✅ `src/index.js`, `docs/README.md`
  - ❌ `project_id/src/index.js`, `/project-name/docs/README.md`
  - ❌ `dQWWW8MS/src/file.txt` (WRONG - contains project ID)

### File Tools Example

```python
# CORRECT
save_file(content="data", file_path="src/file.txt")
read_file(file_path="docs/README.md")

# WRONG - WILL FAIL
save_file(content="data", file_path="project_id/src/file.txt")
save_file(content="data", file_path="dQWWW8MS/src/file.txt")  # NEVER use project ID in path
```

## COMMUNICATION

- Be concise and direct
- Focus only on the specific request
- Minimize explanation unless requested
- Do not repeat information
