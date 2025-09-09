"""
Cloudflare Storage Manager
Manages video uploads to Cloudflare with storage limits and automatic cleanup
"""

import os
import json
import time
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class CloudflareStorageManager:
    """
    Manages video storage on Cloudflare with automatic cleanup and limits
    """
    
    def __init__(self, 
                 storage_file: str = "cloudflare_storage.json",
                 max_videos: int = 30,
                 cloudflare_config: Optional[Dict[str, str]] = None):
        
        self.storage_file = storage_file
        self.max_videos = max_videos
        self.cloudflare_config = cloudflare_config or {}
        
        # Load existing storage records
        self.storage_records = self._load_storage_records()
        
        print(f"[CLOUDFLARE] Initialized storage manager (max: {max_videos} videos)")
    
    def _load_storage_records(self) -> Dict[str, Dict[str, Any]]:
        """Load storage records from JSON file"""
        if not os.path.exists(self.storage_file):
            return {}
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[CLOUDFLARE] Error loading storage records: {e}")
            return {}
    
    def _save_storage_records(self):
        """Save storage records to JSON file"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.storage_records, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[CLOUDFLARE] Error saving storage records: {e}")
    
    def check_storage_limit(self) -> Dict[str, Any]:
        """Check current storage status against limits"""
        current_count = len(self.storage_records)
        
        return {
            "current_videos": current_count,
            "max_videos": self.max_videos,
            "available_slots": max(0, self.max_videos - current_count),
            "storage_full": current_count >= self.max_videos,
            "need_cleanup": current_count >= self.max_videos,
            "oldest_videos": self._get_oldest_videos(5) if current_count > 0 else []
        }
    
    def _get_oldest_videos(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get oldest videos for cleanup"""
        videos = list(self.storage_records.items())
        # Sort by upload timestamp
        videos.sort(key=lambda x: x[1].get("uploaded_at", ""))
        
        return [{
            "job_id": job_id,
            "cloudflare_id": record["cloudflare_id"],
            "filename": record.get("filename", "unknown"),
            "uploaded_at": record.get("uploaded_at"),
            "size_mb": record.get("size_mb", 0)
        } for job_id, record in videos[:limit]]
    
    def upload_video_to_cloudflare(self, job_id: str, video_file_path: str, 
                                  video_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upload video to Cloudflare storage"""
        try:
            # Check storage limit
            storage_status = self.check_storage_limit()
            
            if storage_status["storage_full"]:
                # Perform cleanup of oldest video
                cleanup_result = self._cleanup_oldest_video()
                if not cleanup_result["success"]:
                    return {
                        "success": False,
                        "error": "Storage full and cleanup failed",
                        "storage_status": storage_status,
                        "cleanup_result": cleanup_result
                    }
                
                print(f"[CLOUDFLARE] Cleaned up oldest video to make space")
            
            # Check if video file exists
            if not os.path.exists(video_file_path):
                return {
                    "success": False,
                    "error": "Video file not found",
                    "file_path": video_file_path
                }
            
            # Get file info
            file_size = os.path.getsize(video_file_path)
            filename = os.path.basename(video_file_path)
            
            # Simulate Cloudflare upload (replace with actual API call)
            cloudflare_result = self._simulate_cloudflare_upload(
                video_file_path, filename, file_size
            )
            
            if cloudflare_result["success"]:
                # Record successful upload
                upload_record = {
                    "job_id": job_id,
                    "cloudflare_id": cloudflare_result["cloudflare_id"],
                    "cloudflare_url": cloudflare_result["url"],
                    "filename": filename,
                    "file_size": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "uploaded_at": datetime.now().isoformat(),
                    "local_file_path": video_file_path,
                    "metadata": video_metadata or {}
                }
                
                self.storage_records[job_id] = upload_record
                self._save_storage_records()
                
                # Delete local file after successful upload
                try:
                    os.remove(video_file_path)
                    upload_record["local_file_deleted"] = True
                    print(f"[CLOUDFLARE] Deleted local file: {filename}")
                except Exception as e:
                    print(f"[CLOUDFLARE] Warning: Could not delete local file {filename}: {e}")
                    upload_record["local_file_deleted"] = False
                
                return {
                    "success": True,
                    "cloudflare_id": cloudflare_result["cloudflare_id"],
                    "cloudflare_url": cloudflare_result["url"],
                    "upload_record": upload_record,
                    "storage_status": self.check_storage_limit(),
                    "local_file_deleted": upload_record.get("local_file_deleted", False)
                }
            else:
                return {
                    "success": False,
                    "error": "Cloudflare upload failed",
                    "cloudflare_error": cloudflare_result.get("error")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "exception": "CloudflareStorageManager.upload_video_to_cloudflare"
            }
    
    def _simulate_cloudflare_upload(self, file_path: str, filename: str, file_size: int) -> Dict[str, Any]:
        """Simulate Cloudflare upload (replace with real API)"""
        try:
            # This would be replaced with actual Cloudflare API calls
            # For now, simulate successful upload
            cloudflare_id = f"cf_{int(time.time())}_{filename.replace('.', '_')}"
            
            # Simulate upload time based on file size
            upload_time = min(file_size / (10 * 1024 * 1024), 30)  # Max 30 seconds
            time.sleep(0.1)  # Simulate brief upload time
            
            return {
                "success": True,
                "cloudflare_id": cloudflare_id,
                "url": f"https://cloudflare.com/videos/{cloudflare_id}",
                "upload_time_seconds": upload_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _cleanup_oldest_video(self) -> Dict[str, Any]:
        """Remove oldest video from Cloudflare to make space"""
        try:
            oldest_videos = self._get_oldest_videos(1)
            
            if not oldest_videos:
                return {"success": False, "error": "No videos to cleanup"}
            
            oldest_video = oldest_videos[0]
            job_id = oldest_video["job_id"]
            cloudflare_id = oldest_video["cloudflare_id"]
            
            # Delete from Cloudflare
            delete_result = self._delete_from_cloudflare(cloudflare_id)
            
            if delete_result["success"]:
                # Remove from local records
                if job_id in self.storage_records:
                    del self.storage_records[job_id]
                    self._save_storage_records()
                
                print(f"[CLOUDFLARE] Cleaned up oldest video: {oldest_video['filename']}")
                
                return {
                    "success": True,
                    "deleted_job_id": job_id,
                    "deleted_cloudflare_id": cloudflare_id,
                    "deleted_filename": oldest_video["filename"],
                    "freed_space_mb": oldest_video["size_mb"]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to delete from Cloudflare",
                    "cloudflare_error": delete_result.get("error")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_video_from_cloudflare(self, job_id: str) -> Dict[str, Any]:
        """Manually delete specific video from Cloudflare"""
        try:
            if job_id not in self.storage_records:
                return {
                    "success": False,
                    "error": "Video not found in storage records"
                }
            
            record = self.storage_records[job_id]
            cloudflare_id = record["cloudflare_id"]
            
            # Delete from Cloudflare
            delete_result = self._delete_from_cloudflare(cloudflare_id)
            
            if delete_result["success"]:
                # Remove from local records
                del self.storage_records[job_id]
                self._save_storage_records()
                
                return {
                    "success": True,
                    "deleted_job_id": job_id,
                    "deleted_cloudflare_id": cloudflare_id,
                    "deleted_filename": record.get("filename"),
                    "freed_space_mb": record.get("size_mb", 0),
                    "storage_status": self.check_storage_limit()
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to delete from Cloudflare",
                    "cloudflare_error": delete_result.get("error")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _delete_from_cloudflare(self, cloudflare_id: str) -> Dict[str, Any]:
        """Delete video from Cloudflare (replace with real API)"""
        try:
            # This would be replaced with actual Cloudflare API calls
            # For now, simulate successful deletion
            time.sleep(0.1)  # Simulate API call
            
            return {
                "success": True,
                "cloudflare_id": cloudflare_id,
                "deleted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stored_videos(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of videos stored on Cloudflare"""
        videos = []
        
        for job_id, record in self.storage_records.items():
            videos.append({
                "job_id": job_id,
                "cloudflare_id": record["cloudflare_id"],
                "cloudflare_url": record["cloudflare_url"],
                "filename": record["filename"],
                "size_mb": record["size_mb"],
                "uploaded_at": record["uploaded_at"],
                "metadata": record.get("metadata", {})
            })
        
        # Sort by upload time (newest first)
        videos.sort(key=lambda x: x["uploaded_at"], reverse=True)
        
        return videos[:limit] if limit else videos
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        videos = list(self.storage_records.values())
        
        total_size = sum(v.get("size_mb", 0) for v in videos)
        avg_size = total_size / len(videos) if videos else 0
        
        # Upload timeline (last 7 days)
        now = datetime.now()
        recent_uploads = []
        
        for record in videos:
            upload_time = datetime.fromisoformat(record["uploaded_at"])
            days_ago = (now - upload_time).days
            if days_ago <= 7:
                recent_uploads.append(record)
        
        return {
            "total_videos": len(videos),
            "max_videos": self.max_videos,
            "available_slots": max(0, self.max_videos - len(videos)),
            "total_size_mb": round(total_size, 2),
            "average_video_size_mb": round(avg_size, 2),
            "storage_usage_percent": round((len(videos) / self.max_videos) * 100, 1),
            "recent_uploads_7_days": len(recent_uploads),
            "oldest_video": min(videos, key=lambda x: x["uploaded_at"]) if videos else None,
            "newest_video": max(videos, key=lambda x: x["uploaded_at"]) if videos else None,
            "storage_file_exists": os.path.exists(self.storage_file)
        }

# Global instance
_cloudflare_manager: Optional[CloudflareStorageManager] = None

def get_cloudflare_manager() -> CloudflareStorageManager:
    """Get global Cloudflare storage manager instance"""
    global _cloudflare_manager
    
    if _cloudflare_manager is None:
        _cloudflare_manager = CloudflareStorageManager()
    
    return _cloudflare_manager

if __name__ == "__main__":
    # Test the Cloudflare storage manager
    manager = CloudflareStorageManager(max_videos=5)  # Small limit for testing
    
    print("Testing Cloudflare Storage Manager...")
    
    # Check initial storage status
    status = manager.check_storage_limit()
    print(f"Initial storage status: {status}")
    
    # Simulate uploading videos
    for i in range(7):  # Upload more than limit to test cleanup
        job_id = f"test_job_{i}"
        
        # Create a fake video file path
        fake_video_path = f"fake_video_{i}.mp4"
        
        # Create fake file for testing
        with open(fake_video_path, 'w') as f:
            f.write("fake video content")
        
        print(f"\nUploading video {i+1}...")
        result = manager.upload_video_to_cloudflare(
            job_id, 
            fake_video_path,
            {"title": f"Test Video {i+1}", "domain": "test"}
        )
        
        print(f"Upload result: {result.get('success')}")
        if result.get("success"):
            print(f"Cloudflare URL: {result['cloudflare_url']}")
            print(f"Local file deleted: {result.get('local_file_deleted')}")
        
        # Show storage status
        storage_stats = manager.get_storage_stats()
        print(f"Storage: {storage_stats['total_videos']}/{storage_stats['max_videos']} videos")
    
    # Get final statistics
    final_stats = manager.get_storage_stats()
    print(f"\nFinal storage stats: {final_stats}")
    
    # List stored videos
    stored_videos = manager.get_stored_videos()
    print(f"\nStored videos: {len(stored_videos)}")
    for video in stored_videos:
        print(f"- {video['filename']} ({video['size_mb']} MB)")