
import pytest

from workflow.adapters.fake_evaluator import FakeEvaluator
from workflow.adapters.fake_reviser import FakeReviser
from workflow.adapters.sqlite_event_log import SQLiteEventLog
from workflow.graph import build_workflow_graph
from workflow.models import ContentItem, EvaluationDecision
from workflow.models.event import WorkflowEventType
from workflow.persistence.checkpoint import sqlite_checkpointer
from workflow.services import (
    WorkflowConflictError,
    WorkflowNotFoundError,
    WorkflowService,
)


@pytest.fixture
def content():
    return ContentItem(
        content_id="content-001",
        title="Example article",
        body="Initial content.",
    )


@pytest.fixture
def service(tmp_path):
    with sqlite_checkpointer(tmp_path / "checkpoints.db") as saver:
        event_log = SQLiteEventLog(tmp_path / "events.db")

        graph = build_workflow_graph(
            evaluator=FakeEvaluator(
                decisions=[EvaluationDecision.HUMAN_REVIEW]
            ),
            reviser=FakeReviser(),
            event_log=event_log,
            checkpointer=saver,
        )

        yield WorkflowService(
            graph=graph,
            event_log=event_log,
        )


def test_start_creates_workflow(service, content):
    state = service.start(
        workflow_id="workflow-001",
        content=content,
    )

    assert state["workflow_id"] == "workflow-001"
    assert state["evaluation_count"] == 1

    events = service.events("workflow-001")

    assert events[0].event_type == WorkflowEventType.WORKFLOW_STARTED


def test_start_is_idempotent(service, content):
    first = service.start(
        workflow_id="workflow-001",
        content=content,
    )

    second = service.start(
        workflow_id="workflow-001",
        content=content,
    )

    assert first == second

    events = service.events("workflow-001")

    assert sum(
        event.event_type == WorkflowEventType.WORKFLOW_STARTED
        for event in events
    ) == 1


def test_start_rejects_conflicting_content(service, content):
    service.start(
        workflow_id="workflow-001",
        content=content,
    )

    different_content = ContentItem(
        content_id="content-002",
        title="Different article",
        body="Different content.",
    )

    with pytest.raises(WorkflowConflictError):
        service.start(
            workflow_id="workflow-001",
            content=different_content,
        )


def test_status_returns_persisted_state(service, content):
    service.start(
        workflow_id="workflow-001",
        content=content,
    )

    state = service.status("workflow-001")

    assert state["workflow_id"] == "workflow-001"
    assert state["revision_count"] == 0


def test_status_rejects_unknown_workflow(service):
    with pytest.raises(WorkflowNotFoundError):
        service.status("unknown-workflow")


def test_approve_completes_workflow(service, content):
    service.start(
        workflow_id="workflow-001",
        content=content,
    )

    state = service.approve("workflow-001")

    assert state["status"] == "completed"

    event_types = [
        event.event_type
        for event in service.events("workflow-001")
    ]

    assert WorkflowEventType.APPROVAL_RECORDED in event_types
    assert WorkflowEventType.WORKFLOW_COMPLETED in event_types


def test_duplicate_approval_is_idempotent(service, content):
    service.start(
        workflow_id="workflow-001",
        content=content,
    )

    first = service.approve("workflow-001")
    second = service.approve("workflow-001")

    assert first == second

    events = service.events("workflow-001")

    assert sum(
        event.event_type == WorkflowEventType.APPROVAL_RECORDED
        for event in events
    ) == 1

    assert sum(
        event.event_type == WorkflowEventType.WORKFLOW_COMPLETED
        for event in events
    ) == 1


def test_approve_unknown_workflow(service):
    with pytest.raises(WorkflowNotFoundError):
        service.approve("unknown-workflow")


def test_events_unknown_workflow(service):
    with pytest.raises(WorkflowNotFoundError):
        service.events("unknown-workflow")


def test_start_rejects_blank_workflow_id(service, content):
    with pytest.raises(ValueError, match="cannot be blank"):
        service.start(
            workflow_id="   ",
            content=content,
        )
