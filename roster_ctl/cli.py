import cmd

from agents import Agent


class AgentManagerCLI(cmd.Cmd):
    prompt = "roster-ctl> "

    def __init__(self):
        super().__init__()
        self.agents = {}

    def do_add_agent(self, line):
        args = line.split()
        if len(args) != 1:
            print("Usage: add_agent agent_name")
            return
        agent_name = args[0]
        self.agents[agent_name] = Agent(agent_name)
        print(f"Agent '{agent_name}' added.")

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
