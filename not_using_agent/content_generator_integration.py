#!/usr/bin/env python3
"""
Content Generator Integration - Connects daily news to your content generation system
This is a template that you can customize to match your existing generation script
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class ContentGenerator:
    """
    Integration class for your content generation system
    Customize this to match your existing generation script
    """
    
    def __init__(self):
        self.setup_logging()
        self.output_dir = Path("generated_content")
        self.output_dir.mkdir(exist_ok=True)
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def generate_content(self, title: str, source: str = "ABP Live") -> Dict[str, Any]:
        """
        Generate content based on news title
        
        Args:
            title: News headline/title
            source: Source of the news
            
        Returns:
            Dictionary with generation results
        """
        self.logger.info(f"Generating content for: {title}")
        
        try:
            # 1. Prepare the prompt/input for your generation system
            generation_input = self.prepare_generation_input(title, source)
            
            # 2. Call your actual generation method
            # Replace this with your actual content generation logic
            generated_content = self.call_your_generation_method(generation_input)
            
            # 3. Save the generated content
            output_file = self.save_generated_content(title, generated_content)
            
            result = {
                'status': 'success',
                'title': title,
                'source': source,
                'output_file': str(output_file),
                'generated_at': datetime.now().isoformat(),
                'content_preview': generated_content.get('preview', '')
            }
            
            self.logger.info(f"Successfully generated content for: {title}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate content for '{title}': {e}")
            return {
                'status': 'error',
                'title': title,
                'source': source,
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def prepare_generation_input(self, title: str, source: str) -> Dict[str, Any]:
        """
        Prepare input for your generation system
        Customize this based on your generation script requirements
        """
        
        # Example input structure - customize this for your needs
        generation_input = {
            'headline': title,
            'source': source,
            'type': 'news_story',
            'style': 'engaging',
            'length': 'medium',  # or 'short', 'long'
            'format': 'story',   # or 'article', 'script', etc.
            'timestamp': datetime.now().isoformat()
        }
        
        # Add category-specific instructions
        category = self.detect_category(title)
        generation_input['category'] = category
        generation_input['instructions'] = self.get_category_instructions(category)
        
        return generation_input
    
    def detect_category(self, title: str) -> str:
        """Detect content category from title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['breaking', 'urgent', 'alert']):
            return 'breaking_news'
        elif any(word in title_lower for word in ['politics', 'government', 'minister', 'parliament']):
            return 'politics'
        elif any(word in title_lower for word in ['temple', 'devotee', 'religious', 'festival']):
            return 'religion_culture'
        elif any(word in title_lower for word in ['security', 'border', 'military', 'terrorism']):
            return 'security'
        else:
            return 'general'
    
    def get_category_instructions(self, category: str) -> str:
        """Get generation instructions based on category"""
        instructions = {
            'breaking_news': "Create an urgent, attention-grabbing story with latest updates and key facts.",
            'politics': "Provide balanced coverage with multiple perspectives and factual analysis.",
            'religion_culture': "Write respectfully about cultural and religious events with appropriate context.",
            'security': "Focus on factual reporting while being sensitive to security implications.",
            'general': "Create engaging content that informs and entertains the audience."
        }
        
        return instructions.get(category, instructions['general'])
    
    def call_your_generation_method(self, generation_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call your actual content generation method
        
        CUSTOMIZE THIS METHOD TO CALL YOUR EXISTING GENERATION SCRIPT
        """
        
        # Option 1: If you have a Python function/module
        # try:
        #     from your_generation_module import generate_story
        #     result = generate_story(
        #         prompt=generation_input['headline'],
        #         category=generation_input['category'],
        #         instructions=generation_input['instructions']
        #     )
        #     return result
        # except ImportError:
        #     pass
        
        # Option 2: If you have a command-line script
        # try:
        #     import subprocess
        #     import tempfile
        #     
        #     # Save input to temp file
        #     with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        #         json.dump(generation_input, f)
        #         input_file = f.name
        #     
        #     # Call your script
        #     cmd = [
        #         sys.executable,
        #         'path/to/your/generation_script.py',
        #         '--input', input_file
        #     ]
        #     
        #     result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        #     
        #     if result.returncode == 0:
        #         # Parse output from your script
        #         output_data = json.loads(result.stdout)
        #         return output_data
        #     else:
        #         raise Exception(f"Script failed: {result.stderr}")
        # 
        # except Exception as e:
        #     self.logger.error(f"External script call failed: {e}")
        
        # Option 3: Mock generation for testing (remove this in production)
        self.logger.info("Using mock content generation (replace with your actual method)")
        
        mock_content = {
            'title': generation_input['headline'],
            'story': self.generate_mock_story(generation_input),
            'preview': f"Story about: {generation_input['headline'][:100]}...",
            'word_count': 250,
            'category': generation_input['category']
        }
        
        return mock_content
    
    def generate_mock_story(self, generation_input: Dict[str, Any]) -> str:
        """
        Generate a mock story for testing
        REMOVE THIS IN PRODUCTION AND USE YOUR ACTUAL GENERATION METHOD
        """
        headline = generation_input['headline']
        category = generation_input['category']
        instructions = generation_input['instructions']
        
        mock_story = f"""
**{headline}**

In a developing story from {generation_input['source']}, recent events have unfolded that capture public attention.

{instructions}

This {category} story highlights important aspects that resonate with audiences nationwide. The situation continues to evolve, and updates are expected as more information becomes available.

Key points to consider:
- The significance of this development
- Impact on various stakeholders
- Broader implications for the region
- Public response and reactions

As this story develops, we will continue to monitor the situation and provide timely updates to keep our audience informed.

---
Generated by Content Generation System
Category: {category}
Source: {generation_input['source']}
Generated at: {generation_input['timestamp']}
"""
        
        return mock_story.strip()
    
    def save_generated_content(self, title: str, content: Dict[str, Any]) -> Path:
        """Save generated content to file"""
        # Create safe filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:50]  # Limit length
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_title}_{timestamp}.json"
        
        output_file = self.output_dir / filename
        
        # Save complete content data
        content_data = {
            'original_title': title,
            'generated_content': content,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'filename': filename,
                'category': content.get('category', 'general')
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, indent=2, ensure_ascii=False)
        
        # Also save a readable text version
        text_file = output_file.with_suffix('.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write("=" * 50 + "\n\n")
            f.write(content.get('story', content.get('text', 'No content generated')))
            f.write("\n\n" + "=" * 50 + "\n")
            f.write(f"Generated at: {datetime.now()}\n")
        
        self.logger.info(f"Saved content to: {output_file}")
        return output_file


def main():
    """
    Main function - can be called from daily news uploader
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Content Generator Integration")
    parser.add_argument('--title', required=True, help='News title to generate content for')
    parser.add_argument('--source', default='ABP Live', help='News source')
    parser.add_argument('--output', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    generator = ContentGenerator()
    
    result = generator.generate_content(args.title, args.source)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print result for the calling script
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0 if result['status'] == 'success' else 1


if __name__ == "__main__":
    sys.exit(main())