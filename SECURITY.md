# Security

Security is part of the product, not an afterthought.

## Current expectations

- validate all input data with Pydantic
- keep API responses structured and predictable
- avoid trusting raw user input
- avoid exposing secrets in prompts or logs

## Security topics to cover early

- authentication and authorization
- roles and permissions
- secrets management
- rate limiting
- XSS protection for any future frontend
- CSRF considerations if browser-based state changes are added
- SQL injection prevention once a database layer is introduced

## Operational concerns

- monitoring
- observability
- error handling
- safe logging
- dependency hygiene

## MVP rule

Every new feature should be checked for its security impact before it becomes a default behavior.

