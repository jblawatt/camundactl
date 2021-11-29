import os

import asyncio
from camundactl.cmd.base import init, root


async def _main_async():

    init()

    if "CCTL_PROFILE" in os.environ:
        filename = os.getenv("CCTL_PROFILE")
        import cProfile

        profile = cProfile.Profile()
        try:
            profile.runcall(root)
        finally:
            profile.dump_stats(filename)
    else:
        root()

def _main():
    asyncio.run(_main_async())

if __name__ == "__main__":
    _main()
