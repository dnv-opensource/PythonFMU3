import argparse
import itertools
import platform
import tempfile
import zipfile
from attrs import asdict
from fmpy import read_model_description
from pathlib import Path

import pytest

import pythonfmu3
from pythonfmu3 import builder, deploy
from pythonfmu3.builder import FmuBuilder, get_platform
from pythonfmu3.fmi3slave import Fmi3ModelOptionsCS, Fmi3ModelOptionsME

PROJECT_TEST_CASES = [
    ("dummy.txt",),
    ("dummy.py", "subdir/dummy.txt"),
    ("dummy.py", "subdir/dummy.txt", "subdir/dummy2.txt"),
    ("dummy.py", "subdir/dummy.txt", "subdir2/dummy2.txt"),
]


lib_extension = ({"Darwin": "dylib", "Linux": "so", "Windows": "dll"}).get(
    platform.system(), None
)


def test_zip_content(tmp_path):

    script_name = "pythonslave.py"
    script_file = Path(__file__).parent / "slaves" / script_name
    fmu = FmuBuilder.build_FMU(script_file, dest=tmp_path)
    assert fmu.exists()
    assert zipfile.is_zipfile(fmu)

    with zipfile.ZipFile(fmu) as files:
        names = files.namelist()

        assert "modelDescription.xml" in names
        assert "/".join(("resources", script_name)) in names
        module_file = "/".join(("resources", "slavemodule.txt"))
        assert module_file in names

        nfiles = 20
        if FmuBuilder.has_binary():
            assert (
                "/".join(("binaries", get_platform(), f"PythonSlave.{lib_extension}"))
                in names
            )
        else:
            nfiles -= 1

        # Check sources
        src_folder = Path(pythonfmu3.__path__[0]) / "pythonfmu-export"
        for f in itertools.chain(
            src_folder.rglob("*.hpp"),
            src_folder.rglob("*.cpp"),
            src_folder.rglob("CMakeLists.txt"),
        ):
            if "build" in f.parts:
                continue
            assert "/".join(("sources", f.relative_to(src_folder).as_posix())) in names

        # Check pythonfmu is embedded
        pkg_folder = Path(pythonfmu3.__path__[0])
        for f in pkg_folder.rglob("*.py"):
            relative_f = f.relative_to(pkg_folder).as_posix()
            if "test" not in relative_f:
                assert "/".join(("resources", "pythonfmu3", relative_f)) in names

        assert (
            len(names) >= nfiles
        )  # Library + python script + XML + module name + sources

        with files.open(module_file) as myfile:
            assert myfile.read() == b"pythonslave"


@pytest.mark.parametrize("pfiles", PROJECT_TEST_CASES)
def test_project_files(tmp_path, pfiles):
    pfiles = map(Path, pfiles)
    script_file = Path(__file__).parent / "slaves/pythonslave.py"

    def build():
        with tempfile.TemporaryDirectory() as project_dir:
            project_dir = Path(project_dir)

            project_files = set()
            for f in pfiles:
                full_name = project_dir / f
                if full_name.suffix:
                    full_name.parent.mkdir(parents=True, exist_ok=True)
                    full_name.write_text("dummy content")
                else:
                    full_name.mkdir(parents=True, exist_ok=True)

                # Add subfolder and not file if common parent exits
                to_remove = None
                for p in project_files:
                    if p.parent == full_name.parent or p == full_name.parent:
                        to_remove = p
                        break
                if to_remove is None:
                    project_files.add(full_name)
                else:
                    project_files.remove(to_remove)
                    project_files.add(full_name.parent)

            return FmuBuilder.build_FMU(
                script_file, dest=tmp_path, project_files=project_files
            )

    fmu = build()
    with zipfile.ZipFile(fmu) as files:
        names = files.namelist()

        parents = [p.parent for p in pfiles]
        unique_folders = set(parents)
        common_parents = set()
        if len(unique_folders) < len(parents):
            common_parents = set(filter(lambda f: parents.count(f) > 1, unique_folders))

            pfiles = map(lambda f: f if f.parent in common_parents else f.name, pfiles)

        for pfile in pfiles:
            assert f"resources/{pfile!s}" in names


@pytest.mark.parametrize("pfiles", PROJECT_TEST_CASES)
def test_project_files_containing_script(tmp_path, pfiles):
    orig_script_file = Path(__file__).parent / "slaves/pythonslave.py"
    pfiles = map(Path, pfiles)

    def build():
        with tempfile.TemporaryDirectory() as project_dir:
            project_dir = Path(project_dir)
            script_file = project_dir / "slave.py"
            with open(orig_script_file) as script_f:
                script_file.write_text(script_f.read())

            for f in pfiles:
                full_name = project_dir / f
                if full_name.suffix:
                    full_name.parent.mkdir(parents=True, exist_ok=True)
                    full_name.write_text("dummy content")
                else:
                    full_name.mkdir(parents=True, exist_ok=True)

            return FmuBuilder.build_FMU(
                script_file, dest=tmp_path, project_files=[script_file.parent]
            )

    fmu = build()
    with zipfile.ZipFile(fmu) as files:
        names = files.namelist()

        parents = [p.parent for p in pfiles]
        unique_folders = set(parents)
        common_parents = set()
        if len(unique_folders) < len(parents):
            common_parents = set(filter(lambda f: parents.count(f) > 1, unique_folders))

            pfiles = map(lambda f: f if f.parent in common_parents else f.name, pfiles)

        for pfile in pfiles:
            assert f"resources/{pfile!s}" in names


