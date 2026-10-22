"""Hỏi đáp có trích dẫn qua SSE (US-201…203, 301). Điều phối; truy xuất/LLM nằm sau `AnswerPipeline`.

Tách hai pha để lỗi trước khi mở stream (JWT, kill switch, sở hữu tài liệu, rate limit, validate)
trả JSON problem+json thông thường thay vì SSE (API_Design 3.4.3):
  1. `prepare()`  — kiểm tra + LƯU câu hỏi trước khi gọi dịch vụ ngoài (CN-05).
  2. `stream()`   — phát sự kiện, lưu kết quả; ngắt kết nối ⇒ `interrupted`, giữ phần đã nhận.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from docchat_core.application.common import (
    ChatMetrics,
    Clock,
    IdFactory,
    NoMetrics,
    new_id,
    utc_now,
)
from docchat_core.config import AppConfig
from docchat_core.domain import (
    Citation,
    CitationView,
    Conversation,
    DocumentStatus,
    Message,
    MessageStatus,
)
from docchat_core.domain.errors import (
    AnswerFailed,
    DocumentNotReady,
    NoReadyDocuments,
    NotFound,
    QaDisabled,
    QuestionTooLong,
    RequestInProgress,
    ValidationFailed,
)
from docchat_core.ports import (
    AnswerPipeline,
    CitationRef,
    Completed,
    RateLimiter,
    Token,
    UnitOfWorkFactory,
)

logger = logging.getLogger(__name__)

ASK_RATE_BUCKET = "ask"
ASK_RATE_LIMIT = 30  # câu hỏi/phút/người dùng [Đề xuất]
ASK_RATE_WINDOW = 60
CONVERSATION_SCOPE = "conversation_create"
PING_INTERVAL_SECONDS = 15.0


@dataclass(frozen=True)
class SseEvent:
    name: str
    data: dict[str, Any]


@dataclass(frozen=True)
class AskContext:
    user_id: UUID
    question: str
    document_ids: tuple[UUID, ...]
    ai_message: Message
    replay_citations: tuple[CitationView, ...] | None = None  # có ⇒ phát lại câu trả lời đã lưu


class _End:
    pass


_END = _End()


def citation_payload(c: Citation) -> dict[str, Any]:
    return {
        "id": str(c.id),
        "documentId": str(c.document_id) if c.document_id else None,
        "documentName": c.document_name,
        "page": c.page,
        "valid": c.valid,
    }


class ChatService:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        pipeline: AnswerPipeline,
        config: AppConfig,
        rate_limiter: RateLimiter,
        *,
        metrics: ChatMetrics | None = None,
        clock: Clock = utc_now,
        id_factory: IdFactory = new_id,
        ping_interval: float = PING_INTERVAL_SECONDS,
    ) -> None:
        self._uow = uow_factory
        self._pipeline = pipeline
        self._config = config
        self._limiter = rate_limiter
        self._metrics = metrics or NoMetrics()
        self._clock = clock
        self._new_id = id_factory
        self._ping = ping_interval

    # ---- hội thoại ----
    async def create_conversation(
        self, user_id: UUID, idempotency_key: UUID | None = None
    ) -> Conversation:
        async with self._uow.for_user(user_id) as uow:
            if idempotency_key is not None:
                existing_id = await uow.idempotency.get(CONVERSATION_SCOPE, idempotency_key)
                if existing_id is not None:
                    existing = await uow.conversations.get(existing_id)
                    if existing is not None:
                        return existing
            now = self._clock()
            conv = Conversation(self._new_id(), user_id, now, now)
            await uow.conversations.add(conv)
            if idempotency_key is not None:
                await uow.idempotency.put(CONVERSATION_SCOPE, idempotency_key, conv.id)
            return conv

    # ---- pha 1: kiểm tra + lưu câu hỏi ----
    async def prepare(
        self,
        user_id: UUID,
        conversation_id: UUID,
        *,
        question: str,
        document_ids: Sequence[UUID],
        client_message_id: UUID | None = None,
    ) -> AskContext:
        if not await self._config.qa_enabled():
            raise QaDisabled()
        await self._limiter.hit(user_id, ASK_RATE_BUCKET, ASK_RATE_LIMIT, ASK_RATE_WINDOW)

        question = question.strip()
        if not question:
            raise ValidationFailed("Câu hỏi không được để trống.")
        if len(question) > await self._config.max_question_length():
            raise QuestionTooLong()
        max_docs = await self._config.max_documents_per_question()
        requested = list(dict.fromkeys(document_ids))  # bỏ trùng, giữ thứ tự
        if len(requested) > max_docs:
            raise ValidationFailed(f"Tối đa {max_docs} tài liệu cho một câu hỏi.")

        async with self._uow.for_user(user_id) as uow:
            if await uow.conversations.get(conversation_id) is None:
                raise NotFound()

            if client_message_id is not None:
                prior = await uow.messages.find_user_message_by_client_id(
                    conversation_id, client_message_id
                )
                if prior is not None:
                    return await self._replay(uow, user_id, prior)

            if requested:
                found = await uow.documents.get_many(requested)
                if {d.id for d in found} != set(requested):
                    raise NotFound()  # không tồn tại hoặc thuộc người khác — không phân biệt
                if any(d.status is not DocumentStatus.READY for d in found):
                    raise DocumentNotReady()
                scope = tuple(requested)
            else:
                ready = await uow.documents.list_ready_ids(max_docs)
                if not ready:
                    raise NoReadyDocuments()
                scope = tuple(ready)

            now = self._clock()
            user_msg = Message.new_user(
                self._new_id(), conversation_id, user_id, question, now, client_message_id
            )
            ai_msg = Message.new_ai(self._new_id(), conversation_id, user_id, user_msg.id, now)
            ai_msg.start_streaming()
            await uow.messages.add(user_msg)
            await uow.messages.set_documents(user_msg.id, scope)
            await uow.messages.add(ai_msg)
        return AskContext(user_id, question, scope, ai_msg)

    async def _replay(self, uow: Any, user_id: UUID, prior: Message) -> AskContext:
        reply = await uow.messages.find_reply(prior.id)
        if reply is None or reply.status is not MessageStatus.COMPLETE:
            raise RequestInProgress()
        views = await uow.citations.for_message(reply.id)
        return AskContext(user_id, prior.text, (), reply, replay_citations=tuple(views))

    # ---- pha 2: phát sự kiện ----
    async def stream(self, ctx: AskContext) -> AsyncIterator[SseEvent]:
        ai = ctx.ai_message
        yield SseEvent("message", {"messageId": str(ai.id), "status": "streaming"})

        if ctx.replay_citations is not None:
            async for ev in self._replay_events(ctx):
                yield ev
            return

        queue: asyncio.Queue[Token | Completed | BaseException | _End] = asyncio.Queue()
        producer = asyncio.create_task(self._produce(ctx, queue))
        started = time.monotonic()
        first_token = True
        finished = False
        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), self._ping)
                except TimeoutError:
                    yield SseEvent("ping", {})
                    continue
                if isinstance(item, _End):
                    # Pipeline kết thúc mà không báo Completed: coi là lỗi, không để stream cụt.
                    raise AnswerFailed("LLM_UNAVAILABLE", "generate", True)
                if isinstance(item, BaseException):
                    raise item
                if isinstance(item, Token):
                    if first_token:
                        first_token = False
                        self._metrics.first_token(time.monotonic() - started)
                    ai.append(item.text)
                    yield SseEvent("token", {"text": item.text})
                else:  # Completed
                    citations = await self._finish(ctx, item)
                    finished = True
                    yield SseEvent(
                        "citations", {"citations": [citation_payload(c) for c in citations]}
                    )
                    yield SseEvent(
                        "done",
                        {
                            "messageId": str(ai.id),
                            "status": "complete",
                            "grounded": item.grounded,
                            "citationCount": len(citations),
                        },
                    )
                    break
        except AnswerFailed as exc:
            finished = True
            self._metrics.stage_error(exc.stage)
            yield await self._fail(ctx, exc.code, exc.stage, exc.retryable)
        except Exception as exc:
            finished = True
            logger.error(
                "answer pipeline crashed",
                extra={"event": "answer_crashed", "exc_type": type(exc).__name__},
            )
            self._metrics.stage_error("generate")
            yield await self._fail(ctx, "INTERNAL_ERROR", "generate", True)
        finally:
            producer.cancel()
            if not finished:
                # Client đóng kết nối / bị hủy: giữ phần đã nhận, đánh dấu interrupted.
                await asyncio.shield(self._save_terminal(ctx, interrupted=True))

    async def _produce(
        self, ctx: AskContext, queue: asyncio.Queue[Token | Completed | BaseException | _End]
    ) -> None:
        try:
            async for event in self._pipeline.answer(
                user_id=ctx.user_id, question=ctx.question, document_ids=ctx.document_ids
            ):
                await queue.put(event)
            await queue.put(_END)
        except asyncio.CancelledError:
            raise
        except BaseException as exc:
            await queue.put(exc)

    async def _finish(self, ctx: AskContext, done: Completed) -> list[Citation]:
        ai = ctx.ai_message
        ai.complete(done.grounded, self._clock())
        citations = _to_citations(ai, done.citations, self._new_id)
        try:
            async with self._uow.for_user(ctx.user_id) as uow:
                await uow.messages.update(ai)
                if citations:
                    await uow.citations.add_many(citations)
        except BaseException:
            # Lưu lỗi: trả message về `streaming` để đường lỗi còn ghi được trạng thái cuối.
            ai.status, ai.grounded, ai.completed_at = MessageStatus.STREAMING, None, None
            raise
        self._metrics.answer_finished(done.grounded)
        return citations

    async def _fail(self, ctx: AskContext, code: str, stage: str, retryable: bool) -> SseEvent:
        ai = ctx.ai_message
        await self._save_terminal(ctx, interrupted=bool(ai.text), error_code=code)
        return SseEvent(
            "error",
            {"code": code, "stage": stage, "retryable": retryable, "messageId": str(ai.id)},
        )

    async def _save_terminal(
        self, ctx: AskContext, *, interrupted: bool, error_code: str | None = None
    ) -> None:
        ai = ctx.ai_message
        if ai.status is not MessageStatus.STREAMING:
            return
        now = self._clock()
        if interrupted:
            ai.interrupt(now)
            ai.error_code = error_code
        else:
            ai.fail(error_code or "INTERNAL_ERROR", now)
        try:
            async with self._uow.for_user(ctx.user_id) as uow:
                await uow.messages.update(ai)
        except Exception:
            logger.error("could not persist terminal state", extra={"event": "persist_failed"})

    async def _replay_events(self, ctx: AskContext) -> AsyncIterator[SseEvent]:
        ai = ctx.ai_message
        if ai.text:
            yield SseEvent("token", {"text": ai.text})
        views = ctx.replay_citations or ()
        yield SseEvent("citations", {"citations": [citation_payload(v.citation) for v in views]})
        yield SseEvent(
            "done",
            {
                "messageId": str(ai.id),
                "status": "complete",
                "grounded": bool(ai.grounded),
                "citationCount": len(views),
            },
        )


def _to_citations(ai: Message, refs: Sequence[CitationRef], new_id: IdFactory) -> list[Citation]:
    seen: set[UUID] = set()
    out: list[Citation] = []
    for ref in sorted(refs, key=lambda r: r.ordinal):
        if ref.chunk_id in seen:
            continue
        seen.add(ref.chunk_id)
        out.append(
            Citation(
                id=new_id(),
                message_id=ai.id,
                user_id=ai.user_id,
                ordinal=len(out) + 1,
                page=ref.page,
                document_id=ref.document_id,
                chunk_id=ref.chunk_id,
                document_name=ref.document_name,
            )
        )
    return out
