#!/usr/bin/env python3
"""
NEXUS Voice Control Module
Enables voice commands for controlling NEXUS
"""

import asyncio
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime
import aiohttp
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import speech_recognition as sr
import pyttsx3
import threading
import queue

app = FastAPI(title="NEXUS Voice Control")

# Voice recognition and synthesis
recognizer = sr.Recognizer()
engine = pyttsx3.init()
command_queue = queue.Queue()

# NEXUS API endpoint
NEXUS_API = os.getenv("NEXUS_API_URL", "http://localhost:8002")

class VoiceController:
    def __init__(self):
        self.listening = False
        self.session = None
        self.commands = {
            "create": self.handle_create,
            "open": self.handle_open,
            "search": self.handle_search,
            "status": self.handle_status,
            "help": self.handle_help,
            "stop": self.handle_stop,
        }
        
    async def start(self):
        """Start voice control system"""
        self.session = aiohttp.ClientSession()
        self.listening = True
        
        # Start listening thread
        listener_thread = threading.Thread(target=self.listen_loop, daemon=True)
        listener_thread.start()
        
        # Process commands
        while self.listening:
            try:
                command = command_queue.get(timeout=0.1)
                await self.process_command(command)
            except queue.Empty:
                await asyncio.sleep(0.1)
                
    def listen_loop(self):
        """Continuous listening loop"""
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.listening:
                try:
                    # Listen for command
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    
                    # Recognize speech
                    text = recognizer.recognize_google(audio).lower()
                    
                    # Check for wake word
                    if "nexus" in text or "hey nexus" in text:
                        self.speak("Yes, I'm listening")
                        
                        # Listen for actual command
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        command = recognizer.recognize_google(audio)
                        
                        # Queue command for processing
                        command_queue.put(command)
                        
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    print(f"Voice recognition error: {e}")
                    
    def speak(self, text: str):
        """Text to speech"""
        engine.say(text)
        engine.runAndWait()
        
    async def process_command(self, command: str):
        """Process voice command"""
        command_lower = command.lower()
        
        # Find matching command handler
        for keyword, handler in self.commands.items():
            if keyword in command_lower:
                await handler(command)
                return
                
        # Default: send as natural language goal
        await self.send_goal(command)
        
    async def send_goal(self, goal: str):
        """Send goal to NEXUS"""
        try:
            async with self.session.post(
                f"{NEXUS_API}/api/v2/goals",
                json={"goal": goal, "priority": "MEDIUM"}
            ) as resp:
                if resp.status == 200:
                    self.speak("Goal submitted successfully")
                else:
                    self.speak("Failed to submit goal")
        except Exception as e:
            self.speak("Error connecting to NEXUS")
            
    async def handle_create(self, command: str):
        """Handle create commands"""
        if "project" in command:
            # Extract project name
            words = command.split()
            if "called" in words:
                idx = words.index("called")
                if idx + 1 < len(words):
                    project_name = " ".join(words[idx + 1:])
                    await self.create_project(project_name)
            else:
                self.speak("Please specify a project name")
                
    async def handle_open(self, command: str):
        """Handle open commands"""
        if "project" in command:
            # Extract project name
            words = command.split()
            project_name = None
            for i, word in enumerate(words):
                if word == "project" and i + 1 < len(words):
                    project_name = " ".join(words[i + 1:])
                    break
                    
            if project_name:
                self.speak(f"Opening project {project_name}")
                # Send command to NEXUS
                await self.send_goal(f"Open project {project_name}")
            else:
                self.speak("Which project would you like to open?")
                
    async def handle_search(self, command: str):
        """Handle search commands"""
        # Extract search query
        if "for" in command:
            idx = command.find("for")
            query = command[idx + 3:].strip()
            self.speak(f"Searching for {query}")
            await self.send_goal(f"Search codebase for {query}")
            
    async def handle_status(self, command: str):
        """Handle status commands"""
        try:
            async with self.session.get(f"{NEXUS_API}/api/stats") as resp:
                if resp.status == 200:
                    stats = await resp.json()
                    active_goals = stats.get('active_goals', 0)
                    self.speak(f"NEXUS has {active_goals} active goals")
                else:
                    self.speak("Unable to get status")
        except:
            self.speak("Error getting status")
            
    async def handle_help(self, command: str):
        """Handle help commands"""
        self.speak("You can ask me to create projects, open files, search code, or give me any natural language command")
        
    async def handle_stop(self, command: str):
        """Handle stop commands"""
        self.speak("Stopping voice control")
        self.listening = False
        
    async def create_project(self, project_name: str):
        """Create a new project"""
        self.speak(f"Creating project {project_name}")
        await self.send_goal(f"Create a new project called {project_name}")

# Global controller instance
controller = VoiceController()

@app.on_event("startup")
async def startup():
    """Start voice control on app startup"""
    asyncio.create_task(controller.start())
    
@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    controller.listening = False
    if controller.session:
        await controller.session.close()
        
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "listening": controller.listening}
    
@app.post("/api/voice/command")
async def voice_command(command: dict):
    """Process voice command via API"""
    text = command.get("text", "")
    if text:
        await controller.process_command(text)
        return {"status": "processed"}
    raise HTTPException(status_code=400, detail="No command text provided")
    
@app.websocket("/ws/voice")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time voice control"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            command = json.loads(data)
            
            if command.get("type") == "command":
                await controller.process_command(command.get("text", ""))
                await websocket.send_json({"status": "processed"})
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)