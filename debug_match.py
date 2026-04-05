import sys

sys.path.insert(0, ".")

from src.composer.composer import BaseAgent
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    agent_home = Path(tmpdir) / "agents"
    agent_home.mkdir()
    root = Path(tmpdir)
    src_dir = root / "src"
    src_dir.mkdir()
    file = src_dir / "main.py"
    file.write_text("print")

    agent = BaseAgent(
        name="test",
        agent_home=agent_home,
        model=None,
        tools=[],
        root_folder=str(root),
        file_access=["./src/*.py"],
        read_only_file_access=[],
        deny_file_access=[],
    )

    print("root_folder:", agent.root_folder)
    print("file:", file)
    print("check read:", agent.check_file_access(str(file), "read"))
    print("check write:", agent.check_file_access(str(file), "write"))

    # test pattern matching
    from src.composer.composer import BaseComposer

    composer = BaseComposer(str(agent_home), {})
    # manually call init_agent? skip
    print("Done")
