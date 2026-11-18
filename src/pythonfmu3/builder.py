"""Python FMU builder."""

import itertools
import logging
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from pythonfmu3.fmi3slave import Fmi3SlaveBase
from pythonfmu3.model_options import Fmi3ModelOptionsCS, Fmi3ModelOptionsME
from pythonfmu3.osutil import get_lib_extension, get_platform

FilePath = str | Path
HERE = Path(__file__).parent

logger = logging.getLogger(__name__)


class FmuBuilder:
    """Build the FMU based on a given script file.

    Args:
        script_file: the path to the script file with the model FMI3Slave
        dest: folder where to put the final .fmu file
        project_files: optional additional project files
        documentation_folder: optional folder with documentation files
        terminals: optional path to terminal file 'terminalsAndIcons.xml'
        options: dict with model options
    """
    def __init__(self,
                 script_file: FilePath,
                 dest: FilePath = ".",
                 project_files: Iterable[FilePath] = set(),
                 documentation_folder: FilePath | None = None,
                 terminals: FilePath | None = None,
                 options: dict[str, bool|int|float|None] | None = None
                 )->None:
        self.script_file = FmuBuilder.ensure_file_path(script_file, ends='.py')
        self.dest = FmuBuilder.ensure_folder(dest, mandatory=True, create=True)
        self.project_files = set(map(Path, project_files))
        self.documentation_folder = FmuBuilder.ensure_folder(documentation_folder, mandatory=False, create=False)
        self.terminals = None if terminals is None else FmuBuilder.ensure_file_path(terminals,
                                                                                    ends="terminalsAndIcons.xml")
        self.options = options


    def build(self) -> Path:
        """Build the FMU according to the settings in the class."""
        with tempfile.TemporaryDirectory(prefix="pythonfmu_") as tempd:
            temp_dir = Path(tempd)
            shutil.copy2(self.script_file, temp_dir)

            self.embed_pythonfmu(temp_dir, "pythonfmu3")

            model_identifier, xml = self.get_model_description(temp_dir.absolute())

            dest_file = self.dest / f"{model_identifier}.fmu"

            _node = self.ensure_model_options(xml.find("CoSimulation"), default = Fmi3ModelOptionsCS())
            _node = self.ensure_model_options(xml.find("ModelExchange"), default = Fmi3ModelOptionsME())

            with zipfile.ZipFile(dest_file, "w") as zip_fmu:
                resource = Path("resources")

                # Add files copied in temporary directory
                for f in temp_dir.rglob("*"):
                    if f.is_file() and f.parent.name != "__pycache__":
                        relative_f = f.relative_to(temp_dir)
                        zip_fmu.write(f, arcname=(resource / relative_f))

                # Add information for the Python loader
                zip_fmu.writestr(str(resource.joinpath("slavemodule.txt")), self.script_file.stem)

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
                if self.documentation_folder is not None:
                    documentation = Path("documentation")
                    for f in self.documentation_folder.rglob("*"):
                        if f.is_file():
                            relative_f = f.relative_to(self.documentation_folder)
                            zip_fmu.write(f, arcname=(documentation / relative_f))

                if self.terminals is not None:
                    terminals_folder = Path("terminalsAndIcons")
                    relative_f = self.terminals.relative_to(self.terminals.parent)
                    zip_fmu.write(f, arcname=(terminals_folder / relative_f))

                # Add the model description
                tree = ET.ElementTree(xml)
                ET.indent(tree, space="  ", level=0)
                with zip_fmu.open("modelDescription.xml", 'w') as f:
                    tree.write( f, encoding='utf-8', xml_declaration=True)
            return dest_file

    def get_model_description(self, temp_dir: Path) -> tuple[str, ET.Element]:
        """Extract the FMU model description as XML.

        Args:
            temp_dir: temporary directory where the script file is found

        Returns:
            FMU model name and model description as xml ET.Element
        """
        filepath = temp_dir / self.script_file.name
        module_name = self.script_file.stem
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
            class_name = FmuBuilder.get_class_name(filepath)
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

    @staticmethod
    def get_class_name(file_name: Path) -> str:
        with Path.open(file_name) as file:
            data = file.read()
            found = re.search(r"class (\w+)\(([^)]*\bFmi3Slave(?:Base)?\b[^)]*)\)\s*:", data)
            assert found is not None, "Class name could not be extracted."
            return found.group(1)


    @staticmethod
    def has_binary() -> bool:
        """Check the existence of the binary for this platform."""
        binary_folder = get_platform()
        lib_ext = get_lib_extension() or "*"  # if library extension is unknown, it will look for '*.*' in src_binaries
        src_binaries = HERE / "resources" / "binaries" / binary_folder
        return src_binaries.exists() and len(list(src_binaries.glob(f"*.{lib_ext}"))) >= 1


    def ensure_model_options(self, node:ET.Element, default : Fmi3ModelOptionsCS|Fmi3ModelOptionsME) -> ET.Element:
        option_names = list(default.to_dict().keys())
        if node is not None and self.options is not None:
            for option, value in self.options.items():
                if option in option_names:
                    node.set(option, str(value).lower())
        return node


    @staticmethod
    def ensure_file_path( file: FilePath, ends: str = '') -> Path:
        """Make sure that the file exists and has the correct suffix (if not empty). Return as Path."""
        _file = Path(file).resolve()
        if not _file.exists():
            raise FileExistsError(f"No such file {_file}")
        if ends and not _file.name.endswith( ends):
            raise ValueError(f"File {_file} must end with '{ends}'!")
        return _file

    @staticmethod
    def ensure_folder( path:FilePath|None, *, mandatory:bool=True, create:bool=False) -> Path|None:
        """Check the folder and return as Path.

        Args:
            path: the path to check. If None and mandatory raise an error
            mandatory: state whether the folder is mandatory
            create: state whether the folder should be created if not existent

        Returns:
            The path as Path object or None
        """
        if path is None:
            if mandatory:
                raise ValueError("Mandatory path not provided.")
            return None
        _path = Path(path).resolve()
        if not _path.exists():
            if create:
                _path.mkdir(parents=True)
            else:
                raise ValueError(f"Path {_path} does not exist.")
        return _path

    def embed_pythonfmu(self, temp_dir:Path, pythonfmu:str)->None:
        """Embed pythonfmu in the FMU so it does not need to be imported.

        Args:
            temp_dir: The path to the main temporary direcory where the zip-file is collected
            pythonfmu: name of the pythonfmu directory added to the temp_dir path
            project_files: original location of the project files (in addition to the script_file)
            script_file: path to the script_file containing the FMU class
        """
        temp_folder = temp_dir / pythonfmu
        temp_folder.mkdir()
        for dep in HERE.glob("*.py"):  # Find all python files at the same level as this one
            shutil.copy2(dep, temp_folder)
        for file_ in self.project_files:
            if file_ == self.script_file.parent:
                new_folder = temp_dir / file_.name
                new_folder.mkdir()
                for f in file_.iterdir():
                    if f.is_dir():
                        temp_dest = new_folder / f.name
                        shutil.copytree(f, temp_dest)
                    elif f.name != self.script_file.name:
                        shutil.copy2(f, new_folder)
                    else:
                        logger.debug("Skip file with the same name as the script found in project file.")
            elif file_.is_dir():
                temp_dest = temp_dir / file_.name
                shutil.copytree(file_, temp_dest)
            else:
                shutil.copy2(file_, temp_dir)

