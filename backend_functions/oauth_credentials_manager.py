"""
OAuth Credentials Manager
Securely manages Google OAuth credentials stored in JSON files
"""

import os
import json
import base64
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class OAuthCredentialsManager:
    """
    Manages Google OAuth credentials with encryption and secure storage
    """
    
    def __init__(self, credentials_file: str = "oauth_credentials.json", 
                 encryption_key_file: str = "oauth_key.key"):
        
        self.credentials_file = credentials_file
        self.encryption_key_file = encryption_key_file
        self.master_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.master_key)
        
        # Load existing credentials
        self.credentials_store = self._load_credentials()
        
        print(f"[OAUTH] Initialized credentials manager")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for credentials"""
        if os.path.exists(self.encryption_key_file):
            with open(self.encryption_key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.encryption_key_file, 'wb') as f:
                f.write(key)
            print(f"[OAUTH] Generated new encryption key: {self.encryption_key_file}")
            return key
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load encrypted credentials from file"""
        if not os.path.exists(self.credentials_file):
            return {}
        
        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
            
            # Decrypt each credential entry
            decrypted_store = {}
            for user_id, encrypted_creds in encrypted_data.items():
                try:
                    decrypted_bytes = self.fernet.decrypt(encrypted_creds['encrypted_data'].encode())
                    decrypted_creds = json.loads(decrypted_bytes.decode())
                    decrypted_store[user_id] = {
                        **decrypted_creds,
                        'created_at': encrypted_creds.get('created_at'),
                        'last_used': encrypted_creds.get('last_used'),
                        'usage_count': encrypted_creds.get('usage_count', 0)
                    }
                except Exception as e:
                    print(f"[OAUTH] Error decrypting credentials for {user_id}: {e}")
            
            return decrypted_store
            
        except Exception as e:
            print(f"[OAUTH] Error loading credentials: {e}")
            return {}
    
    def _save_credentials(self):
        """Save encrypted credentials to file"""
        try:
            encrypted_store = {}
            
            for user_id, creds in self.credentials_store.items():
                # Prepare data for encryption (exclude metadata)
                creds_to_encrypt = {
                    'client_id': creds['client_id'],
                    'client_secret': creds['client_secret'],
                    'user_info': creds.get('user_info', {})
                }
                
                # Encrypt credentials
                creds_json = json.dumps(creds_to_encrypt)
                encrypted_data = self.fernet.encrypt(creds_json.encode()).decode()
                
                # Store with metadata
                encrypted_store[user_id] = {
                    'encrypted_data': encrypted_data,
                    'created_at': creds.get('created_at'),
                    'last_used': creds.get('last_used'),
                    'usage_count': creds.get('usage_count', 0)
                }
            
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_store, f, indent=2)
                
        except Exception as e:
            print(f"[OAUTH] Error saving credentials: {e}")
    
    def generate_access_key(self, user_identifier: str) -> str:
        """Generate a secure access key for a user"""
        # Create access key based on user identifier and timestamp
        key_data = f"{user_identifier}_{datetime.now().isoformat()}_{os.urandom(16).hex()}"
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()
        return f"oauth_{key_hash[:32]}"
    
    def add_credentials(self, access_key: str, client_id: str, client_secret: str,
                       user_info: Optional[Dict[str, Any]] = None) -> bool:
        """Add new OAuth credentials"""
        try:
            if access_key in self.credentials_store:
                print(f"[OAUTH] Access key already exists: {access_key}")
                return False
            
            # Validate client_id format (basic validation)
            if not client_id or not client_id.endswith('.apps.googleusercontent.com'):
                print(f"[OAUTH] Invalid client_id format")
                return False
            
            # Validate client_secret (basic validation)
            if not client_secret or len(client_secret) < 10:
                print(f"[OAUTH] Invalid client_secret")
                return False
            
            # Store credentials
            self.credentials_store[access_key] = {
                'client_id': client_id,
                'client_secret': client_secret,
                'user_info': user_info or {},
                'created_at': datetime.now().isoformat(),
                'last_used': None,
                'usage_count': 0
            }
            
            self._save_credentials()
            print(f"[OAUTH] Added credentials for access key: {access_key[:16]}...")
            return True
            
        except Exception as e:
            print(f"[OAUTH] Error adding credentials: {e}")
            return False
    
    def get_credentials(self, access_key: str) -> Optional[Dict[str, Any]]:
        """Get credentials for an access key"""
        try:
            if access_key not in self.credentials_store:
                return None
            
            creds = self.credentials_store[access_key].copy()
            
            # Update usage tracking
            self.credentials_store[access_key]['last_used'] = datetime.now().isoformat()
            self.credentials_store[access_key]['usage_count'] += 1
            self._save_credentials()
            
            return creds
            
        except Exception as e:
            print(f"[OAUTH] Error getting credentials: {e}")
            return None
    
    def remove_credentials(self, access_key: str) -> bool:
        """Remove credentials"""
        try:
            if access_key in self.credentials_store:
                del self.credentials_store[access_key]
                self._save_credentials()
                print(f"[OAUTH] Removed credentials for: {access_key[:16]}...")
                return True
            return False
            
        except Exception as e:
            print(f"[OAUTH] Error removing credentials: {e}")
            return False
    
    def list_credentials(self) -> List[Dict[str, Any]]:
        """List all stored credentials (without secrets)"""
        try:
            creds_list = []
            
            for access_key, creds in self.credentials_store.items():
                creds_list.append({
                    'access_key': access_key[:16] + "...",  # Masked
                    'client_id': creds['client_id'][:20] + "..." if len(creds['client_id']) > 20 else creds['client_id'],
                    'user_info': creds.get('user_info', {}),
                    'created_at': creds.get('created_at'),
                    'last_used': creds.get('last_used'),
                    'usage_count': creds.get('usage_count', 0)
                })
            
            return creds_list
            
        except Exception as e:
            print(f"[OAUTH] Error listing credentials: {e}")
            return []
    
    def validate_access_key(self, access_key: str) -> bool:
        """Validate if access key exists and is valid"""
        return access_key in self.credentials_store
    
    def get_stats(self) -> Dict[str, Any]:
        """Get credentials statistics"""
        try:
            total_creds = len(self.credentials_store)
            active_creds = len([c for c in self.credentials_store.values() if c.get('last_used')])
            
            # Calculate usage statistics
            total_usage = sum(c.get('usage_count', 0) for c in self.credentials_store.values())
            
            # Most used credentials
            most_used = max(self.credentials_store.items(), 
                           key=lambda x: x[1].get('usage_count', 0)) if self.credentials_store else None
            
            return {
                'total_credentials': total_creds,
                'active_credentials': active_creds,
                'total_usage_count': total_usage,
                'most_used_key': most_used[0][:16] + "..." if most_used else None,
                'most_used_count': most_used[1].get('usage_count', 0) if most_used else 0,
                'credentials_file_exists': os.path.exists(self.credentials_file),
                'encryption_key_exists': os.path.exists(self.encryption_key_file)
            }
            
        except Exception as e:
            print(f"[OAUTH] Error getting stats: {e}")
            return {"error": str(e)}

