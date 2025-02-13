from autogenstudio import AutoGenWorkflowConfig

roboco_workflow = AutoGenWorkflowConfig(
    name="RoboCo Agent Orchestration",
    roles={
        "Chief Robotics Officer": {
            "description": "Oversees strategic robot deployment",
            "llm_config": {"model": "gpt-4o", "temperature": 0.3}
        },
        "Robotics Engineer": {
            "description": "Designs and tests robot components",
            "llm_config": {"model": "gpt-4o", "temperature": 0.5}
        }
    },
    workflows={
        "new_deployment": {
            "initiator": "Chief Robotics Officer",
            "participants": ["Robotics Engineer"],
            "max_turns": 8
        }
    }
)
