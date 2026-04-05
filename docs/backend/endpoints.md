# Planning endpoints

## Authentication & User Management
- Deepseek did okay here, but this is up to you how you want to plan this
```
POST   /auth/register          - Create new user account
POST   /auth/login             - Login (returns JWT/session token)
POST   /auth/logout            - Invalidate session
POST   /auth/refresh           - Refresh access token
GET    /users/me               - Get current user profile
PUT    /users/me               - Update user profile
POST   /users/me/change-password - Change password
```

## Project management
| METHODS | ROUTE | PURPOSE | COMPLETED? |
|-|-|-|-|
| GET,POST | /projects | List all projects for user | NO,YES |
| PATCH,PUT,DELETE | /projects/{project_id} |  Update and delete project, we should make it manage the sublimate-compose.yml aswell as the db ) | SOME,, |
| GET,POST | /{project_id}/tasks | See all tasks for project, Add task to project | SOME, |
| GET,DELETE | /{project_id}/tasks/{task_id} | Get task for project, Delete task | SOME, |
| GET,POST | /{project_id}/tasks/{task_id}/chat | Get task chat (messages), Add message to task chat | NO, |

## Project Start/Stop Management & Monitoring
| METHODS | ROUTE | PURPOSE | COMPLETED? |
|-|-|-|-|
| GET,POST,DELETE | /projects/{project_id}/runtime | Get status of daemon, is it running, Start daemon, Stop Daemon | NO,, |
| GET | /projects/{project_id}/runtime/{agent_name} | Get status of agent daemon | NO |

## Agent configuration (per projects)

| METHODS | ROUTE | PURPOSE | COMPLETED? |
|-|-|-|-|
| GET,POST | /projects/{project_id}/agents | Get agents in agent_home, Add agent to agent home | NO, |
| GET | /projects/{project_id}/agent_states | Get all agent states | NO |
| GET,PUT,DELETE | /projects/{project_id}/agents/{agent_name} | Get agent, | |
| GET | /projects/{project_id}/agents/{agent_name}/state | Get agent states (logs) | NO |
| GET,DELETE | /projects/{project_id}/agents/{agent_name}/state/{state_timestamp} | Get specific state, delete specific state |

## Manage agent templates library
