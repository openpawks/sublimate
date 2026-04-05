# Welcome to Sublimate

An automated code management system. Using Sublimate, unlike other AI assisted development systems, sublimate is designed to be:

# Goals

- Remotely accessible
- Working in the background
- Accessible from a CLI, TUI, web frontend, or by API
- Writes robust tests
- Multiple users
- Easy to work with
- Server should be lightweight, fast and efficient
- (Hopefully) Verbose documentation for custom implementations and community support
- Provide a few agent templates to easily work with for quick startup

# ROADMAP

## Functionality

- Manage multiple projects from your interface of choice
- Agents should be able to find errors when testing code
- Agents should be able to run in the background
- Some agents don't have to see the whole codebase to write new code, smartly select relevant areas of the codebase
  - In order not to overwhelm context limits, and grasp just what needs to be known for each change
- Add tasks for an agent to complete
  - Agents may add tasks when they find errors, and that may be completed by another

# Tech stack
| Library/Framework | Purpose |
|-|-|
| FastAPI | Server Backend |
| Langchain | Connect LLMs to sublimate |
| Sqlite/Postgres | Database management, early on we'll use Sqlite for testing and initial prototypes, planning to migrate to postgres |
| Jinja2Templates/React | Frontend (webui) Jinja2Templates for initial prototypes, eventually planning for React |

# Documentation

Comprehensive documentation is available for key components:

- [Composer System](docs/composer.md): Detailed guide to agent orchestration, configuration, and usage
- [Agent Templates](agent_templates/default/): Example configurations and prompts
- [Testing](tests/): Test suite with mocking strategies

# This project is in development

This project is in development


