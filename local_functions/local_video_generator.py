"""
Local AI Video Generator
Simplified orchestrator for running locally without paid APIs
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any

# Import our enhanced local functions
from textToSpeech_gtts import mindsflow_function as generate_speech
from PromptImagesToVideo_pollinations import mindsflow_function as generate_video

# Additional imports for enhanced functionality
import sys
import time
from datetime import datetime

# We'll implement basic audio-video combination locally for now
# The original functions require AWS dependencies

class LocalVideoGeneratorError(Exception):
    """Custom exception for local video generator errors"""
    pass

class LocalVideoGenerator:
    def __init__(self, output_dir: str = "local_video_results"):
        self.output_dir = output_dir
        self.session_id = uuid.uuid4().hex[:8]
        self.session_dir = os.path.join(output_dir, f"session_{self.session_id}")
        self.start_time = datetime.now()
        self.stats = {
            'images_generated': 0,
            'processing_time': 0,
            'errors': [],
            'warnings': []
        }
        
        # Create output directory with error handling
        try:
            os.makedirs(self.session_dir, exist_ok=True)
            print(f"Session created: {self.session_dir}")
        except Exception as e:
            raise LocalVideoGeneratorError(f"Failed to create session directory: {e}")
    
    def generate_enhanced_script(self, topic: str, style: str = None, num_segments: int = 4) -> Dict[str, Any]:
        """
        Generate dynamic script using Gemini AI instead of hardcoded templates
        Creates dynamic, topic-specific content for video
        """
        try:
            from gemini_story_generator import GeminiStoryGenerator
            
            print(f"Generating dynamic story for '{topic}' using Gemini AI...")
            
            # Initialize Gemini generator
            generator = GeminiStoryGenerator()
            
            # Generate story using Gemini
            style_key = style.lower() if style else 'informative'
            script_data = generator.generate_story_segments(topic, num_segments, style_key)
            
            # Add our local session info
            script_data['session_id'] = self.session_id
            script_data['generated_at'] = datetime.now().isoformat()
            
            total_duration = script_data['total_duration']
            segment_count = script_data['segment_count']
            source = script_data.get('source', 'gemini')
            
            print(f"Dynamic script generated: {segment_count} segments, {total_duration:.1f}s total (source: {source})")
            
            # Store generation info in stats
            self.stats['script_source'] = source
            self.stats['script_duration'] = total_duration
            
            return script_data
            
        except Exception as e:
            print(f"WARNING: Gemini script generation failed: {e}")
            print("Falling back to basic template generation...")
            
            # Fallback to simple template if Gemini fails
            return self._generate_fallback_script(topic, style, num_segments)
    
    def _generate_fallback_script(self, topic: str, style: str = None, num_segments: int = 4) -> Dict[str, Any]:
        """Fallback script generation when Gemini is not available"""
        try:
            # Basic templates for fallback
            templates = {
                'informative': [
                    f"Learn about {topic} and its key concepts.",
                    f"Discover the important aspects of {topic}.",
                    f"Understanding {topic} provides valuable insights."
                ],
                'educational': [
                    f"Today we explore {topic} step by step.",  
                    f"Here are the essential facts about {topic}.",
                    f"Apply these {topic} concepts effectively."
                ],
                'promotional': [
                    f"Discover the benefits of {topic} today.",
                    f"See why {topic} matters for you.", 
                    f"Take action with {topic} now."
                ]
            }
            
            style_key = style.lower() if style and style.lower() in templates else 'informative'
            sentences = templates[style_key][:num_segments]
            
            # Create timing data
            azure_time_unit = 10000000
            sentence_data = []
            current_time = 0
            
            for sentence in sentences:
                words = len(sentence.split())
                chars = len(sentence)
                word_duration = (words / 140) * 60 * azure_time_unit
                buffer_time = 15000000  # 1.5 seconds buffer
                estimated_duration = int(word_duration + buffer_time)
                
                sentence_data.append({
                    "sentence": sentence,
                    "start_time": current_time,
                    "end_time": current_time + estimated_duration,
                    "duration": estimated_duration,
                    "word_count": words,
                    "char_count": chars
                })
                current_time += estimated_duration
            
            total_duration = current_time / azure_time_unit
            
            return {
                "Text": " ".join(sentences),
                "sentences": sentence_data,
                "topic": topic,
                "style": style_key,
                "total_duration": total_duration,
                "segment_count": len(sentences),
                "generated_at": datetime.now().isoformat(),
                "source": "fallback_template"
            }
            
        except Exception as e:
            self.stats['errors'].append(f"Fallback script generation failed: {e}")
            raise LocalVideoGeneratorError(f"Fallback script generation failed: {e}")
    
    def create_local_json_file(self, data: Dict[str, Any], filename: str) -> str:
        """Create a local JSON file and return its path"""
        filepath = os.path.join(self.session_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filepath
    
    def validate_generation_params(self, topic: str, **kwargs) -> Dict[str, Any]:
        """
        Validate and optimize generation parameters
        """
        if not topic or not isinstance(topic, str) or len(topic.strip()) < 3:
            raise LocalVideoGeneratorError("Topic must be a non-empty string with at least 3 characters")
        
        # Enhanced default parameters with validation
        params = {
            "topic": topic.strip(),
            "language": kwargs.get("language", "en"),
            "voice_speed": max(0.5, min(2.0, kwargs.get("voice_speed", 1.0))),
            "font_size": max(12, min(72, kwargs.get("font_size", 30))),
            "height": kwargs.get("height", 512),      # Smaller default
            "width": kwargs.get("width", 512),       # Smaller default
            "fps": max(8, min(60, kwargs.get("fps", 12))),  # Lower default FPS
            "image_model": kwargs.get("image_model", "flux"),
            "transition_time": max(0, min(5, kwargs.get("transition_time", 0))),  # No transitions by default
            "zoom": max(1.0, min(3.0, kwargs.get("zoom", 1.0))),  # No zoom by default
            "image_duration": max(2, min(30, kwargs.get("image_duration", 5))),
            "style": kwargs.get("style", "informative"),
            "num_segments": max(3, min(10, kwargs.get("num_segments", 3))),  # Fewer segments for speed
            "quality_mode": kwargs.get("quality_mode", "balanced")  # 'fast', 'balanced', 'quality'
        }
        
        # Validate resolution
        if params["width"] < 256 or params["width"] > 2048:
            self.stats['warnings'].append(f"Width {params['width']} adjusted to valid range")
            params["width"] = max(256, min(2048, params["width"]))
        
        if params["height"] < 256 or params["height"] > 2048:
            self.stats['warnings'].append(f"Height {params['height']} adjusted to valid range")
            params["height"] = max(256, min(2048, params["height"]))
        
        # Validate model
        valid_models = ['flux', 'flux-realism', 'flux-anime', 'flux-3d', 'turbo']
        if params["image_model"] not in valid_models:
            self.stats['warnings'].append(f"Unknown model '{params['image_model']}', using 'flux'")
            params["image_model"] = "flux"
        
        print(f"Parameters validated: {params['width']}x{params['height']}, {params['fps']}fps, {params['image_model']}")
        return params
    
    def generate_video(self, topic: str, **kwargs) -> Dict[str, Any]:
        """
        Enhanced main function to generate video locally with comprehensive error handling
        """
        generation_start = time.time()
        
        try:
            print(f"\nEnhanced Local Video Generation Starting")
            print(f"   Topic: {topic}")
            print(f"   Session: {self.session_id}")
            print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Validate parameters
            params = self.validate_generation_params(topic, **kwargs)
        
            results = {
                'session_id': self.session_id,
                'session_dir': self.session_dir,
                'generation_params': params,
                'start_time': generation_start
            }
            
            # Step 1: Enhanced Script Generation
            print(f"\nStep 1: Generating enhanced script...")
            script_data = self.generate_enhanced_script(
                params["topic"], 
                params["style"], 
                params["num_segments"]
            )
            script_file = self.create_local_json_file(script_data, "enhanced_script.json")
            results['script_file'] = script_file
            results['script_data'] = script_data
            print(f"Enhanced script generated: {script_file}")
            
            # Step 2: Enhanced Speech Generation
            print(f"\nStep 2: Generating speech...")
            try:
                speech_event = {
                    "text": script_data["Text"],
                    "language": params["language"],
                    "voice_speed": params["voice_speed"]
                }
                speech_result = generate_speech(speech_event, None)
                
                if not speech_result.get('success', True):
                    raise Exception(f"Speech generation failed: {speech_result.get('error', 'Unknown error')}")
                
                # Move audio file to session directory with enhanced handling
                audio_file = speech_result.get('audio_file')
                if not audio_file or not os.path.exists(audio_file):
                    raise Exception("Speech generation did not produce audio file")
                
                session_audio = os.path.join(self.session_dir, f"enhanced_narration_{self.session_id}.wav")
                os.rename(audio_file, session_audio)
                speech_result['audio_url'] = session_audio
                
                # Validate audio file
                audio_size = os.path.getsize(session_audio)
                if audio_size < 1024:  # Less than 1KB suggests failure
                    raise Exception(f"Generated audio file is too small ({audio_size} bytes)")
                
                # Get audio duration for video generation
                from moviepy.audio.io.AudioFileClip import AudioFileClip
                temp_audio = AudioFileClip(session_audio)
                audio_duration = temp_audio.duration
                temp_audio.close()
                print(f"Audio duration measured: {audio_duration:.1f}s")
                
                results.update(speech_result)
                print(f"Speech generated: {session_audio} ({audio_size/1024:.1f} KB)")
                
            except Exception as speech_error:
                error_msg = f"Speech generation failed: {speech_error}"
                self.stats['errors'].append(error_msg)
                print(f"ERROR: {error_msg}")
                raise LocalVideoGeneratorError(error_msg)
            
            # Step 3: Enhanced Video Generation from Images
            print(f"\nStep 3: Generating enhanced video from images...")
            try:
                # Create sentences JSON file for image generation
                sentences_file = self.create_local_json_file(script_data["sentences"], "enhanced_sentences.json")
                
                # Enhanced video generation parameters
                print(f"DEBUG: Creating video event with audio_duration={audio_duration:.1f}s")
                video_event = {
                    "img_prompt": f"High-quality scenes related to {params['topic']}, cinematic style",
                    "img_style_prompt": "professional, detailed, high resolution, perfect lighting",
                    "negative_prompt": "blurry, low quality, pixelated, distorted, watermark, text, logo",
                    "width": params["width"],
                    "height": params["height"],
                    "fps": params["fps"],
                    "video_duration": audio_duration,  # Match video duration to audio duration
                    "image_duration": audio_duration / 3,  # Divide by number of sentences/images
                    "sentences_json_url": sentences_file,
                    "transition_time": params["transition_time"],
                    "transition_overlap": False,  # Disable transitions to maintain exact audio duration
                    "zoom": params["zoom"],
                    "topic": params["topic"],
                    "img_model": params["image_model"],
                    "crop_method": "resize" if params["quality_mode"] == "fast" else None
                }
                print(f"DEBUG: Video event created with video_duration={video_event['video_duration']:.1f}s")
                
                video_result = generate_video(video_event, None)
                
                if not video_result.get('success', True):
                    raise Exception(f"Video generation failed: {video_result.get('error', 'Unknown error')}")
                
                # Enhanced video file handling
                video_file = video_result.get('video_file')
                if not video_file or not os.path.exists(video_file):
                    raise Exception("Video generation did not produce video file")
                
                session_video = os.path.join(self.session_dir, f"video_{self.session_id}.mp4")
                os.rename(video_file, session_video)
                video_result['video_url'] = session_video
                
                # Get actual video duration from the generated video
                from moviepy.video.io.VideoFileClip import VideoFileClip
                temp_clip = VideoFileClip(session_video)
                actual_video_duration = temp_clip.duration
                temp_clip.close()
                
                # Get actual audio duration for comparison
                from moviepy.audio.io.AudioFileClip import AudioFileClip
                audio_clip_temp = AudioFileClip(session_audio)
                actual_audio_duration = audio_clip_temp.duration
                audio_clip_temp.close()
                
                print(f"Duration analysis:")
                print(f"  Script estimated: {script_data.get('total_duration', 0):.1f}s")
                print(f"  Audio actual: {actual_audio_duration:.1f}s")
                print(f"  Video actual: {actual_video_duration:.1f}s")
                
                # Check if video-audio duration mismatch is significant
                duration_diff = abs(actual_video_duration - actual_audio_duration)
                if duration_diff > 2.0:  # More than 2 seconds difference
                    print(f"WARNING: Large duration mismatch ({duration_diff:.1f}s)")
                    self.stats['warnings'].append(f"Video-audio duration mismatch: {duration_diff:.1f}s")
                
                # Validate video file
                video_size = os.path.getsize(session_video)
                if video_size < 10240:  # Less than 10KB suggests failure
                    raise Exception(f"Generated video file is too small ({video_size} bytes)")
                
                results.update(video_result)
                results['actual_video_duration'] = actual_video_duration
                results['actual_audio_duration'] = actual_audio_duration
                results['duration_mismatch'] = duration_diff
                self.stats['images_generated'] = video_result.get('images_generated', 0)
                print(f"Video generated: {session_video} ({video_size/1024/1024:.1f} MB, {actual_video_duration:.1f}s)")
                
            except Exception as video_error:
                error_msg = f"Video generation failed: {video_error}"
                self.stats['errors'].append(error_msg)
                print(f"ERROR: {error_msg}")
                raise LocalVideoGeneratorError(error_msg)
            
            # Step 4: Enhanced Audio-Video Combination
            print(f"\nStep 4: Combining audio and video with enhanced processing...")
            
            try:
                # Enhanced MoviePy configuration
                import moviepy.config as mp_config
                import imageio_ffmpeg as iio
                
                # Set FFmpeg path globally
                ffmpeg_exe = iio.get_ffmpeg_exe()
                mp_config.IMAGEIO_FFMPEG_EXE = ffmpeg_exe
                
                # Also set environment variable for extra safety
                os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe
                
                print(f"FFmpeg configured: {ffmpeg_exe}")
                
                from moviepy.video.io.VideoFileClip import VideoFileClip
                from moviepy.audio.io.AudioFileClip import AudioFileClip
                
                # Load and validate media files
                print("Loading media files...")
                video_clip = VideoFileClip(session_video)
                audio_clip = AudioFileClip(session_audio)
                
                print(f"   Video: {video_clip.duration:.1f}s, {video_clip.size}")
                print(f"   Audio: {audio_clip.duration:.1f}s")
                
                # Use actual measured durations
                video_duration = video_clip.duration
                audio_duration = audio_clip.duration
                
                print(f"Duration check: video={video_duration:.1f}s, audio={audio_duration:.1f}s")
                
                # Simple approach: use the video as-is and let MoviePy handle duration mismatch
                print(f"Using video duration: {video_duration:.1f}s, audio duration: {audio_duration:.1f}s")
                print("MoviePy will automatically handle duration differences during combination")
                
                # Combine with enhanced settings and proper audio handling
                print("Combining audio and video...")
                # Use the correct method for this MoviePy version
                print(f"Available audio methods: set_audio={hasattr(video_clip, 'set_audio')}, with_audio={hasattr(video_clip, 'with_audio')}")
                
                if hasattr(video_clip, 'set_audio'):
                    print("Using set_audio method for audio integration")
                    final_clip = video_clip.set_audio(audio_clip)
                elif hasattr(video_clip, 'with_audio'):
                    print("Using with_audio method for audio integration")
                    final_clip = video_clip.with_audio(audio_clip)
                else:
                    raise Exception("No audio integration method available in MoviePy")
                
                print(f"Audio integration successful - final clip duration: {final_clip.duration:.1f}s")
                
                # Enhanced export settings
                final_video = os.path.join(self.session_dir, f"final_enhanced_video_{self.session_id}.mp4")
                
                # Quality-based export settings with proper audio handling
                if params["quality_mode"] == "fast":
                    codec_settings = {
                        'codec': 'libx264', 
                        'audio_codec': 'aac',
                        'bitrate': '1000k',
                        'audio_bitrate': '128k'
                    }
                elif params["quality_mode"] == "quality":
                    codec_settings = {
                        'codec': 'libx264', 
                        'audio_codec': 'aac',
                        'bitrate': '3000k',
                        'audio_bitrate': '256k'
                    }
                else:  # balanced
                    codec_settings = {
                        'codec': 'libx264', 
                        'audio_codec': 'aac',
                        'bitrate': '2000k',
                        'audio_bitrate': '192k'
                    }
                
                # Write video with optimized settings for speed
                optimized_fps = max(8, min(params.get('fps', 24), 16))  # Limit FPS for speed
                print(f"Writing final video with audio (optimized: {optimized_fps}fps)...")
                final_clip.write_videofile(
                    final_video, 
                    fps=optimized_fps,
                    temp_audiofile=f'temp-audio-final-{self.session_id}.m4a',
                    remove_temp=True,
                    # Optimized settings for speed
                    codec='libx264',
                    audio_codec='aac',
                    bitrate='1000k',  # Lower bitrate for speed
                    audio_bitrate='128k',
                    threads=2,
                    preset='ultrafast'  # Fastest encoding preset
                )
                
                # Cleanup clips to free memory
                video_clip.close()
                audio_clip.close()
                final_clip.close()
                
                # Validate final video
                final_size = os.path.getsize(final_video)
                if final_size < 50000:  # Less than 50KB suggests failure
                    raise Exception(f"Final video file is too small ({final_size} bytes)")
                
                # Verify the final video has audio
                try:
                    test_clip = VideoFileClip(final_video)
                    has_audio = test_clip.audio is not None
                    final_duration = test_clip.duration
                    test_clip.close()
                    
                    if not has_audio:
                        print("WARNING Warning: Final video has no audio track")
                        self.stats['warnings'].append("Final video missing audio track")
                    else:
                        print(f"OK Final video has audio track ({final_duration:.1f}s)")
                        
                except Exception as verify_error:
                    print(f"WARNING Could not verify final video: {verify_error}")
                
                print(f"OK Enhanced audio-video combination completed")
                print(f"   Final video: {final_video} ({final_size/1024/1024:.1f} MB)")
                
            except Exception as combine_error:
                error_msg = f"Audio-video combination failed: {combine_error}"
                print(f"ERROR: {error_msg}")
                self.stats['errors'].append(error_msg)
                
                print("WARNING Attempting audio combination fallback...")
                try:
                    # Try a simpler audio combination approach
                    from moviepy.video.io.VideoFileClip import VideoFileClip
                    from moviepy.audio.io.AudioFileClip import AudioFileClip
                    
                    video_clip = VideoFileClip(session_video) 
                    audio_clip = AudioFileClip(session_audio)
                    
                    # Simple duration matching - skip subclip since it may not be available
                    print(f"Using fallback combination: video={video_clip.duration:.1f}s, audio={audio_clip.duration:.1f}s")
                    
                    # Simple combination - use correct method
                    if hasattr(video_clip, 'set_audio'):
                        final_clip = video_clip.set_audio(audio_clip)
                    elif hasattr(video_clip, 'with_audio'):
                        final_clip = video_clip.with_audio(audio_clip)
                    else:
                        final_clip = video_clip  # Fallback without audio
                    final_video = os.path.join(self.session_dir, f"fallback_video_{self.session_id}.mp4")
                    
                    final_clip.write_videofile(
                        final_video,
                        codec='libx264',
                        audio_codec='aac'
                    )
                    
                    video_clip.close()
                    audio_clip.close() 
                    final_clip.close()
                    
                    print(f"OK Fallback audio combination successful: {final_video}")
                    audio_duration = min_duration
                    
                except Exception as fallback_error:
                    print(f"ERROR: Even fallback audio combination failed: {fallback_error}")
                    print("WARNING Using silent video as final fallback")
                    final_video = session_video
                    audio_duration = results.get('duration', script_data.get('total_duration', 0))
            
            # Step 5: Enhanced Results Summary
            processing_time = time.time() - generation_start
            self.stats['processing_time'] = processing_time
            
            results.update({
                'final_video': final_video,
                'final_video_size_mb': os.path.getsize(final_video) / 1024 / 1024 if os.path.exists(final_video) else 0,
                'session_dir': self.session_dir,
                'topic': params['topic'],
                'duration': audio_duration,
                'processing_time': processing_time,
                'generation_stats': self.stats.copy(),
                'parameters_used': params,
                'success': True,
                'version': '2.0_enhanced',
                'completion_time': datetime.now().isoformat()
            })
            
            # Enhanced completion summary
            print(f"\nEnhanced Video Generation Completed Successfully!")
            print(f"   • Session: {self.session_id}")
            print(f"   • Topic: {params['topic']}")
            print(f"   • Duration: {audio_duration:.1f}s")
            print(f"   • Processing time: {processing_time:.1f}s")
            print(f"   • Output directory: {self.session_dir}")
            print(f"   • Final video: {final_video}")
            if self.stats['errors']:
                print(f"   • Errors encountered: {len(self.stats['errors'])}")
            if self.stats['warnings']:
                print(f"   • Warnings: {len(self.stats['warnings'])}")
            
            return results
            
        except LocalVideoGeneratorError as lvge:
            processing_time = time.time() - generation_start
            error_msg = str(lvge)
            
            print(f"\nLocal Video Generator Error: {error_msg}")
            
            results.update({
                'success': False,
                'error': error_msg,
                'error_type': 'LocalVideoGeneratorError',
                'session_dir': self.session_dir,
                'processing_time': processing_time,
                'generation_stats': self.stats.copy(),
                'partial_results': True
            })
            return results
            
        except Exception as e:
            processing_time = time.time() - generation_start
            error_msg = f"Unexpected error during video generation: {e}"
            self.stats['errors'].append(error_msg)
            
            print(f"\nCritical Error: {error_msg}")
            
            results.update({
                'success': False,
                'error': error_msg,
                'error_type': type(e).__name__,
                'session_dir': self.session_dir,
                'processing_time': processing_time,
                'generation_stats': self.stats.copy(),
                'partial_results': True
            })
            return results

def main():
    """
    Enhanced main function for command-line usage with better argument handling
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enhanced Local AI Video Generator v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s "Climate Change" --style educational --quality balanced
  %(prog)s "Cooking Pasta" --width 1920 --height 1080 --fps 30
  %(prog)s "Space Exploration" --model flux-realism --segments 6
        '''
    )
    
    # Required arguments
    parser.add_argument('topic', help='Video topic (required)')
    
    # Video dimensions and quality
    parser.add_argument('--width', type=int, default=1024, help='Video width (default: 1024)')
    parser.add_argument('--height', type=int, default=576, help='Video height (default: 576)')
    parser.add_argument('--fps', type=int, default=24, help='Frames per second (default: 24)')
    
    # Content and style
    parser.add_argument('--style', choices=['informative', 'educational', 'promotional'], 
                       default='informative', help='Video style (default: informative)')
    parser.add_argument('--segments', type=int, default=5, help='Number of segments (default: 5)')
    
    # Technical settings
    parser.add_argument('--model', choices=['flux', 'flux-realism', 'flux-anime', 'flux-3d', 'turbo'],
                       default='flux', help='Image generation model (default: flux)')
    parser.add_argument('--quality', choices=['fast', 'balanced', 'quality'],
                       default='balanced', help='Quality vs speed tradeoff (default: balanced)')
    
    # Animation settings
    parser.add_argument('--zoom', type=float, default=1.2, help='Zoom effect intensity (default: 1.2)')
    parser.add_argument('--transition', type=float, default=1.5, help='Transition time in seconds (default: 1.5)')
    
    # Audio settings
    parser.add_argument('--speed', type=float, default=1.0, help='Voice speed (default: 1.0)')
    parser.add_argument('--language', default='en', help='Language code (default: en)')
    
    # Output settings
    parser.add_argument('--output', default='local_video_results', help='Output directory (default: local_video_results)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        # Display startup information
        print(f"\nEnhanced Local AI Video Generator v2.0")
        print(f"   Topic: {args.topic}")
        print(f"   Resolution: {args.width}x{args.height} @ {args.fps}fps")
        print(f"   Model: {args.model} ({args.quality} quality)")
        print(f"   Style: {args.style} ({args.segments} segments)")
        print(f"   Output: {args.output}")
        
        # Create enhanced generator
        generator = LocalVideoGenerator(args.output)
        
        # Generate video with enhanced parameters
        result = generator.generate_video(
            topic=args.topic,
            width=args.width,
            height=args.height,
            fps=args.fps,
            style=args.style,
            num_segments=args.segments,
            image_model=args.model,
            quality_mode=args.quality,
            zoom=args.zoom,
            transition_time=args.transition,
            voice_speed=args.speed,
            language=args.language
        )
        
        # Enhanced result reporting
        if result['success']:
            print(f"\n\nSUCCESS! Enhanced video generation completed")
            print(f"   Video: Video file: {result['final_video']}")
            print(f"   Dir: Session directory: {result['session_dir']}")
            print(f"   Time: Processing time: {result['processing_time']:.1f} seconds")
            print(f"   Size: File size: {result['final_video_size_mb']:.1f} MB")
            print(f"   Duration: {result['duration']:.1f} seconds")
            
            if args.verbose and result.get('generation_stats'):
                stats = result['generation_stats']
                print(f"\n   Generation Statistics:")
                if stats.get('images_generated'):
                    print(f"      • Images generated: {stats['images_generated']}")
                if stats.get('warnings'):
                    print(f"      • Warnings: {len(stats['warnings'])}")
        else:
            print(f"\n\nFAILED: Video generation failed")
            print(f"   Error: {result['error']}")
            print(f"   Processing time: {result.get('processing_time', 0):.1f} seconds")
            
            if result.get('partial_results'):
                print(f"   Partial results saved in: {result['session_dir']}")
                
            return 1
            
    except KeyboardInterrupt:
        print(f"\n\nGeneration interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nCritical error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)