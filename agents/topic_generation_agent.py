"""
Topic Generation Agent
Automatically generates relevant topics based on given domains
"""

import os
import json
import random
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class GeneratedTopic:
    """Represents a generated topic"""
    topic: str
    domain: str
    subtopics: List[str]
    estimated_interest: float
    keywords: List[str]
    generated_at: datetime
    used: bool = False

class TopicGenerationAgent:
    """
    Autonomous agent that generates topics based on domains
    """
    
    def __init__(self):
        self.topic_templates = {
            "indian_mythology": [
                "The untold story of {character} and their journey",
                "Secret meanings behind {ritual} in ancient times",
                "How {deity} influenced modern {aspect}",
                "The connection between {place} and {myth}",
                "Ancient wisdom of {text} for modern life",
                "The symbolism of {symbol} in Hindu culture",
                "Epic battles: {character} vs {opponent}",
                "The spiritual significance of {festival}",
                "Hidden powers of {weapon} in mythology",
                "Love stories from ancient India: {story}"
            ],
            "technology": [
                "How {tech} is changing {industry}",
                "The future of {field} with {innovation}",
                "Why {company} is leading in {sector}",
                "Breaking: New developments in {area}",
                "The impact of {technology} on {society_aspect}",
                "Revolutionary {product} that could change everything",
                "Hidden dangers of {tech_trend}",
                "Success story: How {startup} disrupted {market}",
                "The science behind {innovation}",
                "Predictions: {field} in the next decade"
            ],
            "science": [
                "Breakthrough discovery in {field}",
                "How {phenomenon} affects {subject}",
                "The mystery of {topic} finally solved",
                "New research reveals {finding}",
                "The connection between {thing1} and {thing2}",
                "What scientists found about {subject}",
                "Incredible facts about {natural_phenomenon}",
                "The evolution of {species_or_concept}",
                "Why {scientific_fact} matters for humanity",
                "Exploring the depths of {scientific_area}"
            ],
            "history": [
                "The untold story of {historical_event}",
                "How {historical_figure} changed {field}",
                "Secrets of {ancient_civilization}",
                "The real reason behind {historical_event}",
                "Lost knowledge of {historical_period}",
                "What {culture} taught us about {concept}",
                "The rise and fall of {empire_or_kingdom}",
                "Hidden facts about {famous_person}",
                "How {invention} changed the world",
                "The mystery of {historical_mystery}"
            ],
            "health": [
                "Natural ways to improve {health_aspect}",
                "The truth about {health_trend}",
                "How {lifestyle_factor} affects {body_system}",
                "Ancient remedies for modern {condition}",
                "The science of {health_practice}",
                "Why {food_or_herb} is a superfood",
                "Mental health: Understanding {condition}",
                "The connection between {factor1} and {factor2}",
                "Simple habits for better {health_goal}",
                "Debunking myths about {health_topic}"
            ],
            "business": [
                "How {company} became a {industry} leader",
                "The psychology of {business_concept}",
                "Why {business_strategy} works",
                "The future of {industry}",
                "Success lessons from {entrepreneur}",
                "How {trend} is reshaping {market}",
                "The rise of {business_model}",
                "What {failure} taught the business world",
                "The economics of {phenomenon}",
                "How to succeed in {field}"
            ]
        }
        
        # Domain-specific variables for template filling
        self.domain_variables = {
            "indian_mythology": {
                "character": ["Hanuman", "Arjuna", "Krishna", "Rama", "Draupadi", "Bhima", "Ganesha"],
                "ritual": ["Yajna", "Puja", "Sandhya Vandana", "Pradakshina", "Aarti"],
                "deity": ["Shiva", "Vishnu", "Durga", "Lakshmi", "Saraswati", "Ganesha"],
                "aspect": ["leadership", "relationships", "spirituality", "success", "wisdom"],
                "place": ["Vrindavan", "Ayodhya", "Kashi", "Dwarka", "Kurukshetra"],
                "myth": ["Ramayana", "Mahabharata", "Puranas", "Vedic stories"],
                "text": ["Bhagavad Gita", "Ramayana", "Upanishads", "Vedas"],
                "symbol": ["Om", "Swastika", "Lotus", "Conch", "Trishul"],
                "opponent": ["Ravana", "Mahishasura", "Kansa", "Duryodhana"],
                "festival": ["Diwali", "Holi", "Navaratri", "Dussehra", "Janmashtami"],
                "weapon": ["Sudarshan Chakra", "Gada", "Trishul", "Bow of Arjuna"],
                "story": ["Radha Krishna", "Shiva Parvati", "Rama Sita"]
            },
            "technology": {
                "tech": ["AI", "Blockchain", "IoT", "5G", "VR", "AR", "Quantum Computing"],
                "industry": ["healthcare", "finance", "education", "entertainment", "retail"],
                "field": ["machine learning", "cybersecurity", "robotics", "biotechnology"],
                "innovation": ["neural networks", "gene editing", "renewable energy", "space tech"],
                "company": ["Google", "Tesla", "Microsoft", "Apple", "Meta", "OpenAI"],
                "sector": ["autonomous vehicles", "cloud computing", "fintech", "medtech"],
                "area": ["artificial intelligence", "quantum physics", "nanotechnology"],
                "technology": ["machine learning", "blockchain", "IoT", "5G networks"],
                "society_aspect": ["privacy", "jobs", "communication", "healthcare"],
                "product": ["smartphone", "electric car", "AI assistant", "VR headset"],
                "tech_trend": ["social media", "cryptocurrency", "AI automation"],
                "startup": ["OpenAI", "Neuralink", "SpaceX", "Stripe"],
                "market": ["transportation", "finance", "healthcare", "education"]
            },
            "science": {
                "field": ["neuroscience", "quantum physics", "marine biology", "astronomy"],
                "phenomenon": ["black holes", "climate change", "genetic mutations", "gravity"],
                "subject": ["human brain", "ocean currents", "planetary formation", "evolution"],
                "topic": ["dark matter", "consciousness", "origin of life", "time travel"],
                "finding": ["new species", "gravitational waves", "brain plasticity"],
                "thing1": ["sleep", "exercise", "stress", "nutrition"],
                "thing2": ["longevity", "memory", "immunity", "creativity"],
                "natural_phenomenon": ["aurora", "earthquakes", "photosynthesis", "migration"],
                "species_or_concept": ["human intelligence", "plant communication", "animal behavior"],
                "scientific_fact": ["quantum entanglement", "DNA repair", "neuroplasticity"],
                "scientific_area": ["deep ocean", "space", "human genome", "quantum realm"]
            },
            "history": {
                "historical_event": ["World War II", "Renaissance", "Industrial Revolution", "Ancient Egypt"],
                "historical_figure": ["Leonardo da Vinci", "Napoleon", "Cleopatra", "Genghis Khan"],
                "ancient_civilization": ["Maya", "Roman Empire", "Indus Valley", "Greek civilization"],
                "historical_period": ["Medieval times", "Ancient Greece", "Victorian era", "Stone Age"],
                "culture": ["Ancient Greeks", "Vikings", "Samurai", "Egyptians"],
                "concept": ["democracy", "medicine", "architecture", "philosophy"],
                "empire_or_kingdom": ["Roman Empire", "Mongol Empire", "British Empire", "Ottoman Empire"],
                "famous_person": ["Julius Caesar", "Alexander the Great", "Einstein", "Churchill"],
                "invention": ["printing press", "wheel", "electricity", "internet"],
                "historical_mystery": ["Stonehenge", "Atlantis", "Bermuda Triangle", "Easter Island"]
            },
            "health": {
                "health_aspect": ["sleep quality", "mental clarity", "immune system", "energy levels"],
                "health_trend": ["intermittent fasting", "cold therapy", "meditation", "plant-based diet"],
                "lifestyle_factor": ["stress", "exercise", "diet", "sleep"],
                "body_system": ["nervous system", "immune system", "digestive system", "cardiovascular system"],
                "condition": ["anxiety", "insomnia", "back pain", "digestive issues"],
                "food_or_herb": ["turmeric", "ginger", "garlic", "green tea", "salmon"],
                "health_practice": ["yoga", "meditation", "acupuncture", "massage therapy"],
                "factor1": ["gut health", "stress levels", "sleep quality", "exercise"],
                "factor2": ["mental health", "immunity", "longevity", "brain function"],
                "health_goal": ["heart health", "weight management", "mental clarity", "longevity"],
                "health_topic": ["detox diets", "supplements", "fitness trends", "mental health"]
            },
            "business": {
                "company": ["Apple", "Amazon", "Tesla", "Google", "Microsoft", "Netflix"],
                "industry": ["tech", "automotive", "retail", "entertainment", "finance"],
                "business_concept": ["marketing", "leadership", "innovation", "customer service"],
                "business_strategy": ["disruption", "diversification", "focus", "partnership"],
                "entrepreneur": ["Elon Musk", "Steve Jobs", "Bill Gates", "Jeff Bezos"],
                "trend": ["remote work", "AI automation", "sustainability", "digital transformation"],
                "market": ["e-commerce", "streaming", "electric vehicles", "cloud computing"],
                "business_model": ["subscription", "platform", "freemium", "marketplace"],
                "failure": ["Blockbuster", "Kodak", "Nokia", "BlackBerry"],
                "phenomenon": ["viral marketing", "network effects", "economies of scale"],
                "field": ["startups", "e-commerce", "fintech", "social media"]
            }
        }
        
    def generate_topics_for_domain(self, domain: str, count: int = 10) -> List[GeneratedTopic]:
        """Generate topics for a specific domain"""
        if domain not in self.topic_templates:
            return self._generate_fallback_topics(domain, count)
        
        topics = []
        templates = self.topic_templates[domain]
        variables = self.domain_variables.get(domain, {})
        
        for _ in range(count):
            template = random.choice(templates)
            filled_template = self._fill_template(template, variables)
            
            topic = GeneratedTopic(
                topic=filled_template,
                domain=domain,
                subtopics=self._generate_subtopics(filled_template, domain),
                estimated_interest=random.uniform(0.6, 1.0),
                keywords=self._extract_keywords(filled_template),
                generated_at=datetime.now()
            )
            topics.append(topic)
        
        return topics
    
    def _fill_template(self, template: str, variables: Dict[str, List[str]]) -> str:
        """Fill template with random variables"""
        filled = template
        for var_name, var_values in variables.items():
            if f"{{{var_name}}}" in filled:
                filled = filled.replace(f"{{{var_name}}}", random.choice(var_values))
        return filled
    
    def _generate_subtopics(self, main_topic: str, domain: str) -> List[str]:
        """Generate related subtopics"""
        # Simple subtopic generation based on domain
        base_subtopics = {
            "indian_mythology": ["historical context", "spiritual meaning", "cultural impact", "modern relevance"],
            "technology": ["current trends", "future implications", "benefits", "challenges"],
            "science": ["research findings", "practical applications", "implications", "future research"],
            "history": ["timeline", "key figures", "consequences", "lessons learned"],
            "health": ["symptoms", "causes", "treatments", "prevention"],
            "business": ["case studies", "strategies", "market impact", "lessons"]
        }
        
        domain_subtopics = base_subtopics.get(domain, ["overview", "details", "implications", "conclusion"])
        return random.sample(domain_subtopics, min(3, len(domain_subtopics)))
    
    def _extract_keywords(self, topic: str) -> List[str]:
        """Extract keywords from topic"""
        # Simple keyword extraction
        stop_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "how", "why", "what"}
        words = topic.lower().replace(".", "").replace(",", "").split()
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return keywords[:5]
    
    def _generate_fallback_topics(self, domain: str, count: int) -> List[GeneratedTopic]:
        """Generate fallback topics for unknown domains"""
        fallback_templates = [
            f"Introduction to {domain}",
            f"The future of {domain}",
            f"Top trends in {domain}",
            f"Understanding {domain} better",
            f"The importance of {domain}",
            f"How {domain} affects our daily lives",
            f"Key concepts in {domain}",
            f"The evolution of {domain}",
            f"Why {domain} matters",
            f"Exploring {domain} in depth"
        ]
        
        topics = []
        for i in range(min(count, len(fallback_templates))):
            topic = GeneratedTopic(
                topic=fallback_templates[i],
                domain=domain,
                subtopics=["overview", "importance", "applications"],
                estimated_interest=0.7,
                keywords=[domain, "introduction", "overview"],
                generated_at=datetime.now()
            )
            topics.append(topic)
        
        return topics
    
    def generate_daily_topics(self, domains: List[str], topics_per_domain: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Generate daily topics for multiple domains"""
        daily_topics = {}
        
        for domain in domains:
            topics = self.generate_topics_for_domain(domain, topics_per_domain)
            daily_topics[domain] = [
                {
                    "topic": t.topic,
                    "domain": t.domain,
                    "subtopics": t.subtopics,
                    "estimated_interest": t.estimated_interest,
                    "keywords": t.keywords,
                    "generated_at": t.generated_at.isoformat(),
                    "used": t.used
                }
                for t in topics
            ]
        
        return daily_topics
    
    def save_topics_to_queue(self, topics: Dict[str, List[Dict[str, Any]]], queue_file: str = "topic_queue.json"):
        """Save generated topics to JSON queue file"""
        try:
            # Load existing queue if exists
            existing_queue = {}
            if os.path.exists(queue_file):
                with open(queue_file, 'r', encoding='utf-8') as f:
                    existing_queue = json.load(f)
            
            # Add new topics to queue
            timestamp = datetime.now().isoformat()
            for domain, domain_topics in topics.items():
                if domain not in existing_queue:
                    existing_queue[domain] = []
                
                for topic in domain_topics:
                    topic["queue_added_at"] = timestamp
                    existing_queue[domain].append(topic)
            
            # Save updated queue
            with open(queue_file, 'w', encoding='utf-8') as f:
                json.dump(existing_queue, f, indent=2, ensure_ascii=False)
            
            print(f"[TOPIC AGENT] Saved {sum(len(topics) for topics in topics.values())} topics to {queue_file}")
            return True
            
        except Exception as e:
            print(f"[TOPIC AGENT] Error saving topics to queue: {e}")
            return False
    
    def get_next_topic_from_queue(self, domain: str = None, queue_file: str = "topic_queue.json") -> Optional[Dict[str, Any]]:
        """Get next unused topic from queue"""
        try:
            if not os.path.exists(queue_file):
                return None
            
            with open(queue_file, 'r', encoding='utf-8') as f:
                queue = json.load(f)
            
            # Find next unused topic
            if domain and domain in queue:
                domains_to_check = [domain]
            else:
                domains_to_check = list(queue.keys())
            
            for domain_name in domains_to_check:
                for i, topic in enumerate(queue[domain_name]):
                    if not topic.get("used", False):
                        # Mark as used
                        queue[domain_name][i]["used"] = True
                        queue[domain_name][i]["used_at"] = datetime.now().isoformat()
                        
                        # Save updated queue
                        with open(queue_file, 'w', encoding='utf-8') as f:
                            json.dump(queue, f, indent=2, ensure_ascii=False)
                        
                        return topic
            
            return None
            
        except Exception as e:
            print(f"[TOPIC AGENT] Error getting topic from queue: {e}")
            return None
    
    def get_queue_status(self, queue_file: str = "topic_queue.json") -> Dict[str, Any]:
        """Get status of topic queue"""
        try:
            if not os.path.exists(queue_file):
                return {"total_topics": 0, "unused_topics": 0, "domains": {}}
            
            with open(queue_file, 'r', encoding='utf-8') as f:
                queue = json.load(f)
            
            status = {
                "total_topics": 0,
                "unused_topics": 0,
                "domains": {}
            }
            
            for domain, topics in queue.items():
                total = len(topics)
                unused = len([t for t in topics if not t.get("used", False)])
                
                status["domains"][domain] = {
                    "total": total,
                    "unused": unused,
                    "used": total - unused
                }
                
                status["total_topics"] += total
                status["unused_topics"] += unused
            
            return status
            
        except Exception as e:
            print(f"[TOPIC AGENT] Error getting queue status: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Test the topic generation agent
    agent = TopicGenerationAgent()
    
    print("Testing Topic Generation Agent...")
    
    # Generate topics for Indian mythology
    topics = agent.generate_topics_for_domain("indian_mythology", 5)
    
    print(f"\nGenerated {len(topics)} topics for 'indian_mythology':")
    for i, topic in enumerate(topics, 1):
        print(f"{i}. {topic.topic}")
        print(f"   Keywords: {', '.join(topic.keywords)}")
        print(f"   Subtopics: {', '.join(topic.subtopics)}")
        print()
    
    # Generate daily topics for multiple domains
    daily_topics = agent.generate_daily_topics(["indian_mythology", "technology", "science"], 3)
    
    # Save to queue
    agent.save_topics_to_queue(daily_topics)
    
    # Test queue operations
    print("Queue Status:", agent.get_queue_status())
    
    next_topic = agent.get_next_topic_from_queue()
    if next_topic:
        print(f"\nNext topic from queue: {next_topic['topic']}")