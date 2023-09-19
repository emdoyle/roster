from graphlib import CycleError, TopologicalSorter

from roster_api.models.workflow import WorkflowSpec, WorkflowStep


def _get_dependencies_for_step(workflow_step: WorkflowStep) -> set[str]:
    deps = set()
    for dep_name in workflow_step.inputMap.values():
        # TODO: factor workflow variable namespacing into shared utility
        try:
            dep_step_name = dep_name.split(".")[0]
        except IndexError:
            raise ValueError(
                f"Could not parse step dependencies for step: {workflow_step}"
            )
        if dep_step_name == "workflow":
            continue
        deps.add(dep_step_name)
    return deps


def sort_workflow_steps(workflow: WorkflowSpec) -> list[str]:
    workflow_graph = {}
    for step_name, step in workflow.steps.items():
        workflow_graph[step_name] = _get_dependencies_for_step(step)

    sorter = TopologicalSorter(graph=workflow_graph)
    try:
        return list(sorter.static_order())
    except CycleError as e:
        raise ValueError(f"Could not sort workflow steps. Cycle detected! {e.args[1]}")
