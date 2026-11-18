import argparse

from pythonfmu3.builder import FmuBuilder
from pythonfmu3.deploy import deploy
from pythonfmu3.model_options import Fmi3ModelOptionsCS, Fmi3ModelOptionsME

from importlib.metadata import version

def parse_build(parser: argparse.ArgumentParser) -> None:
    """Define arguments to build command."""
    parser.add_argument(
#        dest="script_file",
        'script_file',
        metavar = 'script_file',
        help="Path to the Python script.",
    )

    parser.add_argument("-d", "--dest", dest="dest", help="Where to save the FMU.", default=".")

    parser.add_argument(
        "--doc",
        dest="documentation_folder",
        help="Documentation folder to include in the FMU.",
        default=None,
    )

    parser.add_argument(
        "--terminals",
        dest="terminals",
        help="Terminals file (terminalsAndIcons.xml) to include in the FMU.",
        default=None,
    )

    # Boolean options are added using their FMI name, making them implicitly True.
    # For other options their (non-default) number is added after a space.
    for name, default in Fmi3ModelOptionsCS().to_dict().items():
        if default in (True, False):
            parser.add_argument(f"--{name}", dest=name, help=f"If given, {name}={not default}", action="store_true")
        elif name in ("fixedInternalStepSize", "maxOutputDerivativeOrder", "recommendedIntermediateInputSmoothness"):
            parser.add_argument(
                f"--{name}",
                dest=name,
                help=f"If given, {name}= number",
            )
        else:
            raise ValueError(f"Something wrong with option {name}, default:{default}") from None

    cs_keys = list(Fmi3ModelOptionsCS().to_dict().keys())
    for name, default in Fmi3ModelOptionsME().to_dict().items():
        if name not in cs_keys:
            if default in (True, False):
                parser.add_argument(f"--{name}", dest=name, help=f"If given, {name}={not default}", action="store_true")
            else:
                raise ValueError(f"Something wrong with option {name}, default:{default}") from None

    parser.add_argument(
        "project_files",
        metavar="Project files",
        nargs="*",
        help="Additional project files required by the Python script.",
        default=set(),
    )


def parse_deploy(parser: argparse.ArgumentParser):

    parser.add_argument(
        'fmu',
        metavar = 'fmu',
        help="Path to the Python FMU.",
    )

    parser.add_argument(
        "-e",
        "--env",
        dest="environment",
        help="Requirements or environment file.",
        default=None,
    )

    parser.add_argument(
        choices=["pip", "conda"],
        dest="package_manager",
        nargs="?",
        help="Python packages manager",
    )
    

def main():
    parser = argparse.ArgumentParser(prog="pythonfmu")

    parser.add_argument("-V", "--version", action="version", version=version)

    def default_execution(**kwargs):
        print("A subcommand must be provided.\n")
        parser.print_help()

    #parser.set_defaults(execute=default_execution)

    subparsers = parser.add_subparsers(
        title="Subcommands",
        description="Call `pythonfmu _command_ -h` to get more help.",
    )

    build_parser = subparsers.add_parser(
        "build",
        description="Build an FMU from a Python script.",
        help="Build an FMU from a Python script.",
    )
    parse_build(build_parser)

    deploy_parser = subparsers.add_parser(
        "deploy",
        description="""Deploy a Python FMU.

        The command will look in the `resources` folder for one of the following files:
        `requirements.txt` or `environment.yml`.

        If you specify a environment file but no package manager, `conda` will be selected
        for `.yaml` and `.yml` otherwise `pip` will be used.

        The tool assume the Python environment in which the FMU should be executed
        is the current one.
        """,
        help="Install Python FMU dependencies.",
    )
    parse_deploy(deploy_parser)

    _args = vars(parser.parse_args())
    if 'script_file' in _args:
        sf = _args.pop('script_file')
        args = { k:v for k,v in _args.items() if v is not None and (not isinstance(v, bool) or v)} # only non-default
        builder = FmuBuilder(sf, **args)
        builder.build()
    elif 'fmu' in _args:
        fmu = _args.pop('fmu')
        deploy( fmu, **_args)
    else:
        raise ValueError(f"Unknown argument in {_args}") from None


if __name__ == "__main__":
    main()
