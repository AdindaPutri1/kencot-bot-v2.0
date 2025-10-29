from src.utils.config import Config
from pymongo import MongoClient
import logging


class DatabaseConnection:
    """Main database connection handler - supports MongoDB and JSON"""
    
    def __init__(self):
        self.db = None
        self.client = None
        self.use_mongo = False
        self.json_db = None

    def connect(self):
        """Connect to database (MongoDB or JSON fallback)"""
        # Try MongoDB first if URI is provided
        mongo_uri = getattr(Config, 'MONGO_URI', None) 
        mongo_db = getattr(Config, 'MONGO_DB', None) 
        
        if mongo_uri and mongo_uri != "mongodb://localhost:27017":
            try:
                self.client = MongoClient(mongo_uri)
                self.db = self.client[mongo_db]
                # Test connection
                self.client.server_info()
                self.use_mongo = True
                logging.info("[OK] Connected to MongoDB")
                return
            except Exception as e:
                logging.warning(f"MongoDB connection failed: {e}")
                logging.info("Falling back to JSON database...")
    

    def __getitem__(self, key):
        return self.db[key]
    
    def close(self):
        """Close database connection"""
        if self.use_mongo and self.client:
            self.client.close()
            logging.info("MongoDB connection closed")
        elif self.json_db:
            logging.info("JSON database closed")

# Global database instance
db_instance = DatabaseConnection()