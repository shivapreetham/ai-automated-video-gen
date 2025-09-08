"""
Cleanup Utilities for AI Video Generator
Handles automatic cleanup of result folders and temporary files
"""

import os
import shutil
import time
import glob
from typing import List, Dict, Any
from datetime import datetime, timedelta

def cleanup_result_folder(output_dir: str, keep_final_video: bool = True) -> bool:
    """
    Clean up a specific result folder
    
    Args:
        output_dir: Path to the result folder to clean up
        keep_final_video: Whether to keep the final video file for download
    
    Returns:
        bool: True if cleanup was successful
    """
    try:
        if not os.path.exists(output_dir):
            print(f"[CLEANUP] Directory {output_dir} doesn't exist, nothing to clean")
            return True
        
        print(f"[CLEANUP] Starting cleanup of {output_dir}")
        
        if keep_final_video:
            # Find and preserve the final video file temporarily
            final_video_files = []
            for ext in ['*.mp4', '*.avi', '*.mov']:
                pattern = os.path.join(output_dir, f"*final*{ext}")
                final_video_files.extend(glob.glob(pattern))
            
            # Also check for any video file that might be the final one
            if not final_video_files:
                pattern = os.path.join(output_dir, "*.mp4")
                all_videos = glob.glob(pattern)
                if all_videos:
                    # Get the largest video file (likely the final one)
                    final_video_files = [max(all_videos, key=os.path.getsize)]
            
            # Move final video to temp location
            temp_videos = []
            for video_file in final_video_files:
                temp_name = f"{video_file}.temp_keep"
                try:
                    shutil.move(video_file, temp_name)
                    temp_videos.append((temp_name, video_file))
                    print(f"[CLEANUP] Temporarily preserved: {os.path.basename(video_file)}")
                except Exception as e:
                    print(f"[CLEANUP] Warning: Could not preserve {video_file}: {e}")
        
        # Remove the entire directory
        shutil.rmtree(output_dir)
        print(f"[CLEANUP] Removed directory: {output_dir}")
        
        if keep_final_video and temp_videos:
            # Recreate directory and restore final videos
            os.makedirs(output_dir, exist_ok=True)
            for temp_name, original_name in temp_videos:
                try:
                    shutil.move(temp_name, original_name)
                    print(f"[CLEANUP] Restored final video: {os.path.basename(original_name)}")
                except Exception as e:
                    print(f"[CLEANUP] Warning: Could not restore {original_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"[CLEANUP] Error cleaning up {output_dir}: {e}")
        return False

def cleanup_old_results(max_age_hours: int = 24, results_base_dir: str = "results") -> int:
    """
    Clean up old result folders that are older than specified hours
    
    Args:
        max_age_hours: Maximum age in hours before cleanup
        results_base_dir: Base directory containing result folders
    
    Returns:
        int: Number of folders cleaned up
    """
    try:
        if not os.path.exists(results_base_dir):
            print(f"[CLEANUP] Results directory {results_base_dir} doesn't exist")
            return 0
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        print(f"[CLEANUP] Scanning for result folders older than {max_age_hours} hours...")
        
        for folder_name in os.listdir(results_base_dir):
            folder_path = os.path.join(results_base_dir, folder_name)
            
            if not os.path.isdir(folder_path):
                continue
            
            # Check folder creation time
            folder_creation_time = datetime.fromtimestamp(os.path.getctime(folder_path))
            
            if folder_creation_time < cutoff_time:
                print(f"[CLEANUP] Found old folder: {folder_name} (created: {folder_creation_time})")
                if cleanup_result_folder(folder_path, keep_final_video=False):
                    cleaned_count += 1
        
        print(f"[CLEANUP] Cleaned up {cleaned_count} old result folders")
        return cleaned_count
        
    except Exception as e:
        print(f"[CLEANUP] Error during old results cleanup: {e}")
        return 0

def cleanup_temporary_files(base_dir: str = ".") -> int:
    """
    Clean up temporary files like audio, image temp files, etc.
    
    Args:
        base_dir: Base directory to scan for temp files
    
    Returns:
        int: Number of files cleaned up
    """
    try:
        temp_patterns = [
            "temp_*.mp3",
            "temp_*.wav", 
            "temp_*.png",
            "temp_*.jpg",
            "temp_*.mp4",
            "fallback_*.png",
            "segment_*_temp.*",
            "silent_audio_*.wav",
            "*_temp_*.*"
        ]
        
        cleaned_count = 0
        print(f"[CLEANUP] Scanning for temporary files in {base_dir}...")
        
        for pattern in temp_patterns:
            files = glob.glob(os.path.join(base_dir, pattern))
            for file_path in files:
                try:
                    # Only clean files older than 1 hour
                    file_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_age > timedelta(hours=1):
                        os.remove(file_path)
                        print(f"[CLEANUP] Removed temp file: {os.path.basename(file_path)}")
                        cleaned_count += 1
                except Exception as e:
                    print(f"[CLEANUP] Could not remove {file_path}: {e}")
        
        print(f"[CLEANUP] Cleaned up {cleaned_count} temporary files")
        return cleaned_count
        
    except Exception as e:
        print(f"[CLEANUP] Error during temp file cleanup: {e}")
        return 0

def auto_cleanup_after_upload(output_dir: str, upload_success: bool) -> bool:
    """
    Automatically clean up result folder after successful upload to Cloudflare
    
    Args:
        output_dir: Path to the result folder
        upload_success: Whether the upload was successful
    
    Returns:
        bool: True if cleanup was performed
    """
    if upload_success:
        print(f"[CLEANUP] Upload successful, cleaning up result folder...")
        # Give a small delay to ensure upload is complete
        time.sleep(2)
        return cleanup_result_folder(output_dir, keep_final_video=True)
    else:
        print(f"[CLEANUP] Upload failed, keeping result folder for debugging")
        return False

def get_cleanup_stats(results_base_dir: str = "results") -> Dict[str, Any]:
    """
    Get statistics about result folders for cleanup decisions
    
    Args:
        results_base_dir: Base directory containing result folders
    
    Returns:
        dict: Statistics about result folders
    """
    try:
        if not os.path.exists(results_base_dir):
            return {"total_folders": 0, "total_size_mb": 0, "oldest_folder": None}
        
        stats = {
            "total_folders": 0,
            "total_size_mb": 0,
            "oldest_folder": None,
            "newest_folder": None,
            "large_folders": []
        }
        
        oldest_time = None
        newest_time = None
        
        for folder_name in os.listdir(results_base_dir):
            folder_path = os.path.join(results_base_dir, folder_name)
            
            if not os.path.isdir(folder_path):
                continue
            
            stats["total_folders"] += 1
            
            # Calculate folder size
            folder_size = 0
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        folder_size += os.path.getsize(filepath)
                    except:
                        pass
            
            folder_size_mb = folder_size / (1024 * 1024)
            stats["total_size_mb"] += folder_size_mb
            
            # Track large folders (>50MB)
            if folder_size_mb > 50:
                stats["large_folders"].append({
                    "name": folder_name,
                    "size_mb": round(folder_size_mb, 2)
                })
            
            # Track oldest and newest folders
            folder_time = datetime.fromtimestamp(os.path.getctime(folder_path))
            
            if oldest_time is None or folder_time < oldest_time:
                oldest_time = folder_time
                stats["oldest_folder"] = {
                    "name": folder_name,
                    "created": folder_time.isoformat()
                }
            
            if newest_time is None or folder_time > newest_time:
                newest_time = folder_time
                stats["newest_folder"] = {
                    "name": folder_name,
                    "created": folder_time.isoformat()
                }
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats
        
    except Exception as e:
        print(f"[CLEANUP] Error getting cleanup stats: {e}")
        return {"error": str(e)}

# Background cleanup function for scheduled runs
def scheduled_cleanup():
    """
    Run scheduled cleanup tasks
    This can be called periodically to maintain system cleanliness
    """
    print(f"[CLEANUP] Starting scheduled cleanup at {datetime.now()}")
    
    # Clean up old result folders (older than 24 hours)
    old_folders_cleaned = cleanup_old_results(max_age_hours=24)
    
    # Clean up temporary files
    temp_files_cleaned = cleanup_temporary_files()
    
    # Get current stats
    stats = get_cleanup_stats()
    
    print(f"[CLEANUP] Scheduled cleanup complete:")
    print(f"  - Old folders cleaned: {old_folders_cleaned}")
    print(f"  - Temp files cleaned: {temp_files_cleaned}")
    print(f"  - Current result folders: {stats.get('total_folders', 0)}")
    print(f"  - Total storage used: {stats.get('total_size_mb', 0):.2f} MB")
    
    return {
        "old_folders_cleaned": old_folders_cleaned,
        "temp_files_cleaned": temp_files_cleaned,
        "current_stats": stats
    }

if __name__ == "__main__":
    # Run cleanup when script is executed directly
    scheduled_cleanup()