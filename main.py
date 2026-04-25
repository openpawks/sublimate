import uvicorn
import inquirer
import time

from src.backend.app import app
from src.config import settings


# TODO: Use inquirer for onboarding
# - setting up deps for langchain (like langchain[deepseek] or langchain[ollama])
# - setting up auth and admin users
# - setting up database management and stuff
# - setting up server and port, other stuff in config
sublimate_text = (
    r"""
                        88           88  88
                        88           88  ""                                    ,d
                        88           88                                        88
,adPPYba,  88       88  88,dPPYba,   88  88  88,dPYba,,adPYba,   ,adPPYYba,  MM88MMM  ,adPPYba,
I8[    ""  88       88  88P'    "8a  88  88  88P'   "88"    "8a  ""     `Y8    88    a8P_____88
 `"Y8ba,   88       88  88       d8  88  88  88      88      88  ,adPPPPP88    88    8PP"""
    """"
aa    ]8I  "8a,   ,a88  88b,   ,a8"  88  88  88      88      88  88,    ,88    88,   "8b,   ,aa
`"YbbdP"'   `"YbbdP'Y8  8Y"Ybbd8"'   88  88  88      88      88  `"8bbdP"Y8    "Y888  `"Ybbd8"'

"""
)


def main():
    # Let me have fun!

    if "absolutely_not" not in settings.get("fun", []):
        print("\033[96m")
        for index, char in enumerate(sublimate_text):
            print(char, end="", flush=True)
            if settings.get("fun", True):
                time.sleep(0.0005)

        print("\033[1m", flush=True)
        for char in ">> IN ALPHA":
            print(char, end="", flush=True)
            if settings.get("fun", True):
                time.sleep(0.09)

        print("\n")

    quickstart = (
        inquirer.list_input(
            "Start server, or edit config", choices=["server", "config"]
        )
        == "server"
    )

    if quickstart:
        uvicorn.run(app, **settings.get("uvicorn"))
    else:
        print("Not implemented!")


if __name__ == "__main__":
    main()
