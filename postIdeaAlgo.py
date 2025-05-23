from matplotlib import pyplot as plt
import requests

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
    data = response.json()["result"]["rows"]
    url2 = f"https://codeforces.com/api/contest.ratingChanges?contestId={contestId}"
    response2 = requests.get(url2)
    data2 = response2.json()["result"]

    # Initialize rankings and points lists
    rankings = []
    points = []
    perf = []

    # Read users from file
    # with open("./ignore/users.txt", "r") as f:
    #     users = f.read().split("\n")
    url = "https://algoxxx.onrender.com/database"
    response = requests.get(url)
    users_data = response.json()
    users = []
    for i in users_data:
        users.append(i["cfid"].lower())
    
    # print(users)

    # Collect data for users
    algoRanks = []
    for i in data:
        try:
            entry = i
            # perfStuff = data2[i]
            # oldRating = perfStuff["oldRating"]
            # newRating = perfStuff["newRating"]
            rank = entry["rank"]
            rankings.append(entry["rank"])
            points.append(entry["points"] * 500 - entry["penalty"])
            # perf.append(oldRating + (newRating - oldRating) * 4)

            if entry["party"]["members"][0]["handle"].lower() in [u.lower() for u in users]:
                algoRanks.append(
                    {
                        "user": entry["party"]["members"][0]["handle"].lower(),
                        "rank": entry["rank"],
                        "points": entry["points"] * 500 - entry["penalty"],
                        # "performance": oldRating + (newRating - oldRating) * 4
                    }
                )
                algoRanksOnly.append(entry["rank"])
        except:
            pass
    algoRanksOnly.sort()
    x = rankings
    y = points
    # Sort algoRanks by rank
    algoRanks.sort(key=lambda x: x["rank"])
    users = [i["user"].lower() for i in algoRanks]
    handles = ";".join(users)
    urrl = f"https://codeforces.com/api/user.info?handles={handles}&checkHistoricHandles=false"
    response = requests.get(urrl)
    data = response.json()["result"]
    for i in range(len(data)):
        algoRanks[i]["rating"] = data[i]["rating"]
    return x, y, algoRanks, points, rankings


# Function to adjust y position to avoid overlap
def adjust_y_positions(y_positions, y, min_distance):
    for prev_y in y_positions:
        if abs(prev_y - y) < min_distance:
            y += min_distance
    return y


def plotStuff(contestId: int, display_limit: int = 10):
    x, y, algoRanks, points, rankings = getData(contestId)
    # Plot settings
    plt.style.use("dark_background")
    plt.figure(figsize=(11, 6))

    # Colors and styling
    line_color = "#00FF7F"
    point_color = "#FF1493"
    arrow_color = "#FFD700"
    font_properties = {"family": "monospace", "weight": "bold", "size": 10}

    # Draw vertical lines and add annotations with arrows
    min_distance = max(points) * 0.05
    y_positions = []

    for i, data in enumerate(algoRanks[:display_limit]):
        x_value = data["rank"]
        y_value = data["points"]
        plt.vlines(x_value, 0, y_value, colors=line_color, linestyles="--", alpha=0.7)

        # Adjust y position to avoid overlap
        adjusted_y_value = adjust_y_positions(y_positions, y_value, min_distance) + 30
        y_positions.append(adjusted_y_value)
        user_text = data["user"]

        circle_color, suffix = get_color_by_rating(data["rating"])
        # TODO: need to decide whether to show the suffix or not
        # user_text += f"({suffix})"
        plt.annotate(
            user_text,
            xy=(x_value, y_value),
            xytext=(x_value, adjusted_y_value),
            arrowprops=dict(facecolor=arrow_color, arrowstyle="-", lw=1, alpha=0.6),
            fontsize=10,
            fontproperties=font_properties,
            # color=color,
            color=arrow_color,
            verticalalignment="bottom",
            horizontalalignment="center",
        )
        # # # DejaVu Sans Mono
        # # font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", 10)
        # # size = font.getsize(user_text)
        # # print(size)
        # text_length_estimate = len(user_text) * 23  # Adjust multiplier based on your scale and font size
        # print(text_length_estimate, x_value)
        # circle_x = x_value + 3*text_length_estimate  # Adjust this value as needed
        # circle_y = adjusted_y_value + 30

        # # Draw circle
        # plt.scatter(circle_x, circle_y, s=30, color=circle_color)

    # Plot line
    plt.plot(rankings, points, color=line_color, linewidth=2, alpha=0.8)
    # Plot settings
    plt.xlim(0, (algoRanksOnly[display_limit]) + 1000)
    plt.ylim(0, max(points) * 1.1)
    plt.title(
        f"Rank vs Points for Contest {contestId}",
        fontsize=16,
        color="#FFD700",
        fontweight="bold",
    )
    plt.xlabel("Rank", fontsize=14, color="#FFD700")
    plt.ylabel("Points", fontsize=14, color="#FFD700")

    # Set background color for the plot
    plt.gca().set_facecolor("#1e1e1e")

    # Customize ticks and grid
    plt.tick_params(colors="#FFD700", which="both")
    plt.grid(color="#444444", linestyle="-", linewidth=0.5, alpha=0.5)

    # plt.show()
    plt.savefig("plot.png")
