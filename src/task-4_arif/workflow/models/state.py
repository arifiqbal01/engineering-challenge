
from typing import Literal, TypedDict

from workflow.models.content import ContentItem
from workflow.models.evaluation import EvaluationResult


WorkflowStatus = Literal[
    "pending",
    "evaluating",
    "revising",
    "awaiting_review",
    "completed",
    "retry_limit_reached",
]


class WorkflowState(TypedDict):
    workflow_id: str
    content: ContentItem
    evaluation: EvaluationResult | None
    revision_count: int
    status: WorkflowStatus
