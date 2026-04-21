# ERD
![ERD][docs/imgs/erd.png]

# Endpoint plan
## Project
| METHODS | ENDPOINT | URL | COMPLETE? |
|-|-|-|-|
| GET | /api/projects/ | Get all projects for user | N |

# Functional Features
| FEATURE | IMPLEMENTED |
|-|-|
| Create projects | N |
| Importing projects | N |
| Set remote, add remote, remove remote etc | N |
| Task create, remove | N |
...more

# Non Functional Features
| FEATURE | IMPLEMENTED |
|-|-|
| Multi user systems: create remove update accounts | N |
...more

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
![Web layout][docs/imgs/web_layout_plan.png]
