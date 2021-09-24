import asyncio

from camundactl.cmd.base import root


async def _main():
    root()


if __name__ == "__main__":
    asyncio.run(root())
