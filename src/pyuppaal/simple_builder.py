"""High-level builder API for constructing UPPAAL models without manual IDs/positions."""

from __future__ import annotations

import keyword
from typing import Dict, List, Optional, Tuple

from .nta import Edge, Location, Template
from .umodel import UModel


_RESERVED_TEMPLATE_NAMES = frozenset({"decl", "sys_decl", "queries", "__pycache__", "templates"})


class _IdAllocator:
    def next_id(self) -> int:
        raise NotImplementedError


class _SequentialIdAllocator(_IdAllocator):
    def __init__(self, start_id: int) -> None:
        if not isinstance(start_id, int):
            raise TypeError("start_id must be int")
        self._next_id = start_id

    def next_id(self) -> int:
        res = self._next_id
        self._next_id += 1
        return res


class _PosPlacer:
    def pos_for(
        self,
        *,
        template_index: int,
        location_index: int,
        explicit_pos: Optional[Tuple[int, int]],
    ) -> Tuple[int, int]:
        raise NotImplementedError


class _GridPosPlacer(_PosPlacer):
    def __init__(
        self,
        *,
        grid_step: Tuple[int, int],
        row_len: int,
        template_offset: Tuple[int, int],
        origin: Tuple[int, int],
    ) -> None:
        if row_len <= 0:
            raise ValueError("row_len must be positive")
        self._grid_step = grid_step
        self._row_len = row_len
        self._template_offset = template_offset
        self._origin = origin

    def pos_for(
        self,
        *,
        template_index: int,
        location_index: int,
        explicit_pos: Optional[Tuple[int, int]],
    ) -> Tuple[int, int]:
        if explicit_pos is not None:
            return explicit_pos

        base_x = self._origin[0] + template_index * self._template_offset[0]
        base_y = self._origin[1] + template_index * self._template_offset[1]
        row = location_index // self._row_len
        col = location_index % self._row_len
        x = base_x + col * self._grid_step[0]
        y = base_y + row * self._grid_step[1]
        return (x, y)


class ModelBuilder:
    """High-level builder for creating templates without manual IDs/positions."""

    def __init__(
        self,
        *,
        start_id: int = 1,
        id_strategy: str = "sequential",
        pos_strategy: str = "grid",
        grid_step: Tuple[int, int] = (200, 150),
        row_len: int = 6,
        template_offset: Tuple[int, int] = (1200, 0),
        origin: Tuple[int, int] = (0, 0),
    ) -> None:
        if id_strategy != "sequential":
            raise ValueError(f"Unsupported id_strategy: {id_strategy}")
        if pos_strategy != "grid":
            raise ValueError(f"Unsupported pos_strategy: {pos_strategy}")

        self._id_allocator = _SequentialIdAllocator(start_id)
        self._pos_placer = _GridPosPlacer(
            grid_step=grid_step,
            row_len=row_len,
            template_offset=template_offset,
            origin=origin,
        )
        self._templates: List[TemplateBuilder] = []
        self._template_names = set()

    def template(
        self,
        name: str,
        *,
        params: Optional[str] = None,
        declaration: Optional[str] = None,
    ) -> "TemplateBuilder":
        if not isinstance(name, str) or not name:
            raise ValueError("template name must be a non-empty string")
        if not name.isidentifier():
            raise ValueError(f"Template name '{name}' is not a valid Python identifier")
        if keyword.iskeyword(name):
            raise ValueError(f"Template name '{name}' is a Python keyword")
        if name.lower() in _RESERVED_TEMPLATE_NAMES:
            raise ValueError(f"Template name '{name}' is reserved")
        if name in self._template_names:
            raise ValueError(f"Duplicate template name: '{name}'")

        template_index = len(self._templates)
        builder = TemplateBuilder(
            model_builder=self,
            name=name,
            params=params,
            declaration=declaration,
            template_index=template_index,
        )
        self._templates.append(builder)
        self._template_names.add(name)
        return builder

    def build_templates(self) -> List[Template]:
        return [tmpl.to_template() for tmpl in self._templates]

    def build_umodel(
        self,
        *,
        declaration: str = "",
        system: str = "",
        queries: Optional[List[str]] = None,
        model_path: Optional[str] = None,
    ) -> UModel:
        if queries is None:
            queries = []
        templates = self.build_templates()
        return UModel.from_components(
            declaration=declaration,
            templates=templates,
            system=system,
            queries=queries,
            model_path=model_path,
        )


