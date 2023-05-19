import cmd

from resources import Agent
from utils import get_random_name

DEFAULT_AGENT_RESOURCE = Agent.from_yaml("resources/samples/simple_agent.yml")


class RosterCLI(cmd.Cmd):
    prompt = "roster-ctl> "

    def __init__(self):
        super().__init__()
        self.agents: dict[str, Agent] = {}

    def do_add_agent(self, line):
        args = line.split()
        if len(args) < 2:
            print("Usage: add_agent agent_type (agent_name)")
            return
        agent_type = args[0]
        agent_name = args[1] if len(args) == 2 else get_random_name()
        # TODO: schedule Agent on runtime
        self.agents[agent_name] = DEFAULT_AGENT_RESOURCE
        print(f"Agent '{agent_name}' [{self.agents[agent_name].backend}] added.")

    def do_assign_task(self, line):
        args = line.split()
        if len(args) != 2:
            print("Usage: assign_task agent_name task_description")
            return
        agent_name, task_description = args
        if agent_name not in self.agents:
            print(f"Agent '{agent_name}' not found.")
            return
        # TODO: TaskResource
        print(f"Task '{task_description}' assigned to agent '{agent_name}'.")

    def do_quit(self, line):
        return True

    def emptyline(self):
        pass
