# Contributing to Sublimate

Thank you for your interest in contributing to Sublimate!

We deeply value every contribution to this project. Open source thrives when developers share their expertise, creativity, and passion. Whether you're fixing a typo, optimizing performance, adding a feature, or helping with documentation — your work directly impacts researchers and developers worldwide. Code contributions are not the only way to help: answering questions, reporting bugs, and improving documentation are equally valuable. We carefully review all PRs and are genuinely excited to merge contributions that enhance the project. This is truly a community-driven project, and we're honored to have you join us.

### Before You Start

**Please keep PRs small and atomic.** One fix, one feature, one change per PR. This repository has grown in complexity, and large or cross-cutting PRs become very difficult to review safely. Small, focused PRs are easier to review, faster to merge, and less likely to introduce regressions. If your change touches multiple concerns, split it into separate PRs — this protects your time as much as ours.

**Talk to us before building large changes.** Open an issue, start a discussion, or drop a message on Discord (when we make a server...). This helps us reach agreement on your approach before you put significant effort into it. For small fixes (typos, bugs with obvious solutions), feel free to open a PR directly. For anything larger, a quick comment like this goes a long way:

> "I'd like to work on this. My intended approach would be to [brief description]. Does this align with what you'd expect?"

**Don't hesitate to ask questions.** A lot of people worry about "wasting the team's time," but we genuinely don't feel that way — contributors are important to us. Both core team members and external contributors go through the same review process, and review feedback is completely normal (it happens to our core contributors too).

## 🚀 Quick Start

1. **Fork and clone the repository**
2. **Set up your development environment**
3. **Create a new branch** for your feature or fix

## 💻 Development Workflow

We use `uv` to manage the environment. You should install `uv`, as our pre-commit hooks are configured for `uv`.

### Install pre-commit hooks & environment configuration

Install our environment by running
```
uv sync
```
And to install pre commit checks, run
```
uv run pre-commit install
```
It is best practice to use the pre-commit hooks.

### Configuration

Never commit sensitive information like API keys or passwords. Configuration is typically done through the web UI.

### Testing

Run tests before submitting PRs, however this _should_ be configured by our pre-commit checks. If you see any errors when committing, please fix them and then commit.
If you add a feature, it's reccomended to also add tests for that new feature, so that the rest of us don't accidentally break it.

To run a test, do
```
uv run pytest
```

## 📋 Pull Request Process

1. **Search first** — Check existing PRs and issues to make sure nobody is already working on the same thing
2. **Comment before you code** — If you're picking up an issue, leave a comment so others don't duplicate your effort
3. **Create a focused PR** — One feature/fix per PR. If your PR is large or cross-cutting, consider splitting it
4. **Write clear commit messages** — Explain what and why, not just what changed
5. **Add tests** — Include tests for new functionality
6. **Update documentation** — Keep docs in sync with code changes
7. **Ensure CI passes** — All automated checks must pass. Address CI failures promptly

We will review your pull request and either merge it, request changes, or close it with an explanation. Don't worry about things like commit message formatting — we squash-merge and can adjust the final message.


## 🤝 Community

- **Issues**: Check existing issues before opening new ones
- **Wiki**: Contribute to building our wiki!

## 📝 Code of Conduct

- Be respectful and professional
- Welcome newcomers with patience
- Focus on constructive feedback
- Report inappropriate behavior to maintainers

Thank you for helping improve Sublimate!
