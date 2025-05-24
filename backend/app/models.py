import uuid

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, Relationship, SQLModel
from typing import List, Optional, Union
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str
    meetings: List["Meeting"] = Relationship(back_populates="owner", sa_relationship_kwargs={"cascade": "all, delete"})

# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: UUID


class UsersPublic(SQLModel):
    data: List[UserPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: UUID = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


class MeetingStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    ONGOING = "ONGOING"
    ENDED = "ENDED"


class MeetingBase(SQLModel):
    title: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: MeetingStatus = MeetingStatus.SCHEDULED


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[MeetingStatus] = None


class Meeting(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=255)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: MeetingStatus = Field(default=MeetingStatus.SCHEDULED)
    owner_id: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    owner: User = Relationship(back_populates="meetings")
    recordings: List["Recording"] = Relationship(back_populates="meeting", sa_relationship_kwargs={"cascade": "all, delete"})
    action_items: List["ActionItem"] = Relationship(back_populates="meeting", sa_relationship_kwargs={"cascade": "all, delete"})


class RecordingStatus(str, Enum):
    RECORDING = "RECORDING"
    COMPLETED = "COMPLETED"


class RecordingBase(SQLModel):
    meeting_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    status: RecordingStatus = RecordingStatus.RECORDING
    file_url: Optional[str] = None
    transcript_url: Optional[str] = None


class RecordingCreate(RecordingBase):
    pass


class RecordingUpdate(SQLModel):
    end_time: Optional[datetime] = None
    status: Optional[RecordingStatus] = None
    file_url: Optional[str] = None
    transcript_url: Optional[str] = None


class Recording(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    meeting_id: UUID = Field(foreign_key="meeting.id")
    start_time: datetime
    end_time: Optional[datetime] = None
    status: RecordingStatus
    file_url: Optional[str] = None
    transcript_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    meeting: Optional["Meeting"] = Relationship(back_populates="recordings")
    transcripts: List["Transcript"] = Relationship(back_populates="recording")


class TranscriptBase(SQLModel):
    content: str


class TranscriptCreate(SQLModel):
    recording_id: UUID
    content: str


class Transcript(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    recording_id: UUID = Field(foreign_key="recording.id")
    recording: Optional["Recording"] = Relationship(back_populates="transcripts")
    
    summaries: List["Summary"] = Relationship(back_populates="transcript")


class SummaryLengthType(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class SummaryBase(SQLModel):
    content: str
    length_type: SummaryLengthType


class SummaryCreate(SQLModel):
    content: Optional[str] = None  # Optional, will be generated if not provided
    length_type: SummaryLengthType = SummaryLengthType.MEDIUM


class Summary(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    content: str
    length_type: SummaryLengthType
    created_at: datetime = Field(default_factory=datetime.now)
    
    transcript_id: UUID = Field(foreign_key="transcript.id")
    
    transcript: Transcript = Relationship(back_populates="summaries")


class MeetingPublic(SQLModel):
    id: UUID
    title: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: MeetingStatus
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class MeetingsPublic(SQLModel):
    data: List[MeetingPublic]
    count: int


class RecordingPublic(SQLModel):
    id: UUID
    meeting_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    status: RecordingStatus
    file_url: Optional[str] = None
    transcript_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RecordingsPublic(SQLModel):
    data: List[RecordingPublic]
    count: int


class TranscriptPublic(SQLModel):
    id: UUID
    recording_id: UUID
    content: str
    created_at: datetime


class TranscriptsPublic(SQLModel):
    data: List[TranscriptPublic]
    count: int


class SummaryPublic(SQLModel):
    id: UUID
    transcript_id: UUID
    content: str
    length_type: SummaryLengthType
    created_at: datetime


class SummariesPublic(SQLModel):
    data: List[SummaryPublic]
    count: int


# Action Items Models
class ActionItemStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ActionItemBase(SQLModel):
    title: str = Field(max_length=255)
    description: Optional[str] = None
    assignee: Optional[str] = Field(default=None, max_length=255)
    due_date: Optional[datetime] = None
    status: ActionItemStatus = ActionItemStatus.PENDING


class ActionItemCreate(ActionItemBase):
    meeting_id: UUID


class ActionItemUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    assignee: Optional[str] = Field(default=None, max_length=255)
    due_date: Optional[datetime] = None
    status: Optional[ActionItemStatus] = None


class ActionItem(ActionItemBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    meeting_id: UUID = Field(foreign_key="meeting.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    meeting: Optional["Meeting"] = Relationship(back_populates="action_items")


class ActionItemPublic(ActionItemBase):
    id: UUID
    meeting_id: UUID
    created_at: datetime
    updated_at: datetime


class ActionItemsPublic(SQLModel):
    data: List[ActionItemPublic]
    count: int

