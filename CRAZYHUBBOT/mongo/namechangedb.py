from CRAZYHUBBOT.utils.mongo import db

namechangedb = db.namechange


async def get_stored_name(chat_id: int, user_id: int):
    """Returns the last-known {first_name, last_name} doc for this user
    in this chat, or None if we've never seen them before."""
    return await namechangedb.find_one({"chat_id": chat_id, "user_id": user_id})


async def save_name(chat_id: int, user_id: int, first_name: str, last_name: str):
    """Upserts the current first_name/last_name for this user in this chat."""
    await namechangedb.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {
            "$set": {
                "first_name": first_name,
                "last_name": last_name,
            }
        },
        upsert=True,
    )
