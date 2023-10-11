import hashlib
import json


def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    key_parts = [
        first_name or "",
        last_name or "",
        phone or "",
        birthday.strftime("%Y%m%d") if birthday is not None else "",
    ]
    data = "".join(key_parts)
    key = "uid:" + hashlib.md5(data.encode('utf-8')).hexdigest()
    print(key)
    # try get from cache,
    # fallback to heavy calculation in case of cache miss
    score = store.cache_get(key) or 0
    if score:
        return score
    if phone:
        score += 0.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 3.5
    # cache for 60 minutes
    store.cache_set(key, score, 60 * 60)
    return score


def get_interests(store, cid):
    r = store.get("i:%s" % cid)
    return json.loads(r) if r else []
