# Planning endpoints

## Authentication & User Management
- Deepseek did okay here, but this is up to you how you want to plan this
- Authentication low priority as of now.
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

## Task management
| METHODS | ROUTE | PURPOSE | COMPLETED? |
|-|-|-|-|
| GET,POST | /{project_id}/tasks | See all tasks for project, Add task to project | SOME, |
| GET,PATCH,DELETE | /{project_id}/tasks/{task_id} | Get task for project (and details, like who is assigned, chatid), Update who is assigned or task status (closed, etc), Delete task | SOME, |
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
| GET,PUT,DELETE | /projects/{project_id}/agents/{agent_name} | Get agent, Update agent prompt, Delete agent, should also automatically delete from config file | NO,, |
| GET | /projects/{project_id}/agents/heartbeat | Get agent heartbeat configuration | NO |
| PATCH, PUT | /projects/{project_id}/agents/heartbeat | Update agent heartbeat configuration, full | NO |
| GET | /projects/{project_id}/agents/{agent_name}/state | Get agent states (logs) | NO |
| GET,DELETE | /projects/{project_id}/agents/{agent_name}/state/{state_timestamp} | Get specific state, delete specific state |
| GET | /agent-templates | Get agent templates | NO |
| GET | /project-templates | Get project templates | NO |
| POST | /projects/from-template | Create project from template | NO |
| PUT | /projects/{project_id}/from-template | Update project agent template with preset | NO |

## Provider management (per user)
Ideally, API keys should be (password) encrypted. This may be a difficult task
| METHODS | ROUTE | PURPOSE | COMPLETED? |
|-|-|-|-|
| GET, POST | /providers | List configured AI providers, add new provider (by name) | NO |
| GET, PUT, DELETE | /providers/{provider_name} | Get provider details, update with new settings | NO |
| GET | /providers/{provider_name}/test | Test provider works | NO |
| GET | /providers/available | List available providers, we will have some presets | NO |



# THIS IS UNFINISHED, MANY POTENTIAL FEATURES ARE CURRENTLY NOT MARKED
Unmarked as of yet
- More monitoring metrics
- File and configuration management /projects/{project_id}/files/{path}
- Agent communication (low priority)
- Websocket endpoints for realtime updates (low priority)
- Admin endpoints (low priority)
- Version control endpoints
