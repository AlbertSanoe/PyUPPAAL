"""
PyImporter: Import UModel from pyfmt directory structure.

Supports two modes:
- machine (default, safe): Parse manifest TOML + JSON payloads without executing any code
- human (trusted only): Execute Python code from registry.py
"""

import os
import sys
import keyword
import json
from typing import List, Tuple, Optional, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from .umodel import UModel

# TOML parsing (for manifest.toml)
import tomlkit

from .nta import Location, Edge, Template


# Reserved directory names that cannot be used as template names
RESERVED_DIRS = frozenset({'decl', 'sys_decl', 'queries', '__pycache__'})

# Format constants
EXPECTED_FORMAT = "pyuppaal-pyfmt"
SUPPORTED_VERSIONS = {2}


class PyImporter:
    """Import UModel from pyfmt directory structure."""

    @staticmethod
    def import_dir(
        input_dir: str,
        *,
        mode: Literal["auto", "machine", "human"] = "auto",
        trusted: bool = False,
        output_xml_path: Optional[str] = None,
        indent: int = 4,
        overwrite: bool = False
    ) -> "UModel":
        """
        Import a UModel from a pyfmt directory.

        Args:
            input_dir: Path to the pyfmt directory
            mode: Import mode - "auto", "machine", or "human"
            trusted: Allow execution of Python code (required for human mode)
            output_xml_path: Optional path to write XML file
            indent: XML indentation (default 4)
            overwrite: Whether to overwrite existing XML file

        Returns:
            UModel instance

        Raises:
            ValueError: Format mismatch, validation failure, or trust violation
            FileNotFoundError: Required files missing
        """
        input_dir = os.path.abspath(input_dir)

        if not os.path.isdir(input_dir):
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        # Detect or validate mode
        detected_mode = PyImporter._detect_mode(input_dir)

        if mode == "auto":
            mode = detected_mode
        elif mode != detected_mode:
            raise ValueError(
                f"Requested mode '{mode}' but directory appears to be '{detected_mode}' format"
            )

        # Security check for human mode
        if mode == "human" and not trusted:
            raise ValueError(
                "Human mode requires trusted=True. "
                "Human import executes Python code from the input directory. "
                "Use mode='machine' for safe import, or set trusted=True if you trust the source."
            )

        # Load components based on mode
        if mode == "machine":
            declaration, system, queries, templates = PyImporter._load_machine_mode(input_dir)
        else:  # human
            declaration, system, queries, templates = PyImporter._load_human_mode(input_dir)

        # Validate components
        PyImporter._validate_components(declaration, system, queries, templates)

        # Build UModel
        from .umodel import UModel
        umodel = UModel.from_components(
            declaration=declaration,
            templates=templates,
            system=system,
            queries=queries,
            model_path=output_xml_path
        )

        # Write XML if requested
        if output_xml_path:
            if os.path.exists(output_xml_path) and not overwrite:
                raise FileExistsError(
                    f"Output file already exists: {output_xml_path}. "
                    "Set overwrite=True to overwrite."
                )
            umodel.save_as(output_xml_path, indent=indent)

        return umodel

    @staticmethod
    def _detect_mode(input_dir: str) -> Literal["machine", "human"]:
        """Detect import mode based on directory contents."""
        manifest_path = os.path.join(input_dir, "manifest.toml")
        registry_path = os.path.join(input_dir, "registry.py")

        if os.path.isfile(manifest_path):
            return "machine"
        elif os.path.isfile(registry_path):
            return "human"
        else:
            raise ValueError(
                f"Cannot detect format: neither manifest.toml nor registry.py found in {input_dir}"
            )

    # ========== Machine Mode Loading ==========

    @staticmethod
    def _load_machine_mode(input_dir: str) -> Tuple[str, str, List[str], List[Template]]:
        """Load components from machine mode directory."""
        manifest_path = os.path.join(input_dir, "manifest.toml")
        manifest = PyImporter._load_manifest(manifest_path)

        # Load global declaration
        decl_path = os.path.join(input_dir, manifest["paths"]["decl"])
        declaration = PyImporter._load_decl_json(decl_path)

        # Load system declaration
        sys_decl_path = os.path.join(input_dir, manifest["paths"]["sys_decl"])
        system = PyImporter._load_sys_decl_json(sys_decl_path)

        # Load queries
        queries_path = os.path.join(input_dir, manifest["paths"]["queries"])
        queries = PyImporter._load_queries_json(queries_path)

        # Load templates
        templates = []
        for tmpl_info in manifest["templates"]:
            tmpl_path = os.path.join(input_dir, tmpl_info["path"])
            template = PyImporter._load_template_json(tmpl_path, tmpl_info["name"])
            templates.append(template)

        return declaration, system, queries, templates

    @staticmethod
    def _load_manifest(manifest_path: str) -> dict:
        """Load and validate manifest.toml."""
        if not os.path.isfile(manifest_path):
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = tomlkit.load(f)

        # Validate format
        fmt = manifest.get("format")
        if fmt != EXPECTED_FORMAT:
            raise ValueError(
                f"Invalid format in manifest: expected '{EXPECTED_FORMAT}', got '{fmt}'"
            )

        # Validate version
        version = manifest.get("format_version")
        if version not in SUPPORTED_VERSIONS:
            raise ValueError(
                f"Unsupported format version: {version}. Supported: {SUPPORTED_VERSIONS}"
            )

        # Validate required paths
        paths = manifest.get("paths", {})
        for key in ("decl", "sys_decl", "queries"):
            if key not in paths:
                raise ValueError(f"Missing required path in manifest: paths.{key}")

        # Validate templates list
        if "templates" not in manifest or not manifest["templates"]:
            raise ValueError("Manifest must contain at least one template")

        return manifest

    @staticmethod
    def _load_decl_json(decl_path: str) -> str:
        """Load global declaration from JSON file."""
        if not os.path.isfile(decl_path):
            raise FileNotFoundError(f"Declaration file not found: {decl_path}")

        with open(decl_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("declaration", "")

    @staticmethod
    def _load_sys_decl_json(sys_decl_path: str) -> str:
        """Load system declaration from JSON file."""
        if not os.path.isfile(sys_decl_path):
            raise FileNotFoundError(f"System declaration file not found: {sys_decl_path}")

        with open(sys_decl_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("system", "")

    @staticmethod
    def _load_queries_json(queries_path: str) -> List[str]:
        """Load queries from JSON file."""
        if not os.path.isfile(queries_path):
            raise FileNotFoundError(f"Queries file not found: {queries_path}")

        with open(queries_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("queries", [])

    @staticmethod
    def _load_template_json(template_path: str, expected_name: str) -> Template:
        """Load a template from JSON file."""
        if not os.path.isfile(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate name matches
        name = data.get("name")
        if name != expected_name:
            raise ValueError(
                f"Template name mismatch: manifest says '{expected_name}', "
                f"file contains '{name}'"
            )

        # Required fields
        init_ref = data.get("init_ref")
        if init_ref is None:
            raise ValueError(f"Template '{name}' missing required field: init_ref")

        # Optional fields
        params = data.get("params")
        local_decl = data.get("local_decl")

        # Parse locations
        locations_data = data.get("locations", [])
        locations = PyImporter._parse_locations(locations_data, name)

        # Validate init_ref exists in locations
        location_ids = {loc.location_id for loc in locations}
        if init_ref not in location_ids:
            raise ValueError(
                f"Template '{name}': init_ref={init_ref} not found in locations. "
                f"Available IDs: {sorted(location_ids)}"
            )

        # Parse edges
        edges_data = data.get("edges", [])
        edges = PyImporter._parse_edges(edges_data, locations, name)

        return Template(
            name=name,
            locations=locations,
            init_ref=init_ref,
            edges=edges,
            params=params,
            declaration=local_decl
        )

    @staticmethod
    def _parse_locations(locations_data: List[dict], template_name: str) -> List[Location]:
        """Parse locations from TOML data."""
        locations = []
        seen_ids = set()

        for i, loc_data in enumerate(locations_data):
            # Required fields
            loc_id = loc_data.get("id")
            if loc_id is None:
                raise ValueError(
                    f"Template '{template_name}': location[{i}] missing required field: id"
                )

            # Check for duplicate IDs
            if loc_id in seen_ids:
                raise ValueError(
                    f"Template '{template_name}': duplicate location id={loc_id}"
                )
            seen_ids.add(loc_id)

            pos = loc_data.get("pos")
            if pos is None or len(pos) != 2:
                raise ValueError(
                    f"Template '{template_name}': location[{i}] missing or invalid pos"
                )

            # Optional fields
            name = loc_data.get("name")
            name_pos = loc_data.get("name_pos")
            if name_pos:
                name_pos = tuple(name_pos)

            invariant = loc_data.get("invariant")
            invariant_pos = loc_data.get("invariant_pos")
            if invariant_pos:
                invariant_pos = tuple(invariant_pos)

            rate_of_exp = loc_data.get("rate_of_exponential")
            rate_of_exp_pos = loc_data.get("rate_of_exp_pos")
            if rate_of_exp_pos:
                rate_of_exp_pos = tuple(rate_of_exp_pos)

            is_initial = loc_data.get("is_initial", False)
            is_urgent = loc_data.get("urgent", False)
            is_committed = loc_data.get("committed", False)
            is_branchpoint = loc_data.get("branchpoint", False)

            comments = loc_data.get("comments")
            comments_pos = loc_data.get("comments_pos")
            if comments_pos:
                comments_pos = tuple(comments_pos)

            test_code_on_enter = loc_data.get("test_code_on_enter")
            test_code_on_exit = loc_data.get("test_code_on_exit")

            location = Location(
                location_id=loc_id,
                location_pos=tuple(pos),
                name=name,
                name_pos=name_pos,
                invariant=invariant,
                invariant_pos=invariant_pos,
                rate_of_exponential=rate_of_exp,
                rate_of_exp_pos=rate_of_exp_pos,
                is_initial=is_initial,
                is_urgent=is_urgent,
                is_committed=is_committed,
                is_branchpoint=is_branchpoint,
                comments=comments,
                comments_pos=comments_pos,
                test_code_on_enter=test_code_on_enter,
                test_code_on_exit=test_code_on_exit
            )
            locations.append(location)

        return locations

    @staticmethod
    def _parse_edges(
        edges_data: List[dict],
        locations: List[Location],
        template_name: str
    ) -> List[Edge]:
        """Parse edges from TOML data."""
        # Build location lookup
        loc_map = {loc.location_id: loc for loc in locations}
        edges = []

        for i, edge_data in enumerate(edges_data):
            # Required fields
            source_id = edge_data.get("source_id")
            target_id = edge_data.get("target_id")

            if source_id is None:
                raise ValueError(
                    f"Template '{template_name}': edge[{i}] missing source_id"
                )
            if target_id is None:
                raise ValueError(
                    f"Template '{template_name}': edge[{i}] missing target_id"
                )

            # Validate source/target exist
            if source_id not in loc_map:
                raise ValueError(
                    f"Template '{template_name}': edge[{i}] source_id={source_id} "
                    f"not found in locations"
                )
            if target_id not in loc_map:
                raise ValueError(
                    f"Template '{template_name}': edge[{i}] target_id={target_id} "
                    f"not found in locations"
                )

            # Get positions (use location pos as default)
            source_pos = edge_data.get("source_pos")
            if source_pos:
                source_pos = tuple(source_pos)
            else:
                source_pos = loc_map[source_id].location_pos

            target_pos = edge_data.get("target_pos")
            if target_pos:
                target_pos = tuple(target_pos)
            else:
                target_pos = loc_map[target_id].location_pos

            # Optional label fields
            select = edge_data.get("select")
            select_pos = edge_data.get("select_pos")
            if select_pos:
                select_pos = tuple(select_pos)

            sync = edge_data.get("sync")
            sync_pos = edge_data.get("sync_pos")
            if sync_pos:
                sync_pos = tuple(sync_pos)

            update = edge_data.get("update")
            update_pos = edge_data.get("update_pos")
            if update_pos:
                update_pos = tuple(update_pos)

            guard = edge_data.get("guard")
            guard_pos = edge_data.get("guard_pos")
            if guard_pos:
                guard_pos = tuple(guard_pos)

            prob_weight = edge_data.get("probability_weight")
            prob_weight_pos = edge_data.get("prob_weight_pos")
            if prob_weight_pos:
                prob_weight_pos = tuple(prob_weight_pos)

            comments = edge_data.get("comments")
            comments_pos = edge_data.get("comments_pos")
            if comments_pos:
                comments_pos = tuple(comments_pos)

            test_code = edge_data.get("test_code")

            # Nails
            nails_data = edge_data.get("nails", [])
            nails = [tuple(n) for n in nails_data]

            edge = Edge(
                source_location_id=source_id,
                target_location_id=target_id,
                source_location_pos=source_pos,
                target_location_pos=target_pos,
                select=select,
                select_pos=select_pos,
                sync=sync,
                sync_pos=sync_pos,
                update=update,
                update_pos=update_pos,
                guard=guard,
                guard_pos=guard_pos,
                probability_weight=prob_weight,
                prob_weight_pos=prob_weight_pos,
                comments=comments,
                comments_pos=comments_pos,
                test_code=test_code,
                nails=nails
            )
            edges.append(edge)

        return edges

    # ========== Human Mode Loading ==========

    @staticmethod
    def _load_human_mode(input_dir: str) -> Tuple[str, str, List[str], List[Template]]:
        """
        Load components from human mode directory (trusted).

        WARNING: This executes Python code from the input directory.
        Only use with trusted sources.
        """
        import importlib.util
        import uuid

        registry_path = os.path.join(input_dir, "registry.py")
        if not os.path.isfile(registry_path):
            raise FileNotFoundError(f"Registry file not found: {registry_path}")

        # Generate unique module name to avoid conflicts
        module_name = f"_pyuppaal_import_{uuid.uuid4().hex[:8]}"

        # Add input_dir to sys.path temporarily for relative imports
        parent_dir = os.path.dirname(input_dir)
        pkg_name = os.path.basename(input_dir)

        # Create a temporary package structure
        old_path = sys.path.copy()
        try:
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)

            # Load registry module
            spec = importlib.util.spec_from_file_location(
                f"{pkg_name}.registry",
                registry_path,
                submodule_search_locations=[input_dir]
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load registry from {registry_path}")

            registry = importlib.util.module_from_spec(spec)
            sys.modules[f"{pkg_name}.registry"] = registry
            spec.loader.exec_module(registry)

            # Extract data from registry
            templates = PyImporter._get_registry_attr(registry, "ALL_TEMPLATES", list)
            declaration = PyImporter._get_registry_func(registry, "load_global_declaration")
            system = PyImporter._get_registry_func(registry, "load_system_declaration")
            queries = PyImporter._get_registry_func(registry, "load_queries")

        except Exception as e:
            raise ImportError(
                f"Failed to load human mode registry: {e}\n"
                f"Ensure registry.py exports ALL_TEMPLATES, load_global_declaration(), "
                f"load_system_declaration(), and load_queries()"
            ) from e
        finally:
            sys.path = old_path
            # Clean up sys.modules
            to_remove = [k for k in sys.modules if k.startswith(f"{pkg_name}.")]
            for k in to_remove:
                del sys.modules[k]

        return declaration, system, queries, templates

    @staticmethod
    def _get_registry_attr(registry, attr_name: str, expected_type: type):
        """Get an attribute from registry module."""
        if not hasattr(registry, attr_name):
            raise ValueError(f"Registry missing required attribute: {attr_name}")
        value = getattr(registry, attr_name)
        if not isinstance(value, expected_type):
            raise ValueError(
                f"Registry.{attr_name} should be {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
        return value

    @staticmethod
    def _get_registry_func(registry, func_name: str):
        """Call a function from registry module."""
        if not hasattr(registry, func_name):
            raise ValueError(f"Registry missing required function: {func_name}")
        func = getattr(registry, func_name)
        if not callable(func):
            raise ValueError(f"Registry.{func_name} should be callable")
        return func()

    # ========== Validation ==========

    @staticmethod
    def _validate_components(
        declaration: str,
        system: str,
        queries: List[str],
        templates: List[Template]
    ) -> None:
        """Validate imported components."""
        # Validate templates
        if not templates:
            raise ValueError("At least one template is required")

        seen_names = set()
        all_location_ids = set()

        for template in templates:
            name = template.name

            # Check name is valid Python identifier
            if not name.isidentifier():
                raise ValueError(
                    f"Template name '{name}' is not a valid Python identifier"
                )

            # Check name is not a keyword
            if keyword.iskeyword(name):
                raise ValueError(
                    f"Template name '{name}' is a Python keyword"
                )

            # Check name is not reserved
            if name.lower() in RESERVED_DIRS:
                raise ValueError(
                    f"Template name '{name}' is reserved"
                )

            # Check for duplicate names
            if name in seen_names:
                raise ValueError(f"Duplicate template name: '{name}'")
            seen_names.add(name)

            # Check location IDs are globally unique
            for loc in template.locations:
                if loc.location_id in all_location_ids:
                    raise ValueError(
                        f"Duplicate location ID {loc.location_id} "
                        f"(found in template '{name}')"
                    )
                all_location_ids.add(loc.location_id)
