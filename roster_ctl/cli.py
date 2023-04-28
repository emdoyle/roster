import cmd

from agents import AbstractAgent, OpenAIAgent
from resources import Agent
from utils import get_random_name

KNOWN_AGENTS = {
    "openai": OpenAIAgent,
}

DEFAULT_AGENT_RESOURCE = Agent.from_yaml("resources/samples/simple_agent.yml")


class RosterCLI(cmd.Cmd):
    prompt = "roster-ctl> "

    def __init__(self):
        super().__init__()
        self.agents: dict[str, AbstractAgent] = {}

    def do_add_agent(self, line):
        args = line.split()
        if len(args) != 1:
            print("Usage: add_agent agent_type (agent_name)")
            return
        agent_type = args[0]
        agent_name = args[1] if len(args) == 2 else get_random_name()
        self.agents[agent_name] = KNOWN_AGENTS[agent_type].from_resource(
            DEFAULT_AGENT_RESOURCE
        )
        print(f"Agent '{agent_name}' [{agent_type}] added.")

    def do_assign_task(self, line):
        args = line.split()
        if len(args) != 2:
            print("Usage: assign_task agent_name task_description")
            return
        agent_name, task_description = args
        if agent_name not in self.agents:
            print(f"Agent '{agent_name}' not found.")
            return
        agent = self.agents[agent_name]
        agent.assign_task(task_description)
        print(f"Task '{task_description}' assigned to agent '{agent_name}'.")

    def do_EOF(self, line):
        return True

    def emptyline(self):
        pass
