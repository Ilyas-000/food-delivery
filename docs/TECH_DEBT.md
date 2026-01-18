# Technical Debt

This file tracks agreed technical debt items for later cleanup.

## Backlog

- Naming consistency: simplify and clarify naming (DTO/use_case, module names, route names).
- Over-commented code: reduce boilerplate/explanatory comments, keep only non-obvious logic notes.
- API responses metadata: large inline `responses` blocks in routes should be simplified or moved.
- PyCharm IDE: absolute imports (`from src...`) show as unresolved because multiple services expose a `src` package in one module; document a multi-module setup or add a shared IDE config to avoid red imports.
