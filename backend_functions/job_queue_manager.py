"""
Job Queue Manager
Manages video generation jobs and their mapping to topics using JSON persistence
"""

import os
import json
import uuid
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

class JobStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class VideoJob:
    job_id: str
    topic: str
    domain: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    message: str = ""
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    # Video generation parameters
    script_length: str = "medium"
    voice: str = "alloy"
    width: int = 1024
    height: int = 576
    fps: int = 24
    img_style_prompt: str = "cinematic, professional"
    include_dialogs: bool = True
    use_different_voices: bool = True
    add_captions: bool = True
    add_title_card: bool = True
    add_end_card: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key in ['created_at', 'started_at', 'completed_at']:
            if data[key] is not None:
                data[key] = data[key].isoformat() if isinstance(data[key], datetime) else data[key]
        # Convert enum to string
        data['status'] = data['status'].value if isinstance(data['status'], JobStatus) else data['status']
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoJob':
        """Create from dictionary (JSON deserialization)"""
        # Convert datetime strings back to datetime objects
        for key in ['created_at', 'started_at', 'completed_at']:
            if data[key] is not None and isinstance(data[key], str):
                try:
                    data[key] = datetime.fromisoformat(data[key])
                except:
                    data[key] = None
        
        # Convert status string to enum
        if isinstance(data['status'], str):
            data['status'] = JobStatus(data['status'])
        
        return cls(**data)