class TemplateBuilder:
    """Builder for a single template."""

    def __init__(
        self,
        *,
        model_builder: ModelBuilder,
        name: str,
        params: Optional[str],
        declaration: Optional[str],
        template_index: int,
    ) -> None:
        self._model_builder = model_builder
        self.name = name
        self._params = params
        self._declaration = declaration
        self._template_index = template_index
        self._locations: List[Location] = []
        self._locations_by_name: Dict[str, Location] = {}
        self._edges: List[Edge] = []
        self._initial_name: Optional[str] = None

    def location(
        self,
        name: str,
        *,
        initial: bool = False,
        urgent: bool = False,
        committed: bool = False,
        branchpoint: bool = False,
        pos: Optional[Tuple[int, int]] = None,
        invariant: Optional[str] = None,
        rate_of_exponential: Optional[float] = None,
        comments: Optional[str] = None,
        test_code_on_enter: Optional[str] = None,
        test_code_on_exit: Optional[str] = None,
    ) -> str:
        if not isinstance(name, str) or not name:
            raise ValueError("location name must be a non-empty string")
        if name in self._locations_by_name:
            raise ValueError(f"Duplicate location name: '{name}'")

        if initial:
            if self._initial_name is not None and self._initial_name != name:
                raise ValueError("Only one initial location is allowed per template")
            self._initial_name = name

        location_id = self._model_builder._id_allocator.next_id()
        location_index = len(self._locations)
        location_pos = self._model_builder._pos_placer.pos_for(
            template_index=self._template_index,
            location_index=location_index,
            explicit_pos=pos,
        )

        loc = Location(
            location_id=location_id,
            location_pos=location_pos,
            name=name,
            invariant=invariant,
            rate_of_exponential=rate_of_exponential,
            is_initial=initial,
            is_urgent=urgent,
            is_committed=committed,
            is_branchpoint=branchpoint,
            comments=comments,
            test_code_on_enter=test_code_on_enter,
            test_code_on_exit=test_code_on_exit,
        )
        self._locations.append(loc)
        self._locations_by_name[name] = loc
        return name

    def set_initial(self, name: str) -> None:
        if name not in self._locations_by_name:
            raise ValueError(f"Unknown location name: '{name}'")
        if self._initial_name is not None and self._initial_name != name:
            raise ValueError("Only one initial location is allowed per template")
        self._initial_name = name

    def edge(
        self,
        source: str,
        target: str,
        *,
        select: Optional[str] = None,
        sync: Optional[str] = None,
        update: Optional[str] = None,
        guard: Optional[str] = None,
        probability_weight: Optional[float] = None,
        comments: Optional[str] = None,
        test_code: Optional[str] = None,
        nails: Optional[List[Tuple[int, int]]] = None,
        source_pos: Optional[Tuple[int, int]] = None,
        target_pos: Optional[Tuple[int, int]] = None,
    ) -> None:
        if source not in self._locations_by_name:
            raise ValueError(f"Unknown source location: '{source}'")
        if target not in self._locations_by_name:
            raise ValueError(f"Unknown target location: '{target}'")

        source_loc = self._locations_by_name[source]
        target_loc = self._locations_by_name[target]
        if source_pos is None:
            source_pos = source_loc.location_pos
        if target_pos is None:
            target_pos = target_loc.location_pos

        edge = Edge(
            source_location_id=source_loc.location_id,
            target_location_id=target_loc.location_id,
            source_location_pos=source_pos,
            target_location_pos=target_pos,
            select=select,
            sync=sync,
            update=update,
            guard=guard,
            probability_weight=probability_weight,
            comments=comments,
            test_code=test_code,
            nails=list(nails) if nails else [],
        )
        self._edges.append(edge)

    def to_template(self) -> Template:
        if self._initial_name is None:
            raise ValueError(
                f"Template '{self.name}' must have exactly one initial location"
            )
        init_ref = self._locations_by_name[self._initial_name].location_id
        return Template(
            name=self.name,
            locations=self._locations,
            init_ref=init_ref,
            edges=self._edges,
            params=self._params,
            declaration=self._declaration,
        )
