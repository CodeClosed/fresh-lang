---
applyTo: "**/*.{test,spec}.{js,ts,jsx,tsx,py}"
---
# Testing Guidelines

- Follow the Arrange-Act-Assert (AAA) pattern in all unit tests.
- Use descriptive test names that state the expected behavior (`should <expected behavior> when <condition>`).
- Mock external network calls, databases, and filesystem side effects.
