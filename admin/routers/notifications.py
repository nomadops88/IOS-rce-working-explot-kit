import asyncio
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime
from typing import Optional
from jose import JWTError, jwt

from ..database import get_db, Notification, create_notification, User
from ..auth import get_current_user, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/notifications", tags=["notifications"], redirect_slashes=False)

# SSE connection management
_notification_queues: list = []


def _broadcast_notification(notification: dict):
    """Broadcast notification to all SSE connections."""
    dead_queues = []
    for queue in _notification_queues:
        try:
            queue.put_nowait(notification)
        except asyncio.QueueFull:
            dead_queues.append(queue)
        except Exception:
            dead_queues.append(queue)
    for q in dead_queues:
        if q in _notification_queues:
            _notification_queues.remove(q)


async def _get_current_user_sse(
    request: Request,
    token: Optional[str] = Query(None, description="Fallback query token for EventSource (no custom headers)"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """SSE auth: prefers Authorization header, falls back to query token."""
    raw = None
    if authorization and authorization.startswith("Bearer "):
        raw = authorization[7:]
    elif token:
        raw = token
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(raw, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("")
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Notification).order_by(desc(Notification.timestamp))
    if unread_only:
        query = query.filter(Notification.is_read == 0)
    if category:
        query = query.filter(Notification.category == category)

    total = query.count()
    items = query.offset(skip).limit(limit).all()
    unread_count = db.query(func.count(Notification.id)).filter(Notification.is_read == 0).scalar()

    return {
        "total": total,
        "unread_count": unread_count,
        "items": items,
        "skip": skip,
        "limit": limit
    }


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    count = db.query(func.count(Notification.id)).filter(Notification.is_read == 0).scalar()
    return {"unread_count": count}


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        return {"message": "Notification not found"}
    notif.is_read = 1
    db.commit()
    return {"message": "Notification marked as read"}


@router.put("/read")
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    db.query(Notification).filter(Notification.is_read == 0).update({"is_read": 1})
    db.commit()
    return {"message": "All notifications marked as read"}


@router.delete("")
async def clear_notifications(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Notification)
    if category:
        query = query.filter(Notification.category == category)
    deleted = query.delete(synchronize_session=False)
    db.commit()
    return {"message": f"Cleared {deleted} notifications"}


@router.get("/stream")
async def notification_stream(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(_get_current_user_sse)
):
    """SSE real-time notification stream."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _notification_queues.append(queue)

    async def event_generator():
        try:
            # Send connection event
            yield f"event: connected\ndata: {{\"message\": \"SSE connected\"}}\n\n"

            while True:
                try:
                    notification = await asyncio.wait_for(queue.get(), timeout=30.0)
                    import json
                    data = json.dumps(notification, ensure_ascii=False, default=str)
                    yield f"event: notification\ndata: {data}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat to keep connection alive
                    yield f"event: heartbeat\ndata: {{}}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if queue in _notification_queues:
                _notification_queues.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def broadcast_notification_sync(db: Session, title: str, message: str, category: str = "info",
                                 related_device_uuid: str = None, related_resource_type: str = None,
                                 related_resource_id: str = None):
    """Create notification and broadcast to SSE clients (called by other routers)."""
    create_notification(
        db, title, message, category,
        related_device_uuid, related_resource_type, related_resource_id
    )

    import json
    notif_dict = {
        "title": title,
        "message": message,
        "category": category,
        "related_device_uuid": related_device_uuid,
        "related_resource_type": related_resource_type,
        "related_resource_id": related_resource_id,
        "timestamp": datetime.now().isoformat()
    }
    # Schedule broadcast in running event loop if available
    try:
        loop = asyncio.get_running_loop()
        loop.call_soon(_broadcast_notification, notif_dict)
    except RuntimeError:
        pass
