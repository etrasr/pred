import requests
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class GistStorage:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        if not self.github_token:
            logger.error("❌ GITHUB_TOKEN environment variable is required")
            raise ValueError("GITHUB_TOKEN is required")
        
        self.base_url = "https://api.github.com/gists"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Try to load existing Gist ID, or create new one
        self.gist_id = self._load_or_create_gist()
        logger.info(f"📂 Using Gist: {self.gist_id}")
    
    def _load_or_create_gist(self):
        """Load existing Gist ID or create new one"""
        gist_id_file = '/opt/render/project/src/gist_id.txt'
        
        try:
            # Try to read existing Gist ID from file
            if os.path.exists(gist_id_file):
                with open(gist_id_file, 'r') as f:
                    existing_gist_id = f.read().strip()
                    if existing_gist_id and self._gist_exists(existing_gist_id):
                        logger.info(f"✅ Found existing Gist ID: {existing_gist_id}")
                        return existing_gist_id
            
            # Create new Gist
            new_gist_id = self._create_new_gist()
            
            # Save Gist ID to file for future use
            with open(gist_id_file, 'w') as f:
                f.write(new_gist_id)
            
            logger.info(f"📝 Created new Gist: {new_gist_id}")
            return new_gist_id
            
        except Exception as e:
            logger.error(f"❌ Error managing Gist ID: {e}")
            # Fallback: create new Gist without saving ID
            return self._create_new_gist()
    
    def _gist_exists(self, gist_id):
        """Check if Gist exists and is accessible"""
        try:
            url = f"{self.base_url}/{gist_id}"
            response = requests.get(url, headers=self.headers)
            return response.status_code == 200
        except:
            return False
    
    def _create_new_gist(self):
        """Create a new Gist for storing Keno data"""
        initial_data = {
            "draws": [],
            "number_stats": {},
            "created_at": datetime.now().isoformat(),
            "description": "Keno Prediction Bot Data Storage - Auto-generated"
        }
        
        data = {
            "description": "Keno Prediction Bot Data Storage",
            "public": False,
            "files": {
                "keno_data.json": {
                    "content": json.dumps(initial_data, indent=2)
                }
            }
        }
        
        response = requests.post(self.base_url, headers=self.headers, json=data)
        
        if response.status_code == 201:
            gist_data = response.json()
            return gist_data['id']
        else:
            logger.error(f"❌ Failed to create Gist: {response.status_code} - {response.text}")
            raise Exception("Failed to create Gist storage")
    
    def load_data(self):
        """Load all data from Gist"""
        try:
            url = f"{self.base_url}/{self.gist_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                gist_data = response.json()
                content = gist_data['files']['keno_data.json']['content']
                data = json.loads(content)
                logger.info(f"✅ Loaded data from Gist: {len(data.get('draws', []))} draws")
                return data
            else:
                logger.error(f"❌ Failed to load Gist: {response.status_code}")
                return self._get_default_data()
                
        except Exception as e:
            logger.error(f"❌ Error loading from Gist: {e}")
            return self._get_default_data()
    
    def save_data(self, data):
        """Save data to Gist"""
        try:
            url = f"{self.base_url}/{self.gist_id}"
            
            update_data = {
                "description": f"Keno Prediction Bot - {len(data.get('draws', []))} draws - Last update: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "files": {
                    "keno_data.json": {
                        "content": json.dumps(data, indent=2)
                    }
                }
            }
            
            response = requests.patch(url, headers=self.headers, json=update_data)
            
            if response.status_code == 200:
                logger.info(f"✅ Data saved to Gist: {len(data.get('draws', []))} draws")
                return True
            else:
                logger.error(f"❌ Failed to save Gist: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving to Gist: {e}")
            return False
    
    def _get_default_data(self):
        """Return default data structure"""
        return {
            "draws": [],
            "number_stats": {},
            "created_at": datetime.now().isoformat()
        }
    
    def get_gist_url(self):
        """Get the URL to view the Gist"""
        return f"https://gist.github.com/{self.gist_id}"
