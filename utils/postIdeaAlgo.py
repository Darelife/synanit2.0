from matplotlib import pyplot as plt
import requests
import io

algoRanksOnly = []

def get_color_by_rating(rating):
    if rating > 2400:
        return "red", "GM"
    elif rating > 2200:
        return "orange", "M"
    elif rating > 1900:
        return "purple", "CM"
    elif rating > 1600:
        return "blue", "E"
    elif rating > 1400:
        return "cyan", "S"
    elif rating > 1200:
        return "green", "P"
    else:
        return "gray", "N"

def getData(contestId):
    url = f"https://codeforces.com/api/contest.standings?contestId={contestId}&showUnofficial=false"
    response = requests.get(url)
    data = response.json().get("result", {}).get("rows", [])
    
    rankings = []
    points = []
    
    url = "https://algoxxx.onrender.com/database"
    try:
        response = requests.get(url, timeout=5)
        users_data = response.json()
        users = [i["cfid"].lower() for i in users_data]
    except:
        users = []
    
    algoRanks = []
    for entry in data:
        try:
            rank = entry["rank"]
            rankings.append(rank)
            points.append(entry["points"] * 500 - entry["penalty"])
            
            handle = entry["party"]["members"][0]["handle"].lower()
            if handle in users:
                algoRanks.append(
                    {
                        "user": handle,
                        "rank": rank,
                        "points": entry["points"] * 500 - entry["penalty"],
                    }
                )
                algoRanksOnly.append(rank)
        except Exception as e:
            pass
            
    algoRanksOnly.sort()
    
    # Sort algoRanks by rank
    algoRanks.sort(key=lambda x: x["rank"])
    
    # Get ratings
    users_in_contest = [i["user"].lower() for i in algoRanks]
    if users_in_contest:
        handles = ";".join(users_in_contest)
        urrl = f"https://codeforces.com/api/user.info?handles={handles}&checkHistoricHandles=false"
        try:
            response = requests.get(urrl, timeout=5)
            if response.status_code == 200:
                user_info = response.json().get("result", [])
                # Map ratings
                rating_map = {u["handle"].lower(): u.get("rating", 0) for u in user_info}
                for i in algoRanks:
                    i["rating"] = rating_map.get(i["user"], 0)
            else:
                 for i in algoRanks: i["rating"] = 0
        except:
             for i in algoRanks: i["rating"] = 0
             
    return rankings, points, algoRanks, points, rankings

def adjust_y_positions(y_positions, y, min_distance):
    for prev_y in y_positions:
        if abs(prev_y - y) < min_distance:
            y += min_distance
    return y

def plotStuff(contestId: int, display_limit: int = 10):
    x, y, algoRanks, points, rankings = getData(contestId)
    
    if not points:
        return None

    # Plot settings
    plt.style.use("dark_background")
    plt.figure(figsize=(11, 6))

    line_color = "#00FF7F"
    arrow_color = "#FFD700"
    font_properties = {"family": "monospace", "weight": "bold", "size": 10}

    min_distance = max(points) * 0.05
    y_positions = []

    for i, data in enumerate(algoRanks[:display_limit]):
        x_value = data["rank"]
        y_value = data["points"]
        plt.vlines(x_value, 0, y_value, colors=line_color, linestyles="--", alpha=0.7)

        adjusted_y_value = adjust_y_positions(y_positions, y_value, min_distance) + 30
        y_positions.append(adjusted_y_value)
        user_text = data["user"]

        plt.annotate(
            user_text,
            xy=(x_value, y_value),
            xytext=(x_value, adjusted_y_value),
            arrowprops=dict(facecolor=arrow_color, arrowstyle="-", lw=1, alpha=0.6),
            fontsize=10,
            fontproperties=font_properties,
            color=arrow_color,
            verticalalignment="bottom",
            horizontalalignment="center",
        )

    plt.plot(rankings, points, color=line_color, linewidth=2, alpha=0.8)
    
    if algoRanksOnly and len(algoRanksOnly) > display_limit:
        xlim_max = algoRanksOnly[display_limit] + 1000
    elif algoRanksOnly:
        xlim_max = max(algoRanksOnly) + 100
    else:
        xlim_max = max(rankings) if rankings else 100
        
    plt.xlim(0, xlim_max)
    plt.ylim(0, max(points) * 1.1)
    
    plt.title(
        f"Rank vs Points for Contest {contestId}",
        fontsize=16,
        color="#FFD700",
        fontweight="bold",
    )
    plt.xlabel("Rank", fontsize=14, color="#FFD700")
    plt.ylabel("Points", fontsize=14, color="#FFD700")

    plt.gca().set_facecolor("#1e1e1e")
    plt.tick_params(colors="#FFD700", which="both")
    plt.grid(color="#444444", linestyle="-", linewidth=0.5, alpha=0.5)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf
