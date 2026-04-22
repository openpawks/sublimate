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

# Non Functional Features
| FEATURE | IMPLEMENTED |
|-|-|
| Multi user systems: create remove update accounts | N |

# Datastorage prototype (to store data generated or in use by sublimate)
```
~/.sublimate/
|-  projects/
    |-  {project_name}.git/ # bare repository
        |-  sublimate/
            |-  {branch_name}
|-  postgres/
```

# Web layout
Coming soon!
![Web layout](docs/imgs/web_layout_plan.png)
