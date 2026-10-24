
from workflow.models import (
    ContentItem,
    WorkflowState,
)


def test_initial_workflow_state():
    content = ContentItem(
        content_id="content-001",
        title="Example article",
        body="Initial content.",
    )

    state: WorkflowState = {
        "workflow_id": "workflow-001",
        "content": content,
        "evaluation": None,
        "revision_count": 0,
        "status": "pending",
    }

    assert state["workflow_id"] == "workflow-001"
    assert state["revision_count"] == 0
    assert state["evaluation"] is None
    assert state["status"] == "pending"


def test_workflow_state_supports_partial_updates():
    update = {
        "revision_count": 1,
        "status": "revising",
    }

    assert update["revision_count"] == 1
    assert update["status"] == "revising"