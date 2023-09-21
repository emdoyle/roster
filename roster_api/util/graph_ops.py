from graphlib import CycleError, TopologicalSorter


def sort_dependencies(graph: dict[str, set[str]]) -> list[str]:
    sorter = TopologicalSorter(graph=graph)
    try:
        return list(sorter.static_order())
    except CycleError as e:
        raise ValueError(f"Could not sort workflow steps. Cycle detected! {e.args[1]}")
