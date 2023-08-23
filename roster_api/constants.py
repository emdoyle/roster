API_VERSION = "v0.1"
LOGGER_NAME = "roster_api"

EXECUTION_ID_HEADER = "X-Roster-Execution-ID"
EXECUTION_TYPE_HEADER = "X-Roster-Execution-Type"

# TODO: proper namespace support, callsites should prepend 'default' or other
WORKFLOW_ROUTER_QUEUE = "default:actor:roster-admin:workflow-router"
