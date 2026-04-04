# MUTE ME
okay, so seems like a "project" should manage each "agent" like this [according to deepseek](https://chat.deepseek.com/share/3ehnbv327upq3spow6)
DEEPSEEK SUGGESTED IDEA - NOT FINAL
```
your-project-root/
├── AGENTS.md
├── agents/
│   ├── main.md
│   ├── researcher.md
│   ├── writer.md
│   ├── monitor.md           # Dedicated monitoring agent
│   │
│   ├── heartbeats/          # NEW: Per-agent heartbeat directory
│   │   ├── researcher.heartbeat.md
│   │   ├── writer.heartbeat.md
│   │   ├── monitor.heartbeat.md
│   │   └── main.heartbeat.md
│   │
│   └── shared/
│       └── heartbeat_schema.md  # Common format specification
│
└── docs/
    ├── agent_states/        # Track last heartbeat results
    │   ├── researcher_state.md
    │   ├── writer_state.md
    │   └── monitor_state.md
    └── ...
```
so i guess instead of storing it in the db, we just store agents in the project_root & agent_root i guess.. not sure why deepseek said that agent_states should go in docs/ though - seems iffy to me. maybe i could move agent_states to agents/ ?

we could also give some of the "agents" tools to "create" other "agents" and stuff. (main.md)

so the plan is that it'll be dynamically generated per project from filestructure, and stored :nauseated_face: in memory

...

what we _could_ do is have a nice simple interface, but still lets you understand the file structure.
inside agents_home, maybe there should be a `tasks/` or `issues/` thing for each agent to see issue status blah blah blah

my adapted one...
WAITING APPROVAL
```
your-project-root/
├── AGENTS.md
├── agents/
│   ├── main.md
│   ├── researcher.md
│   ├── writer.md
│   ├── monitor.md           # Dedicated monitoring agent
│   │
│   ├── tasks/
│   │   ├── uuid/ # if new one unaccounted for, will add to database or something idk
│   │   │   ├── task.md # or issue summary? 
# YOU _COULD_ STORE CHAT HISTORY HERE... but probably can keep it inside our db for quick querying and stuff idk
│   │  
│   │ 
│   ├── heartbeats/          # NEW: Per-agent heartbeat directory
│   │   ├── researcher.heartbeat.md
│   │   ├── writer.heartbeat.md
│   │   ├── monitor.heartbeat.md
│   │   └── main.heartbeat.md
    │
    ├── agent_states/        # Track last heartbeat results
        │   ├── researcher.state.md
        │   ├── writer.state.md
        │   └── monitor.state.md
        └── ...
│   │
│   └── shared/
│       └── heartbeat_schema.md  # Common format specification
│
└── docs/
```
not _too_ sure if we _need_ `tasks/`, that can be handled within our database i guess.

## main.md schema
```
---
name: main
desc: Project lead orchestrator and delegator
model: openai/gpt-4o
temperature: 0.7
handoffs: researcher, writer
---

You are the project lead. Your job is to route requests to the correct specialized agent.
If the user asks for research, hand off to `researcher`.
If the user asks to write code, hand off to `writer`.
```
## *.heartbeat.md schema
```
---
agent: monitor
schedule: "* * * * *"        # Every minute LOOKS A LOT LIKE CRONJOB SYNTAX
timeout: 30s
priority: high
dependencies: researcher, writer   # Wait for these to finish first
---

# Monitor Agent - System Health

## Health Checks
- [ ] Verify all agent heartbeat files are ≤ 5 minutes old
- [ ] Check disk space for `/docs/` directory
- [ ] Validate API keys for all configured tools

## Recovery Actions
- If researcher.heartbeat.md is stale: Restart researcher agent
- If disk space < 10%: Trigger cleanup script

## Reporting
- Log status to `/docs/agent_states/system_health.md`
- If critical: Send alert to MAIN agent with @alert
```

also says we should build an orchestrator for this... not _too_ hard to do. 
example in my [shared deepseek chat](https://chat.deepseek.com/share/3ehnbv327upq3spow6)

we could also automatically generate these with AI and stuff, what people are going to want us to do.
we can have a few presets, easy to select and choose from (which would definitely help, paperclip has no such thing)

DEEPSEEK ORCHESTRATOR EXAMPLE
```python
# heartbeat_orchestrator.py
import schedule
import time
from pathlib import Path

class HeartbeatOrchestrator:
    def __init__(self, agents_home="./AGENT_HOME"):
        self.agents_home = Path(agents_home)
        self.heartbeat_dir = self.agents_home / "agents" / "heartbeats"
        
    def load_heartbeat_config(self, agent_name):
        """Parse the .heartbeat.md file for schedule and tasks"""
        hb_file = self.heartbeat_dir / f"{agent_name}.heartbeat.md"
        # Parse YAML frontmatter and extract tasks
        return config
    
    def execute_agent_heartbeat(self, agent_name):
        """Run a specific agent's heartbeat tasks"""
        print(f"💓 Executing heartbeat for {agent_name}")
        
        # 1. Read the agent's heartbeat config
        config = self.load_heartbeat_config(agent_name)
        
        # 2. Check dependencies
        if not self.dependencies_satisfied(config['dependencies']):
            print(f"⏸️ {agent_name} waiting for dependencies")
            return
        
        # 3. Spawn agent subprocess
        result = subprocess.run([
            "agent-runner", 
            agent_name,
            "--heartbeat-mode",
            "--tasks", config['tasks']
        ])
        
        # 4. Update state
        self.update_agent_state(agent_name, result)
        
    def run(self):
        # Schedule each agent based on its cron expression
        for agent in ['researcher', 'writer', 'monitor', 'main']:
            config = self.load_heartbeat_config(agent)
            schedule.every().minute.do(
                self.execute_agent_heartbeat, 
                agent
            ).tag(agent)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
```
don't think we'll be using this exactly, but its a good boilerplate.
```
```
