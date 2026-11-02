"""Python FMU builder."""

import argparse
import itertools
import logging
import re
import shutil
import sys
import tempfile
import zipfile
from collections.abc import Iterable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import xml.etree.ElementTree as ET

from pythonfmu3.fmi3slave import Fmi3SlaveBase
from pythonfmu3.model_options import Fmi3ModelOptionsCS, Fmi3ModelOptionsME

from pythonfmu3.osutil import get_lib_extension, get_platform

FilePath = str | Path
HERE = Path(__file__).parent

logger = logging.getLogger(__name__)


def get_class_name(file_name: Path) -> str:
    with Path.open(file_name) as file:
        data = file.read()
        found = re.search(r"class (\w+)\(([^)]*\bFmi3Slave(?:Base)?\b[^)]*)\)\s*:", data)
        assert found is not None, "Class name could not be extracted."
        return found.group(1)


def get_model_description(filepath: Path, module_name: str) -> tuple[str, ET.Element]:
    """Extract the FMU model description as XML.

    Args:
        filepath (pathlib.Path) : script file path
        module_name (str) : python module to load

    Returns
    -------
        FMU model name, model description as xml ET.Element
    """
    # Add current folder to handle local dependencies
    sys.path.insert(0, str(filepath.parent))
    try:
        # Import the user interface
        spec = spec_from_file_location(module_name, filepath)
        assert spec is not None, f"Spec could not be imported from module {module_name}, path {filepath}"
        fmu_interface = module_from_spec(spec)
        assert fmu_interface is not None, f"Intrface could not be imported from spec {spec}"
        assert spec.loader is not None, f"No loader for spec {spec} found."
        spec.loader.exec_module(fmu_interface)
        # Instantiate the interface
        class_name = get_class_name(filepath)
        instance = getattr(fmu_interface, class_name)(instanceName="dummyInstance", resources=str(filepath.parent))
        model_options_cs = instance.model_options_cs.to_dict()
    finally:
        sys.path.remove(str(filepath.parent))  # remove inserted temporary path

    if not isinstance(instance, Fmi3SlaveBase):
        raise TypeError(f"The provided class '{class_name}' does not inherit from {Fmi3SlaveBase.__qualname__}")
    # Produce the xml
    _xml : ET.Element = instance.to_xml(model_options_cs)
    assert instance.modelName is not None, "Need an instance and modelName at this point"
    return (instance.modelName, _xml)


