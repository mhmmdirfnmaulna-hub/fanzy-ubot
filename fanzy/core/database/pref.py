# fanzy/core/database/prefix.py
from fanzy.core.database import mongodb
from fanzy import ubot

prefixes = mongodb["fanzy"]["prefix"]

async def get_pref(user_id: int):
    """Mendapatkan prefix user (dalam bentuk list)"""
    
    # Cek cache dari ubot._prefix dulu
    if user_id in ubot._prefix:
        return ubot._prefix[user_id]
    
    # Jika tidak ada di cache, ambil dari database
    sh = await prefixes.find_one({"_id": user_id})
    
    if sh:
        pref = sh.get("prefixesi")
        if isinstance(pref, str):
            result = [pref] if pref else ["."]
        elif isinstance(pref, list):
            result = pref if pref else ["."]
        else:
            result = ["."]
    else:
        result = ["."]
    
    # Simpan ke cache
    ubot._prefix[user_id] = result
    return result

async def set_pref(user_id: int, prefix: list):
    """Menyimpan prefix user (dalam bentuk list)"""
    
    # Update database
    await prefixes.update_one(
        {"_id": user_id}, 
        {"$set": {"prefixesi": prefix}}, 
        upsert=True
    )
    
    # Update cache di ubot._prefix
    ubot._prefix[user_id] = prefix

async def rem_pref(user_id: int):
    """Menghapus prefix user (kembali ke default)"""
    
    # Update database ke default
    await prefixes.update_one(
        {"_id": user_id}, 
        {"$set": {"prefixesi": ["."]}},
        upsert=True
    )
    
    # Update cache ke default
    ubot._prefix[user_id] = ["."]

async def clear_prefix_cache(user_id: int = None):
    """Bersihkan cache"""
    if user_id:
        ubot._prefix.pop(user_id, None)
    else:
        ubot._prefix.clear()