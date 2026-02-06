import random
import asyncio
import aiohttp
import time
from typing import List, Dict, Optional, Tuple

class CodeforcesAPI:
    def __init__(self):
        self.base_url = "https://codeforces.com/api"

    async def fetch_json(self, session: aiohttp.ClientSession, endpoint: str, params: Dict = None) -> Optional[Dict]:
        url = f"{self.base_url}/{endpoint}"
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return None

    async def search_problems(self, session: aiohttp.ClientSession, min_rating: int, max_rating: int, count: int = 1, tags: List[str] = []) -> List[Dict]:
        """
        Search for random problems within a rating range.
        """
        data = await self.fetch_json(session, "problemset.problems")
        if not data or data["status"] != "OK":
            return []

        problems = data["result"]["problems"]
        candidates = []

        for p in problems:
            if "rating" in p and min_rating <= p["rating"] <= max_rating:
                # Add tag filtering if needed in future
                candidates.append(p)
        
        if not candidates:
            return []
            
        # Ensure unique selection
        if count > len(candidates):
            count = len(candidates)
            
        return random.sample(candidates, count)
        
    async def get_contest_problems(self, session: aiohttp.ClientSession, contest_id: int) -> List[Dict]:
        """Fetch all problems from a specific contest."""
        # Not strictly needed for duel but useful helper
        pass

    async def check_solved(self, session: aiohttp.ClientSession, handle: str, problems: List[Dict], start_time: float) -> Tuple[List[bool], List[float]]:
        """
        Check if a user has solved specific problems after a start time.
        Returns a tuple of (bool solved list, completion times).
        """
        data = await self.fetch_json(session, "user.status", {"handle": handle, "from": 1, "count": 20})
        # Note: count=20 might be too low if user submits a lot? 
        # But for active duels, 20 recent subs is usually enough for a 2 min refresh cycle or short duel.
        # Maybe bump to 50 to be safe.
        
        if not data or data["status"] != "OK":
            return [False] * len(problems), [0] * len(problems)

        submissions = data["result"]
        solved_mask = [False] * len(problems)
        completion_times = [0.0] * len(problems)

        for i, problem in enumerate(problems):
            target_contest = problem.get("contestId")
            target_index = problem.get("index")
            
            for sub in submissions:
                # Check timeframe
                if sub.get("creationTimeSeconds", 0) < start_time:
                    continue
                    
                # Check verdict
                if sub.get("verdict") != "OK":
                    continue
                    
                # Check problem identity
                p = sub.get("problem", {})
                if p.get("contestId") == target_contest and p.get("index") == target_index:
                    solved_mask[i] = True
                    # Use the earliest solve time if multiple (though rare in short timeframe)
                    # creationTimeSeconds is int, but we use float for comparison generally
                    completion_times[i] = sub.get("creationTimeSeconds")
                    break # Found solve for this problem
        
        return solved_mask, completion_times

# Global instance or instantiate in Cog? 
# Instantiate in Cog is better for passing session.