class JobQueueManager:
    """
    Manages video generation job queue with JSON persistence
    """
    
    def __init__(self, 
                 queue_file: str = "job_queue.json",
                 job_map_file: str = "job_video_mapping.json",
                 max_concurrent_jobs: int = 2,
                 auto_cleanup_hours: int = 24):
        
        self.queue_file = queue_file
        self.job_map_file = job_map_file
        self.max_concurrent_jobs = max_concurrent_jobs
        self.auto_cleanup_hours = auto_cleanup_hours
        
        # In-memory cache for faster access
        self._job_cache: Dict[str, VideoJob] = {}
        self._job_video_map: Dict[str, str] = {}  # job_id -> video_file_path
        
        # Thread lock for concurrent access
        self._lock = threading.Lock()
        
        # Load existing data
        self._load_from_files()
        
        print(f"[JOB QUEUE] Initialized with {len(self._job_cache)} existing jobs")
    
    def _load_from_files(self):
        """Load jobs and mappings from JSON files"""
        try:
            # Load job queue
            if os.path.exists(self.queue_file):
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                
                for job_id, job_dict in job_data.items():
                    try:
                        job = VideoJob.from_dict(job_dict)
                        self._job_cache[job_id] = job
                    except Exception as e:
                        print(f"[JOB QUEUE] Error loading job {job_id}: {e}")
            
            # Load job-video mapping
            if os.path.exists(self.job_map_file):
                with open(self.job_map_file, 'r', encoding='utf-8') as f:
                    self._job_video_map = json.load(f)
                    
        except Exception as e:
            print(f"[JOB QUEUE] Error loading from files: {e}")
    
    def _save_to_files(self):
        """Save jobs and mappings to JSON files"""
        try:
            # Save job queue
            job_data = {}
            for job_id, job in self._job_cache.items():
                job_data[job_id] = job.to_dict()
            
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False)
            
            # Save job-video mapping
            with open(self.job_map_file, 'w', encoding='utf-8') as f:
                json.dump(self._job_video_map, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"[JOB QUEUE] Error saving to files: {e}")
    
    def add_job(self, topic: str, domain: str, **kwargs) -> str:
        """Add new job to queue"""
        with self._lock:
            job_id = str(uuid.uuid4())
            
            job = VideoJob(
                job_id=job_id,
                topic=topic,
                domain=domain,
                status=JobStatus.QUEUED,
                created_at=datetime.now(),
                **kwargs
            )
            
            self._job_cache[job_id] = job
            self._save_to_files()
            
            print(f"[JOB QUEUE] Added job {job_id}: {topic}")
            return job_id
    
    def get_job(self, job_id: str) -> Optional[VideoJob]:
        """Get job by ID"""
        return self._job_cache.get(job_id)
    
    def update_job_status(self, job_id: str, status: JobStatus, 
                         progress: float = None, message: str = None, 
                         error: str = None, result: Dict[str, Any] = None):
        """Update job status and metadata"""
        with self._lock:
            if job_id not in self._job_cache:
                return False
            
            job = self._job_cache[job_id]
            job.status = status
            
            if progress is not None:
                job.progress = progress
            if message is not None:
                job.message = message
            if error is not None:
                job.error = error
            if result is not None:
                job.result = result
            
            # Update timestamps
            if status == JobStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.now()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job.completed_at = datetime.now()
            
            self._save_to_files()
            return True
    
    def get_next_job(self) -> Optional[VideoJob]:
        """Get next queued job for processing"""
        with self._lock:
            # Check if we've reached max concurrent jobs
            processing_count = sum(1 for job in self._job_cache.values() 
                                 if job.status == JobStatus.PROCESSING)
            
            if processing_count >= self.max_concurrent_jobs:
                return None
            
            # Find oldest queued job
            queued_jobs = [job for job in self._job_cache.values() 
                          if job.status == JobStatus.QUEUED]
            
            if not queued_jobs:
                return None
            
            # Sort by creation time
            next_job = min(queued_jobs, key=lambda j: j.created_at)
            return next_job
    
    def map_job_to_video(self, job_id: str, video_file_path: str):
        """Map completed job to its generated video file"""
        with self._lock:
            self._job_video_map[job_id] = video_file_path
            self._save_to_files()
            print(f"[JOB QUEUE] Mapped job {job_id} to video: {video_file_path}")
    
    def get_video_for_job(self, job_id: str) -> Optional[str]:
        """Get video file path for job"""
        return self._job_video_map.get(job_id)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        status = {
            "total_jobs": len(self._job_cache),
            "by_status": {},
            "by_domain": {},
            "processing_jobs": [],
            "next_jobs": [],
            "completed_videos": len(self._job_video_map)
        }
        
        # Count by status
        for status_enum in JobStatus:
            count = sum(1 for job in self._job_cache.values() if job.status == status_enum)
            status["by_status"][status_enum.value] = count
        
        # Count by domain
        domain_counts = {}
        for job in self._job_cache.values():
            domain_counts[job.domain] = domain_counts.get(job.domain, 0) + 1
        status["by_domain"] = domain_counts
        
        # Currently processing jobs
        processing_jobs = [
            {
                "job_id": job.job_id,
                "topic": job.topic,
                "domain": job.domain,
                "progress": job.progress,
                "message": job.message,
                "started_at": job.started_at.isoformat() if job.started_at else None
            }
            for job in self._job_cache.values() 
            if job.status == JobStatus.PROCESSING
        ]
        status["processing_jobs"] = processing_jobs
        
        # Next jobs in queue
        next_jobs = sorted(
            [job for job in self._job_cache.values() if job.status == JobStatus.QUEUED],
            key=lambda j: j.created_at
        )[:5]
        
        status["next_jobs"] = [
            {
                "job_id": job.job_id,
                "topic": job.topic,
                "domain": job.domain,
                "created_at": job.created_at.isoformat()
            }
            for job in next_jobs
        ]
        
        return status
    
    def get_completed_jobs_with_videos(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get completed jobs that have generated videos"""
        completed_jobs = []
        
        for job in self._job_cache.values():
            if (job.status == JobStatus.COMPLETED and 
                job.job_id in self._job_video_map):
                
                video_path = self._job_video_map[job.job_id]
                
                # Check if video file still exists
                video_exists = os.path.exists(video_path) if video_path else False
                
                job_info = {
                    "job_id": job.job_id,
                    "topic": job.topic,
                    "domain": job.domain,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "video_path": video_path,
                    "video_exists": video_exists,
                    "result": job.result
                }
                completed_jobs.append(job_info)
        
        # Sort by completion time (newest first)
        completed_jobs.sort(
            key=lambda j: j.get("completed_at", ""), 
            reverse=True
        )
        
        return completed_jobs[:limit]
    
    def cleanup_old_jobs(self, hours: int = None) -> Dict[str, int]:
        """Remove old completed/failed jobs"""
        if hours is None:
            hours = self.auto_cleanup_hours
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            jobs_to_remove = []
            videos_to_remove = []
            
            for job_id, job in self._job_cache.items():
                # Remove old completed or failed jobs
                if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED] and
                    job.completed_at and job.completed_at < cutoff_time):
                    
                    jobs_to_remove.append(job_id)
                    
                    # Also remove video mapping
                    if job_id in self._job_video_map:
                        videos_to_remove.append(job_id)
            
            # Remove jobs
            for job_id in jobs_to_remove:
                del self._job_cache[job_id]
            
            # Remove video mappings
            for job_id in videos_to_remove:
                del self._job_video_map[job_id]
            
            # Save changes
            if jobs_to_remove or videos_to_remove:
                self._save_to_files()
            
            cleanup_stats = {
                "jobs_removed": len(jobs_to_remove),
                "video_mappings_removed": len(videos_to_remove),
                "cutoff_hours": hours
            }
            
            if cleanup_stats["jobs_removed"] > 0:
                print(f"[JOB QUEUE] Cleaned up {cleanup_stats['jobs_removed']} old jobs")
            
            return cleanup_stats
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job"""
        with self._lock:
            if job_id not in self._job_cache:
                return False
            
            job = self._job_cache[job_id]
            
            # Can only cancel queued jobs
            if job.status != JobStatus.QUEUED:
                return False
            
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            job.message = "Job cancelled by user"
            
            self._save_to_files()
            print(f"[JOB QUEUE] Cancelled job {job_id}")
            return True
    
    def get_jobs_by_domain(self, domain: str, status: JobStatus = None) -> List[VideoJob]:
        """Get jobs filtered by domain and optionally status"""
        jobs = [job for job in self._job_cache.values() if job.domain == domain]
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)
    
    def bulk_add_jobs_from_topics(self, topics_by_domain: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """Add multiple jobs from topic generation results"""
        added_count = {}
        
        for domain, topics in topics_by_domain.items():
            count = 0
            for topic_data in topics:
                if not topic_data.get("used", False):  # Only add unused topics
                    job_id = self.add_job(
                        topic=topic_data["topic"],
                        domain=domain,
                        script_length="medium",  # Default values
                        voice="alloy",
                        img_style_prompt=f"professional, {domain}-themed, high quality"
                    )
                    count += 1
            
            added_count[domain] = count
            if count > 0:
                print(f"[JOB QUEUE] Added {count} jobs for domain '{domain}'")
        
        return added_count

if __name__ == "__main__":
    # Test the job queue manager
    manager = JobQueueManager()
    
    print("Testing Job Queue Manager...")
    
    # Add some test jobs
    job1 = manager.add_job("The story of Hanuman", "indian_mythology")
    job2 = manager.add_job("AI and the future", "technology")
    job3 = manager.add_job("Quantum physics explained", "science")
    
    print(f"\nAdded jobs: {job1}, {job2}, {job3}")
    
    # Get queue status
    status = manager.get_queue_status()
    print(f"\nQueue Status:")
    print(f"Total jobs: {status['total_jobs']}")
    print(f"By status: {status['by_status']}")
    print(f"By domain: {status['by_domain']}")
    
    # Test getting next job
    next_job = manager.get_next_job()
    if next_job:
        print(f"\nNext job: {next_job.topic} (ID: {next_job.job_id})")
        
        # Simulate processing
        manager.update_job_status(next_job.job_id, JobStatus.PROCESSING, 
                                progress=0.5, message="Generating video...")
        
        # Simulate completion
        manager.update_job_status(next_job.job_id, JobStatus.COMPLETED, 
                                progress=1.0, message="Video completed")
        
        # Map to video file
        manager.map_job_to_video(next_job.job_id, f"/videos/{next_job.job_id}.mp4")
    
    # Final status
    final_status = manager.get_queue_status()
    print(f"\nFinal Status:")
    print(f"By status: {final_status['by_status']}")
    
    # Get completed jobs with videos
    completed = manager.get_completed_jobs_with_videos()
    print(f"\nCompleted jobs with videos: {len(completed)}")
    for job in completed:
        print(f"- {job['topic']} -> {job['video_path']}")