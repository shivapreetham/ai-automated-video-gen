"""
Agentic Video Generation Worker
Automatically processes video generation jobs from the queue
"""

import os
import sys
import time
import threading
import signal
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from backend_functions.job_queue_manager import JobQueueManager, JobStatus
from backend_functions.story_video_generator import generate_story_video
from agents.topic_generation_agent import TopicGenerationAgent

class AgenticVideoWorker:
    """
    Autonomous worker that processes video generation jobs
    """
    
    def __init__(self, 
                 worker_id: str = "worker-1",
                 poll_interval: int = 10,
                 max_retries: int = 2,
                 auto_refill_queue: bool = True):
        
        self.worker_id = worker_id
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.auto_refill_queue = auto_refill_queue
        
        # Initialize components
        self.job_manager = JobQueueManager()
        self.topic_agent = TopicGenerationAgent() if auto_refill_queue else None
        
        # Worker state
        self.is_running = False
        self.current_job_id = None
        self.worker_thread = None
        
        # Statistics
        self.stats = {
            "jobs_processed": 0,
            "jobs_completed": 0,
            "jobs_failed": 0,
            "started_at": None,
            "last_activity": None
        }
        
        print(f"[WORKER {worker_id}] Initialized agentic video worker")
    
    def start(self):
        """Start the worker in a separate thread"""
        if self.is_running:
            print(f"[WORKER {self.worker_id}] Already running")
            return
        
        self.is_running = True
        self.stats["started_at"] = datetime.now()
        
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        print(f"[WORKER {self.worker_id}] Started")
    
    def stop(self):
        """Stop the worker"""
        if not self.is_running:
            return
        
        print(f"[WORKER {self.worker_id}] Stopping...")
        self.is_running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=30)
        
        print(f"[WORKER {self.worker_id}] Stopped")
    
    def _worker_loop(self):
        """Main worker loop"""
        print(f"[WORKER {self.worker_id}] Starting worker loop")
        
        while self.is_running:
            try:
                # Check for new jobs
                next_job = self.job_manager.get_next_job()
                
                if next_job:
                    self._process_job(next_job)
                else:
                    # No jobs available - maybe refill queue
                    if self.auto_refill_queue and self._should_refill_queue():
                        self._refill_queue()
                    
                    # Wait before checking again
                    time.sleep(self.poll_interval)
                
            except Exception as e:
                print(f"[WORKER {self.worker_id}] Error in worker loop: {e}")
                time.sleep(self.poll_interval)
        
        print(f"[WORKER {self.worker_id}] Worker loop ended")
    
    def _process_job(self, job):
        """Process a single video generation job"""
        job_id = job.job_id
        self.current_job_id = job_id
        self.stats["jobs_processed"] += 1
        self.stats["last_activity"] = datetime.now()
        
        print(f"[WORKER {self.worker_id}] Processing job {job_id}: {job.topic}")
        
        try:
            # Update job status to processing
            self.job_manager.update_job_status(
                job_id, JobStatus.PROCESSING, 
                progress=0.0, 
                message=f"Starting video generation (Worker: {self.worker_id})"
            )
            
            # Generate video using the story video generator
            result = generate_story_video(
                topic=job.topic,
                script_length=job.script_length,
                voice=job.voice,
                width=job.width,
                height=job.height,
                fps=job.fps,
                img_style_prompt=job.img_style_prompt,
                include_dialogs=job.include_dialogs,
                use_different_voices=job.use_different_voices,
                add_captions=job.add_captions,
                add_title_card=job.add_title_card,
                add_end_card=job.add_end_card
            )
            
            if result.get("success"):
                # Success - update job and map video
                final_video = result.get("final_video", {})
                video_file_path = final_video.get("file_path")
                
                self.job_manager.update_job_status(
                    job_id, JobStatus.COMPLETED,
                    progress=1.0,
                    message=f"Video generation completed (Worker: {self.worker_id})",
                    result=result
                )
                
                if video_file_path:
                    self.job_manager.map_job_to_video(job_id, video_file_path)
                
                self.stats["jobs_completed"] += 1
                print(f"[WORKER {self.worker_id}] Job {job_id} completed successfully")
                
            else:
                # Failed - update job with error
                error_msg = result.get("error", "Unknown error occurred")
                self.job_manager.update_job_status(
                    job_id, JobStatus.FAILED,
                    message=f"Video generation failed (Worker: {self.worker_id})",
                    error=error_msg
                )
                
                self.stats["jobs_failed"] += 1
                print(f"[WORKER {self.worker_id}] Job {job_id} failed: {error_msg}")
                
        except Exception as e:
            # Unexpected error during processing
            error_msg = str(e)
            self.job_manager.update_job_status(
                job_id, JobStatus.FAILED,
                message=f"Processing error (Worker: {self.worker_id})",
                error=error_msg
            )
            
            self.stats["jobs_failed"] += 1
            print(f"[WORKER {self.worker_id}] Job {job_id} error: {error_msg}")
        
        finally:
            self.current_job_id = None
    
    def _should_refill_queue(self) -> bool:
        """Check if queue needs refilling"""
        if not self.topic_agent:
            return False
        
        status = self.job_manager.get_queue_status()
        queued_jobs = status["by_status"].get("queued", 0)
        
        # Refill if less than 5 queued jobs
        return queued_jobs < 5
    
    def _refill_queue(self):
        """Automatically refill queue with new topics"""
        if not self.topic_agent:
            return
        
        print(f"[WORKER {self.worker_id}] Auto-refilling queue with new topics")
        
        try:
            # Generate topics for common domains
            domains = ["indian_mythology", "technology", "science", "history", "health"]
            daily_topics = self.topic_agent.generate_daily_topics(
                domains=domains, 
                topics_per_domain=3
            )
            
            # Add topics to job queue
            added_count = self.job_manager.bulk_add_jobs_from_topics(daily_topics)
            
            total_added = sum(added_count.values())
            print(f"[WORKER {self.worker_id}] Auto-refilled queue with {total_added} new jobs")
            
        except Exception as e:
            print(f"[WORKER {self.worker_id}] Error refilling queue: {e}")
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get current worker status"""
        status = {
            "worker_id": self.worker_id,
            "is_running": self.is_running,
            "current_job_id": self.current_job_id,
            "stats": dict(self.stats)
        }
        
        # Convert datetime objects to strings
        for key in ["started_at", "last_activity"]:
            if status["stats"][key]:
                status["stats"][key] = status["stats"][key].isoformat()
        
        # Add current job info if processing
        if self.current_job_id:
            current_job = self.job_manager.get_job(self.current_job_id)
            if current_job:
                status["current_job"] = {
                    "topic": current_job.topic,
                    "domain": current_job.domain,
                    "progress": current_job.progress,
                    "message": current_job.message
                }
        
        return status

class AgenticWorkforceManager:
    """
    Manages multiple agentic workers
    """
    
    def __init__(self, num_workers: int = 1):
        self.num_workers = num_workers
        self.workers: Dict[str, AgenticVideoWorker] = {}
        self.is_running = False
        
        # Create workers
        for i in range(num_workers):
            worker_id = f"worker-{i+1}"
            worker = AgenticVideoWorker(
                worker_id=worker_id,
                auto_refill_queue=(i == 0)  # Only first worker refills queue
            )
            self.workers[worker_id] = worker
        
        print(f"[WORKFORCE] Created {num_workers} workers")
    
    def start_all_workers(self):
        """Start all workers"""
        if self.is_running:
            print("[WORKFORCE] Already running")
            return
        
        self.is_running = True
        
        for worker in self.workers.values():
            worker.start()
        
        print(f"[WORKFORCE] Started {len(self.workers)} workers")
    
    def stop_all_workers(self):
        """Stop all workers"""
        if not self.is_running:
            return
        
        print("[WORKFORCE] Stopping all workers...")
        self.is_running = False
        
        for worker in self.workers.values():
            worker.stop()
        
        print("[WORKFORCE] All workers stopped")
    
    def get_workforce_status(self) -> Dict[str, Any]:
        """Get status of all workers"""
        return {
            "is_running": self.is_running,
            "num_workers": len(self.workers),
            "workers": {
                worker_id: worker.get_worker_status()
                for worker_id, worker in self.workers.items()
            }
        }

# Global workforce manager instance
_workforce_manager: Optional[AgenticWorkforceManager] = None

def start_agentic_workforce(num_workers: int = 1) -> AgenticWorkforceManager:
    """Start the agentic video generation workforce"""
    global _workforce_manager
    
    if _workforce_manager and _workforce_manager.is_running:
        print("[AGENTIC] Workforce already running")
        return _workforce_manager
    
    _workforce_manager = AgenticWorkforceManager(num_workers)
    _workforce_manager.start_all_workers()
    
    return _workforce_manager

def stop_agentic_workforce():
    """Stop the agentic video generation workforce"""
    global _workforce_manager
    
    if _workforce_manager:
        _workforce_manager.stop_all_workers()

def get_workforce_status() -> Optional[Dict[str, Any]]:
    """Get current workforce status"""
    global _workforce_manager
    
    if _workforce_manager:
        return _workforce_manager.get_workforce_status()
    
    return None

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    print("\n[AGENTIC] Received shutdown signal")
    stop_agentic_workforce()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting Agentic Video Generation System...")
    
    try:
        # Start workforce
        workforce = start_agentic_workforce(num_workers=1)
        
        print("Agentic system running. Press Ctrl+C to stop.")
        
        # Keep main thread alive and show periodic status
        while True:
            time.sleep(60)  # Wait 1 minute
            
            status = get_workforce_status()
            if status:
                total_processed = sum(
                    worker["stats"]["jobs_processed"] 
                    for worker in status["workers"].values()
                )
                total_completed = sum(
                    worker["stats"]["jobs_completed"] 
                    for worker in status["workers"].values()
                )
                
                print(f"[STATUS] Processed: {total_processed}, Completed: {total_completed}")
    
    except KeyboardInterrupt:
        print("\n[AGENTIC] Shutting down...")
        stop_agentic_workforce()
    except Exception as e:
        print(f"[AGENTIC] Error: {e}")
        stop_agentic_workforce()