from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import random

app = FastAPI(title="Bond - Dating API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Profile(BaseModel):
    id: str
    name: str
    age: int
    bio: str
    interests: List[str]
    image: str
    location: str
    verified: bool = False
    gender: Optional[str] = "Not specified"
    distance_km: Optional[float] = None

class LikeRequest(BaseModel):
    from_user: str
    to_user: str

class SuperLikeRequest(BaseModel):
    from_user: str
    to_user: str

class Message(BaseModel):
    id: str
    from_user: str
    to_user: str
    text: str
    timestamp: str

class Match(BaseModel):
    id: str
    users: List[str]
    created_at: str
    last_message: Optional[str] = None

profiles_db: List[Profile] = [
    Profile(id="1", name="Ama", age=24, bio="Love adventure and good conversation. Looking for genuine connection in Accra.", interests=["Travel", "Music", "Coffee", "Books", "Beach"], image="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&h=600&fit=crop", location="Accra, GH", verified=True, gender="Female", distance_km=2.3),
    Profile(id="2", name="Kwame", age=27, bio="Entrepreneur & fitness enthusiast. Building my startup in Kumasi.", interests=["Gym", "Business", "Football", "Tech", "Startups"], image="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=600&fit=crop", location="Kumasi, GH", verified=True, gender="Male", distance_km=5.1),
    Profile(id="3", name="Serwaa", age=23, bio="Artist and dreamer. Searching for my muse. Painting and soul music.", interests=["Art", "Photography", "Dance", "Nature", "Painting"], image="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=600&fit=crop", location="Accra, GH", verified=False, gender="Female", distance_km=1.2),
    Profile(id="4", name="Kojo", age=26, bio="Software dev who loves jollof and code. Swipe right if you laugh at my jokes.", interests=["Coding", "Gaming", "Food", "Movies", "Jollof"], image="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&h=600&fit=crop", location="Tema, GH", verified=True, gender="Male", distance_km=12.4),
    Profile(id="5", name="Adwoa", age=25, bio="Nurse by day, dancer by night. Looking for someone who can keep up!", interests=["Dance", "Health", "Music", "Yoga", "Cooking"], image="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=600&fit=crop", location="Cape Coast, GH", verified=True, gender="Female", distance_km=8.7),
    Profile(id="6", name="Yaw", age=29, bio="Engineer. Love football, F1 and building things.", interests=["Engineering", "Football", "F1", "Building", "Cars"], image="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=600&fit=crop", location="Accra, GH", verified=True, gender="Male", distance_km=3.3),
]

likes_db = []
super_likes_db = []
matches_db = []
messages_db = []
dislikes_db = []

@app.get("/")
def root():
    return {"message": "Bond API is live! ❤️", "version": "2.0.0", "profiles": len(profiles_db), "matches": len(matches_db), "status": "Ready for love"}

@app.get("/profiles", response_model=List[Profile])
def get_profiles(skip: int = 0, limit: int = 20, location: Optional[str] = None):
    filtered = profiles_db
    if location:
        filtered = [p for p in filtered if location.lower() in p.location.lower()]
    return filtered[skip:skip+limit]

@app.get("/profiles/{profile_id}", response_model=Profile)
def get_profile(profile_id: str):
    for p in profiles_db:
        if p.id == profile_id:
            return p
    raise HTTPException(status_code=404, detail="Profile not found")

@app.get("/discover")
def discover_profiles():
    disliked_ids = [d["to_user"] for d in dislikes_db if d["from_user"] == "user_me"]
    available = [p for p in profiles_db if p.id not in disliked_ids]
    random.shuffle(available)
    return available[:10]

@app.post("/like")
def like_profile(req: LikeRequest):
    likes_db.append(req.dict())
    is_match = False
    match_id = None
    for like in likes_db:
        if like["from_user"] == req.to_user and like["to_user"] == req.from_user:
            is_match = True
            match_id = str(uuid.uuid4())[:8]
            existing = [m for m in matches_db if set(m["users"]) == set([req.from_user, req.to_user])]
            if not existing:
                matches_db.append({"id": match_id, "users": [req.from_user, req.to_user], "created_at": datetime.now().isoformat(), "last_message": None})
            break
    return {"liked": True, "is_match": is_match, "match_id": match_id, "message": "It's a Match! 💘" if is_match else "Like sent!"}

@app.post("/superlike")
def super_like(req: SuperLikeRequest):
    super_likes_db.append(req.dict())
    return {"superliked": True, "message": "Super Like sent! ⭐"}

@app.post("/dislike")
def dislike_profile(req: LikeRequest):
    dislikes_db.append(req.dict())
    return {"disliked": True}

@app.get("/matches")
def get_matches(user_id: str = "user_me"):
    user_matches = []
    for match in matches_db:
        if user_id in match["users"]:
            other_id = [u for u in match["users"] if u != user_id][0]
            other_profile = next((p for p in profiles_db if p.id == other_id), None)
            if other_profile:
                user_matches.append({**match, "other_user": other_profile.dict()})
    return user_matches

@app.get("/likes")
def get_likes():
    return {"likes": likes_db, "super_likes": super_likes_db, "count": len(likes_db)}

@app.post("/profiles", response_model=Profile)
def create_profile(profile: Profile):
    if any(p.id == profile.id for p in profiles_db):
        raise HTTPException(status_code=400, detail="Profile ID already exists")
    profiles_db.append(profile)
    return profile

@app.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str):
    global profiles_db
    profiles_db = [p for p in profiles_db if p.id != profile_id]
    return {"deleted": True, "id": profile_id}

@app.get("/stats")
def get_stats():
    return {"total_profiles": len(profiles_db), "total_matches": len(matches_db), "total_likes": len(likes_db), "active_users": len(profiles_db) + 1}
