import os

from camundactl.cmd.base import init, root


def _main():

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


if __name__ == "__main__":
    _main()
