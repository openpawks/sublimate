# ERD
![ERD](docs/imgs/erd.png)

# Endpoint plan
Prefix everything with `/api/v0/` if its an api endpoint.

User context is inferred from auth (JWT/session), not from URL path.

## Project

| METHODS | ENDPOINT | COMPLETE? | NOTES |
|-|-|-|-|
| GET, POST | /projects/ | Y | List all (optionally filter by `?user_id=`), create |
| GET, PATCH, DELETE | /projects/{project_id} | Y | CRUD by id |
| POST | /projects/import | N | Import a project into sublimate |

## Tasks

| METHODS | ENDPOINT | COMPLETE? | NOTES |
|-|-|-|-|
| GET, POST | /tasks/ | Y | List all (optionally filter by `?project_id=`), create |
| GET, PATCH, DELETE | /tasks/{task_id} | Y | CRUD by id |
| GET, POST | /tasks/{task_id}/chat | N | Get task chat, send message |
| WS | /ws/tasks/{task_id}/chat | N | Live chat feedback |

## Agents

| METHODS | ENDPOINT | COMPLETE? | NOTES |
|-|-|-|-|
| GET, POST | /agents/ | Y | List all (optionally filter by `?project_id=`), create |
| GET, PATCH, DELETE | /agents/{agent_id} | Y | CRUD by id |

## Chats

| METHODS | ENDPOINT | COMPLETE? | NOTES |
|-|-|-|-|
| GET, POST | /chats/ | Y | List all (optionally filter by `?task_id=`), create |
| GET, PATCH, DELETE | /chats/{chat_id} | Y | CRUD by id |

## Messages

| METHODS | ENDPOINT | COMPLETE? | NOTES |
|-|-|-|-|
| GET, POST | /messages/ | Y | List all (optionally filter by `?chat_id=`), create |
| GET, PATCH, DELETE | /messages/{message_id} | Y | CRUD by id |

## Providers

| METHODS | ENDPOINT | COMPLETE? | NOTES |
|-|-|-|-|
| GET, POST | /providers/ | Y | List all, create |
| GET, PATCH, DELETE | /providers/{provider_id} | Y | CRUD by id |

## User / Auth

| METHODS | ENDPOINT | COMPLETE? | NOTES |
|-|-|-|-|
| POST | /auth/login | N | login |
| GET | /auth/logout | N | logout |
| GET, PATCH | /auth/settings | N | get/update settings |


# Functional Features
| FEATURE | IMPLEMENTED |
|-|-|
| Create projects | Y |
| Importing projects | N |
| Set remote, add remote, remove remote etc | N |
| Task create, remove | Y |
| CRUD agents | Y |
| CRUD chats | Y |
| CRUD messages | Y |
| CRUD providers | Y |
| Frontend | N |
| TUI | N |

# Non Functional Features
| FEATURE | IMPLEMENTED |
|-|-|
| Multi user systems: create remove update accounts, with modern authentication | N |
| git integration, serve git from /git/ as an option - although this risks bloat, it would be very useful for new users to be able to manage their repos, should probably make user.name a unique field, also make root user on onboarding and prompt set password | N |
| simple git management in UI so that you can push, pull merge and stuff simply from sublimate, very useful for new users especially | N |
| forgot password reset, although encrypted stuff will be lost | N |
| user gets encryption options if they want | N |
| Api key encryption by user password hash & salt so master user can't see other people's API keys, useful if we want to serve this | N |
| `sublimate-agent` much like opencode or claude code just normal, single threaded local user coding, still can run sublimate server or save to user db, just as root account (and don't allow signups and stuff, serve on different port) | N |
| MCP integration, from /mcp/* endpoints | N |
| docker lmao | N |

# Datastorage prototype (to store data generated or in use by sublimate)
## Multi user
```
~/.sublimate/ # SERVER
  |- /u/{user_name}/{project_name}/
    |- .git/
    |- {branch/task names}/
  |- postgres/ (in future)
  |- sublimate.db
```

## Single user (mostly just if people _just_ want the coding agent, and nothing else, like opencode/claude-code alternative - no need to start the whole server!)
```
~/.config/sublimate/sublimate.json # SINGLE USER, API keys
```
