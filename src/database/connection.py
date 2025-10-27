"""
Database connection handler - supports both MongoDB and JSON fallback
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from src.config import Config
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class JsonDBList:
    """Wrapper list to mimic MongoDB API"""
    def __init__(self, data_list=None):
        self.data = data_list or []

    def find_one(self, query):
        for item in self.data:
            match = True
            for k, v in query.items():
                # support $gt for datetime
                if isinstance(v, dict) and "$gt" in v:
                    item_val = item.get(k)
                    if isinstance(item_val, str):
                        try:
                            item_val = datetime.fromisoformat(item_val)
                        except:
                            pass
                    if not (item_val and item_val > v["$gt"]):
                        match = False
                        break
                else:
                    if item.get(k) != v:
                        match = False
                        break
            if match:
                return item
        return None
        
    def find(self, query):
        """Find multiple documents matching query"""
        results = []
        for item in self.data:
            match = True
            for k, v in query.items():
                if isinstance(v, dict) and "$gt" in v:
                    if not (item.get(k) and item.get(k) > v["$gt"]):
                        match = False
                        break
                elif isinstance(v, dict) and "$gte" in v:
                    if not (item.get(k) and item.get(k) >= v["$gte"]):
                        match = False
                        break
                elif isinstance(v, dict) and "$lt" in v:
                    if not (item.get(k) and item.get(k) < v["$lt"]):
                        match = False
                        break
                elif isinstance(v, dict) and "$lte" in v:
                    if not (item.get(k) and item.get(k) <= v["$lte"]):
                        match = False
                        break
                elif item.get(k) != v:
                    match = False
                    break
            if match:
                results.append(item)
        return JsonDBCursor(results)

    def delete_many(self, query):
        """Delete multiple documents matching query"""
        original_len = len(self.data)
        self.data = [item for item in self.data if not all(
            item.get(k) == v if not isinstance(v, dict) else self._match_operator(item.get(k), v)
            for k, v in query.items()
        )]
        deleted_count = original_len - len(self.data)
        return type('DeleteResult', (), {'deleted_count': deleted_count})()

    def _match_operator(self, value, operator_dict):
        """Match MongoDB operators"""
        if "$gt" in operator_dict:
            return value and value > operator_dict["$gt"]
        elif "$gte" in operator_dict:
            return value and value >= operator_dict["$gte"]
        elif "$lt" in operator_dict:
            return value and value < operator_dict["$lt"]
        elif "$lte" in operator_dict:
            return value and value <= operator_dict["$lte"]
        return False

    def insert_one(self, doc):
        """Insert single document"""
        self.data.append(doc)
        return type('InsertResult', (), {'inserted_id': len(self.data) - 1})()

    def update_one(self, query, update, upsert=False):
        """Update single document"""
        doc = self.find_one(query)
        if doc:
            # Handle $set operator
            if "$set" in update:
                for k, v in update["$set"].items():
                    doc[k] = v
            # Handle $inc operator
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    doc[k] = doc.get(k, 0) + v
            # Handle $push operator
            if "$push" in update:
                for k, v in update["$push"].items():
                    if k not in doc:
                        doc[k] = []
                    if isinstance(v, dict) and "$each" in v:
                        items = v["$each"]
                        doc[k].extend(items)
                        if "$slice" in v:
                            doc[k] = doc[k][v["$slice"]:]
                    else:
                        doc[k].append(v)
            # Handle $addToSet operator
            if "$addToSet" in update:
                for k, v in update["$addToSet"].items():
                    if k not in doc:
                        doc[k] = []
                    if isinstance(v, dict) and "$each" in v:
                        for item in v["$each"]:
                            if item not in doc[k]:
                                doc[k].append(item)
                    else:
                        if v not in doc[k]:
                            doc[k].append(v)
            # Handle $setOnInsert (only for upsert)
            if upsert and "$setOnInsert" in update:
                pass  # Already inserting new doc
            return doc
        elif upsert:
            # Create new document
            new_doc = dict(query)
            if "$set" in update:
                new_doc.update(update["$set"])
            if "$setOnInsert" in update:
                new_doc.update(update["$setOnInsert"])
            self.insert_one(new_doc)
            return new_doc
        return None

    def update_many(self, query, update):
        """Update multiple documents"""
        count = 0
        for item in self.data:
            match = all(item.get(k) == v for k, v in query.items())
            if match:
                if "$set" in update:
                    for k, v in update["$set"].items():
                        item[k] = v
                count += 1
        return type('UpdateResult', (), {'modified_count': count})()

    def count_documents(self, query):
        """Count documents matching query"""
        count = 0
        for item in self.data:
            match = True
            for k, v in query.items():
                if isinstance(v, dict):
                    if "$gte" in v and not (item.get(k) and item.get(k) >= v["$gte"]):
                        match = False
                        break
                    elif "$lte" in v and not (item.get(k) and item.get(k) <= v["$lte"]):
                        match = False
                        break
                elif item.get(k) != v:
                    match = False
                    break
            if match:
                count += 1
        return count

class JsonDBCursor:
    """Cursor for JSON query results"""
    def __init__(self, results):
        self.results = results
        self._sort_key = None
        self._sort_order = 1
        self._limit_val = None

    def sort(self, key, order=1):
        """Sort results"""
        self._sort_key = key
        self._sort_order = order
        return self

    def limit(self, val):
        """Limit results"""
        self._limit_val = val
        return self

    def __iter__(self):
        """Iterator for results"""
        results = self.results[:]
        if self._sort_key:
            results.sort(key=lambda x: x.get(self._sort_key, 0), 
                        reverse=(self._sort_order == -1))
        if self._limit_val:
            results = results[:self._limit_val]
        return iter(results)

class JsonDatabase:
    """JSON-based database"""
    def __init__(self, json_path):
        self.json_path = Path(json_path)
        self.db = {}
        self.load_json()

    def load_json(self):
        """Load database from JSON file"""
        if self.json_path.exists():
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Wrap each collection in JsonDBList
                    for key, value in data.items():
                        if isinstance(value, list):
                            self.db[key] = JsonDBList(value)
                        else:
                            self.db[key] = value
                logger.info(f"Database loaded from JSON: {self.json_path}")
            except Exception as e:
                logger.error(f"Error loading JSON database: {e}")
                self.db = {}
        else:
            logger.warning(f"{self.json_path} not found, starting with empty database")
            self.db = {}

    def save_json(self):
        """Save database to JSON file"""
        try:
            save_data = {}
            for key, value in self.db.items():
                if isinstance(value, JsonDBList):
                    save_data[key] = value.data
                else:
                    save_data[key] = value
            
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, default=str)
            logger.info("Database saved to JSON")
        except Exception as e:
            logger.error(f"Error saving JSON database: {e}")

    def __getitem__(self, key):
        """Get collection"""
        if key not in self.db:
            self.db[key] = JsonDBList()
        return self.db[key]

    def __setitem__(self, key, value):
        """Set collection"""
        self.db[key] = value

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
                logger.info("[OK] Connected to MongoDB")
                return
            except Exception as e:
                logger.warning(f"MongoDB connection failed: {e}")
                logger.info("Falling back to JSON database...")
        
        # Fallback to JSON
        self.use_mongo = False
        json_path = Config.DATA_DIR / "database.json"
        self.json_db = JsonDatabase(json_path)
        self.db = self.json_db
        logger.info("[OK] Using JSON database")

    def __getitem__(self, key):
        """Get collection from database"""
        if self.use_mongo:
            return self.db[key]
        else:
            return self.json_db[key]

    def save(self):
        """Save database (only for JSON mode)"""
        if not self.use_mongo and self.json_db:
            self.json_db.save_json()

    def close(self):
        """Close database connection"""
        if self.use_mongo and self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
        elif self.json_db:
            self.json_db.save_json()
            logger.info("JSON database saved and closed")

# Global database instance
db_instance = DatabaseConnection()