def test_documentation(tmp_path):
    script_file = Path(__file__).parent / "slaves/pythonslave.py"

    def build():
        with tempfile.TemporaryDirectory() as documentation_dir:
            doc_dir = Path(documentation_dir)
            license_file = doc_dir / "licenses" / "license.txt"
            license_file.parent.mkdir()
            license_file.write_text("Dummy license")
            index_file = doc_dir / "index.html"
            index_file.write_text("dummy index")
            return FmuBuilder.build_FMU(
                script_file, dest=tmp_path, documentation_folder=doc_dir
            )

    fmu = build()
    with zipfile.ZipFile(fmu) as files:
        names = files.namelist()

        assert "documentation/index.html" in names
        assert "documentation/licenses/license.txt" in names


def test_terminals(tmp_path):
    script_file = Path(__file__).parent / "slaves/pythonslave.py"

    def build():
        with tempfile.TemporaryDirectory() as terminals_dir:
            terminals_dir = Path(terminals_dir)
            terminals = terminals_dir / "terminalsAndIcons.xml"
            terminals.write_text("Dummy Terminal 1")

            return FmuBuilder.build_FMU(script_file, dest=tmp_path, terminals=terminals)

    fmu = build()
    with zipfile.ZipFile(fmu) as files:
        names = files.namelist()
        assert "terminalsAndIcons/terminalsAndIcons.xml" in names

def test_cli():
    def default_execution(**kwargs):
        print("A subcommand must be provided.\n")
        parser.print_help()
        
    parser = argparse.ArgumentParser(prog="pythonfmu")
    parser.add_argument("-V", "--version", action="version", version="9.9.9")

    parser.set_defaults(execute=default_execution)

    subparsers = parser.add_subparsers(
        title="Subcommands",
        description="Call `pythonfmu _command_ -h` to get more help.",
    )

    build_parser = subparsers.add_parser(
        "build",
        description="Build an FMU from a Python script.",
        help="Build an FMU from a Python script.",
    )
    builder.create_command_parser(build_parser)

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
    deploy.create_command_parser(deploy_parser)

    options = vars(parser.parse_args())

    
    py_file = Path(__file__).parent.resolve().parent / "examples/two_state.py"
    #cmd = f" build -f {py_file}"
    #print("CMD", cmd)
    args = parser.parse_args(["build", "-f", str(py_file), "--hasEventMode", "--fixedInternalStepSize", "0.01"])
    assert args.script_file == str(py_file)
    assert not args.needsExecutionTool
    assert args.hasEventMode
    
    assert isinstance(vars(args), dict), "Arguments converted to dict, which is also used in cli"

    dest = builder.FmuBuilder.build_FMU(
        script_file = py_file,
        dest = Path(__file__).parent.resolve() / "test_working_directory",
        #project_files: Iterable[FilePath] = set(),
        #documentation_folder: Optional[FilePath] = None,
        #terminals : Optional[FilePath] = None,
        options = {'hasEventMode':False, 'canHandleVariableCommunicationStepSize':False}
    )
    md = read_model_description(dest, True, True, True)
    dct = asdict(md.coSimulation)
    assert not dct['hasEventMode'], f"'hasEventMode' is {dct['hasEventMode']}!"
    assert not dct['canHandleVariableCommunicationStepSize'], f"{dct['canHandleVariableCommunicationStepSize']}!"
    print(f"Generated {dest}. Validated modelDescription.")

def test_model_options():
    mcs = Fmi3ModelOptionsCS(hasEventMode=True, fixedInternalStepSize=0.01)
    assert mcs.hasEventMode
    assert mcs.fixedInternalStepSize == 0.01
    assert not mcs.providesAdjointDerivatives
    assert not mcs.to_dict()['needsExecutionTool'], "Can access all options as dict"
    mcs = Fmi3ModelOptionsCS(hasEventMode=True)
    assert 'fixedInternalStepSize' not in mcs.to_dict(w_none=False), "Not listed because it is None"
    assert 'needsExecutionTool' in mcs.to_dict(), "Listed even if default value"
    assert 'needsExecutionTool' not in mcs.to_dict(w_default=False), "Not listed because default value"
    

if __name__ == "__main__":
    """Possibility to run single or all tests from the IDE."""
    retcode = 0#pytest.main(["-rA", "-v", "--rootdir", "../", "--show", "True", __file__])
    assert retcode == 0, f"Non-zero return code {retcode}"
    test_cli()
    #test_model_options()