# Global instance
_oauth_manager: Optional[OAuthCredentialsManager] = None

def get_oauth_manager() -> OAuthCredentialsManager:
    """Get global OAuth credentials manager instance"""
    global _oauth_manager
    
    if _oauth_manager is None:
        _oauth_manager = OAuthCredentialsManager()
    
    return _oauth_manager

if __name__ == "__main__":
    # Test the OAuth credentials manager
    manager = OAuthCredentialsManager()
    
    print("Testing OAuth Credentials Manager...")
    
    # Generate test access key
    test_key = manager.generate_access_key("test_user")
    print(f"Generated access key: {test_key}")
    
    # Add test credentials
    success = manager.add_credentials(
        test_key, 
        "123456789.apps.googleusercontent.com",
        "test_client_secret_12345",
        {"name": "Test User", "email": "test@example.com"}
    )
    print(f"Add credentials success: {success}")
    
    # Get credentials
    retrieved = manager.get_credentials(test_key)
    print(f"Retrieved credentials: {retrieved is not None}")
    
    # List credentials
    creds_list = manager.list_credentials()
    print(f"Credentials list: {len(creds_list)} items")
    
    # Get stats
    stats = manager.get_stats()
    print(f"Stats: {stats}")
    
    # Clean up test
    manager.remove_credentials(test_key)
    print("Cleaned up test credentials")