from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId

from app.utils.timezone import now_tz
from tradingagents.utils.logging_init import get_logger

logger = get_logger("default")


class ExpectationService:
    def __init__(self):
        self.collection_name = "user_expectations"

    async def _get_collection(self):
        from app.core.database import get_mongo_db
        db = get_mongo_db()
        return db[self.collection_name]

    async def create(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        collection = await self._get_collection()
        doc = {
            "user_id": user_id,
            "title": data.get("title", ""),
            "content": data.get("content", {}),
            "is_active": data.get("is_active", False),
            "created_at": now_tz(),
            "updated_at": now_tz(),
        }
        result = await collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def update(self, expectation_id: str, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        collection = await self._get_collection()
        update_fields = {"updated_at": now_tz()}
        if "title" in data and data["title"] is not None:
            update_fields["title"] = data["title"]
        if "content" in data and data["content"] is not None:
            update_fields["content"] = data["content"]
        if "is_active" in data and data["is_active"] is not None:
            update_fields["is_active"] = data["is_active"]
        result = await collection.find_one_and_update(
            {"_id": ObjectId(expectation_id), "user_id": user_id},
            {"$set": update_fields},
            return_document=True,
        )
        if result:
            result["_id"] = str(result["_id"])
        return result

    async def delete(self, expectation_id: str, user_id: str) -> bool:
        collection = await self._get_collection()
        result = await collection.delete_one({"_id": ObjectId(expectation_id), "user_id": user_id})
        return result.deleted_count > 0

    async def get_by_id(self, expectation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        collection = await self._get_collection()
        doc = await collection.find_one({"_id": ObjectId(expectation_id), "user_id": user_id})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def list_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        collection = await self._get_collection()
        cursor = collection.find({"user_id": user_id}).sort("updated_at", -1).skip(skip).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def get_active(self, user_id: str) -> Optional[Dict[str, Any]]:
        collection = await self._get_collection()
        doc = await collection.find_one({"user_id": user_id, "is_active": True})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def set_active(self, expectation_id: str, user_id: str) -> bool:
        collection = await self._get_collection()
        await collection.update_many({"user_id": user_id}, {"$set": {"is_active": False}})
        result = await collection.update_one(
            {"_id": ObjectId(expectation_id), "user_id": user_id},
            {"$set": {"is_active": True, "updated_at": now_tz()}},
        )
        return result.modified_count > 0

    async def copy(self, expectation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        original = await self.get_by_id(expectation_id, user_id)
        if not original:
            return None
        new_data = {
            "title": f"{original.get('title', '')} (副本)",
            "content": original.get("content", {}),
            "is_active": False,
        }
        return await self.create(user_id, new_data)