class FmuBuilder:
    @staticmethod
    def build_FMU( # noqa: PLR0915, PLR0912, C901 ## should be simplified!
        script_file: FilePath,
        dest: FilePath = ".",
        project_files: Iterable[FilePath] = set(),
        documentation_folder: FilePath | None = None,
        terminals: FilePath | None = None,
        options: dict[str, bool|int|float|None] | None = None,
    ) -> Path:
        _script_file = Path(script_file)
        if not _script_file.exists():
            raise ValueError(f"No such file {_script_file}")
        if not _script_file.suffix.endswith(".py"):
            raise ValueError(f"File {_script_file} must have extension '.py'!")

        _dest = Path(dest)
        if not _dest.exists():
            _dest.mkdir(parents=True)
        _project_files = set(map(Path, project_files))

        if documentation_folder is not None:
            documentation_folder = Path(documentation_folder)
            if not documentation_folder.exists():
                raise ValueError(f"The documentation folder does not exists {documentation_folder!s}")

        if terminals is not None:
            terminals = Path(terminals)
            if not terminals.exists():
                raise ValueError(f"The specified terminalsAndIcons file does not exists {terminals!s}")
            if not terminals.name == "terminalsAndIcons.xml":
                raise ValueError(
                    f"Incorrect terminal name {terminals!s}. Terminal file must be named terminalsAndIcons.xml"
                )

        module_name = _script_file.stem

        with tempfile.TemporaryDirectory(prefix="pythonfmu_") as tempd:
            temp_dir = Path(tempd)
            shutil.copy2(_script_file, temp_dir)

            # Embed pythonfmu in the FMU so it does not need to be included
            dep_folder = temp_dir / "pythonfmu3"
            dep_folder.mkdir()
            for dep in HERE.glob("*.py"):  # Find all python files at the same level as this one
                shutil.copy2(dep, dep_folder)
            for file_ in _project_files:
                if file_ == _script_file.parent:
                    new_folder = temp_dir / file_.name
                    new_folder.mkdir()
                    for f in file_.iterdir():
                        if f.is_dir():
                            temp_dest = new_folder / f.name
                            shutil.copytree(f, temp_dest)
                        elif f.name != _script_file.name:
                            shutil.copy2(f, new_folder)
                        else:
                            logger.debug("Skip file with the same name as the script found in project file.")
                elif file_.is_dir():
                    temp_dest = temp_dir / file_.name
                    shutil.copytree(file_, temp_dest)
                else:
                    shutil.copy2(file_, temp_dir)

            model_identifier, xml = get_model_description(temp_dir.absolute() / _script_file.name, module_name)

            dest_file = _dest / f"{model_identifier}.fmu"

            type_node = xml.find("CoSimulation")
            cs_option_names = list(Fmi3ModelOptionsCS().to_dict().keys())
            if type_node is not None and options is not None:
                for option, value in options.items():
                    if option in cs_option_names:
                        type_node.set(option, str(value).lower())

            type_node = xml.find("ModelExchange")
            me_option_names = list(Fmi3ModelOptionsME().to_dict().keys())
            if type_node is not None and options is not None:
                for option, value in options.items():
                    if option in me_option_names:
                        type_node.set(option, str(value).lower())

            with zipfile.ZipFile(dest_file, "w") as zip_fmu:
                resource = Path("resources")

                # Add files copied in temporary directory
                for f in temp_dir.rglob("*"):
                    if f.is_file() and f.parent.name != "__pycache__":
                        relative_f = f.relative_to(temp_dir)
                        zip_fmu.write(f, arcname=(resource / relative_f))

                # Add information for the Python loader
                zip_fmu.writestr(str(resource.joinpath("slavemodule.txt")), module_name)

                # Add FMI API wrapping Python class source
                sources = Path("sources")
                src = HERE / "pythonfmu-export"
                for f in itertools.chain(src.rglob("*.hpp"), src.rglob("*.cpp"), src.rglob("CMakeLists.txt")):
                    relative_f = f.relative_to(src)
                    if "build" in relative_f.parts:
                        continue
                    zip_fmu.write(f, arcname=(sources / relative_f))

                # Add FMI API wrapping Python class library
                binaries = Path("binaries")
                src_binaries = HERE / "resources" / "binaries"
                for f in itertools.chain(
                    src_binaries.rglob("*.dll"),
                    src_binaries.rglob("*.so"),
                    src_binaries.rglob("*.dylib"),
                ):
                    relative_f = f.relative_to(src_binaries)
                    arcname = binaries / relative_f.parent / f"{model_identifier}{relative_f.suffix}"
                    zip_fmu.write(f, arcname=arcname)

                # Add the documentation folder
                if documentation_folder is not None:
                    documentation = Path("documentation")
                    for f in documentation_folder.rglob("*"):
                        if f.is_file():
                            relative_f = f.relative_to(documentation_folder)
                            zip_fmu.write(f, arcname=(documentation / relative_f))

                if terminals is not None:
                    terminals_folder = Path("terminalsAndIcons")
                    relative_f = terminals.relative_to(terminals.parent)
                    zip_fmu.write(f, arcname=(terminals_folder / relative_f))

                # Add the model description
                tree = ET.ElementTree(xml)
                ET.indent(tree, space="  ", level=0)
                #res = tree.write(zip_fmu, encoding='utf-8', xml_declaration=True)
                #print("RES", res)
#                 with Path.open(temp_dir /"modelDescription.xml", 'wb') as f:
#                     tree.write(f, encoding='utf-8')
#                     num = zip_fmu.write(f)
#                     assert num>0
                with zip_fmu.open("modelDescription.xml", 'w') as f:
                    tree.write( f, encoding='utf-8', xml_declaration=True)
            return dest_file

    @staticmethod
    def has_binary() -> bool:
        """Check the existence of the binary for this platform."""
        binary_folder = get_platform()
        lib_ext = get_lib_extension() or "*"  # if library extension is unknown, it will look for '*.*' in src_binaries
        src_binaries = HERE / "resources" / "binaries" / binary_folder
        return src_binaries.exists() and len(list(src_binaries.glob(f"*.{lib_ext}"))) >= 1


def create_command_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-f",
        "--file",
        dest="script_file",
        help="Path to the Python script.",
        required=True,
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

    parser.set_defaults(execute=FmuBuilder.build_FMU)
