# Errors

Log of command failures, exceptions, and unexpected behaviors.

## Format

```markdown
## [ERR-YYYYMMDD-XXX] skill_or_command

**Logged**: ISO-8601 timestamp
**Priority**: high
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
Brief description

### Error
```
Actual error message
```

### Context
- Command attempted
- Input/parameters
- Environment

### Suggested Fix
Resolution approach

### Metadata
- Reproducible: yes | no | unknown
- Related Files: path/to/file
- See Also: ERR-...

---
```

## Entries

