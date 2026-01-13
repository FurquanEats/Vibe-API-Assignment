from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base

# Database Setup
DATABASE_URL = "sqlite:///./vibecheck.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Models ---

class Poll(Base):
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    
    options = relationship("Option", back_populates="poll")
    votes = relationship("Vote", back_populates="poll")

class Option(Base):
    __tablename__ = "options"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    
    poll = relationship("Poll", back_populates="options")

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    option_id = Column(Integer, ForeignKey("options.id"))
    
    poll = relationship("Poll", back_populates="votes")

    # Enforce one vote per user per poll at the database level
    __table_args__ = (UniqueConstraint('user_id', 'poll_id', name='_user_poll_uc'),)

Base.metadata.create_all(bind=engine)

# --- Schemas ---

class PollCreate(BaseModel):
    question: str
    options: list[str]

class VoteCreate(BaseModel):
    user_id: str
    option_id: int

# --- API ---

app = FastAPI(title="Vibe Check Polling API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/polls", status_code=201)
def create_poll(poll_data: PollCreate, db: Session = Depends(get_db)):
    """
    Creates a new poll and its associated options.
    """
    new_poll = Poll(question=poll_data.question)
    db.add(new_poll)
    db.commit()
    db.refresh(new_poll)
    
    for opt_text in poll_data.options:
        new_option = Option(text=opt_text, poll_id=new_poll.id)
        db.add(new_option)
    db.commit()
    
    return {"id": new_poll.id, "message": "Poll created successfully"}

@app.get("/polls/{poll_id}")
def get_poll(poll_id: int, db: Session = Depends(get_db)):
    """
    Returns poll details and current vote counts for each option.
    """
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    response_options = []
    for option in poll.options:
        vote_count = db.query(Vote).filter(Vote.option_id == option.id).count()
        response_options.append({
            "option_id": option.id,
            "text": option.text,
            "votes": vote_count
        })
        
    return {
        "id": poll.id,
        "question": poll.question,
        "options": response_options
    }

@app.post("/polls/{poll_id}/vote")
def vote_poll(poll_id: int, vote_data: VoteCreate, db: Session = Depends(get_db)):
    """
    Records a vote. Handles the UniqueConstraint to prevent duplicates.
    """
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    # Validate that the selected option belongs to this poll
    valid_option = db.query(Option).filter(Option.id == vote_data.option_id, Option.poll_id == poll_id).first()
    if not valid_option:
        raise HTTPException(status_code=400, detail="Invalid option for this poll")

    try:
        new_vote = Vote(user_id=vote_data.user_id, poll_id=poll_id, option_id=vote_data.option_id)
        db.add(new_vote)
        db.commit()
    except Exception:
        db.rollback()
        # Catch integrity error from UniqueConstraint
        raise HTTPException(status_code=400, detail="User has already voted on this poll")

    return {"message": "Vote cast successfully"}