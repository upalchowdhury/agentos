# Contributing to Agent Economy OS

## Development Setup

1. Fork the repository
2. Clone your fork
3. Run `./scripts/dev-setup.sh`
4. Create a feature branch

## Code Standards

### Go (Gateway)
- Follow production-grade rules in `.windsurf/agentosbuildingguide.md`
- Max function length: 50 lines
- Unit test coverage: >80%
- Use table-driven tests
- Run: `go vet ./...` and `golangci-lint run`

### TypeScript (Identity)
- ESLint with max warnings: 0
- Strict TypeScript mode
- Explicit error handling
- Run: `npm run lint`

### Python (Memory)
- Black formatter (line length: 100)
- Ruff linter
- Type hints with mypy
- Run: `black . && ruff check . && mypy src/`

### Rust (Policy Engine)
- Clippy with deny warnings
- Format with rustfmt
- Run: `cargo clippy -- -D warnings && cargo fmt --check`

## Testing

```bash
# All tests
./scripts/test-all.sh

# Service-specific
cd services/gateway && go test -v ./...
cd services/identity && npm test
cd services/memory && pytest
cd services/policy-engine && cargo test
```

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new functionality
4. Follow commit message format: `type(scope): description`
   - types: feat, fix, docs, refactor, test, chore
5. Request review from maintainers

## Commit Message Examples

```
feat(gateway): add rate limiting middleware
fix(identity): resolve DID verification issue
docs(api): update credential issuance examples
test(memory): add vector store integration tests
refactor(policy): simplify rule evaluation logic
```

## Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass and cover new code
- [ ] No hardcoded values or secrets
- [ ] Error handling is comprehensive
- [ ] Documentation is updated
- [ ] Performance impact considered
- [ ] Security implications reviewed

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
