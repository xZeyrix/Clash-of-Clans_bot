import requests
API_KEY = "api key"
tag = "%239G29PC8U"

def get_cwl_prep_members():
    url = f"https://api.clashofclans.com/v1/clans/{tag}/currentwar/leaguegroup"
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    data = response.json()
    for clan in data["clans"]:
        if clan["tag"] == "#9G29PC8U":
            members = list()
            for member in clan["members"]:
                members.append(member["name"] + " - " + str(member["townHallLevel"]) + "тх")
            break
    return members
def get_cwl_status():
    url = f"https://api.clashofclans.com/v1/clans/{tag}/currentwar/leaguegroup"
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    data = response.json()
    return data["state"]
def get_clan_members():
    url = f"https://api.clashofclans.com/v1/clans/{tag}/members"
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    data = response.json()
    role = {"member":"участник", "admin":"старик", "coLeader":"сорук", "leader":"глава"}
    members = list()
    for member in data["items"]:
        argument = "ник:" + member["name"] + " роль:" + role[member["role"]] + " лига:" + member["leagueTier"]["name"]
        members.append(argument)
    return members
def get_raids():
    url = f"https://api.clashofclans.com/v1/clans/{tag}/capitalraidseasons"
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    data = response.json()["items"][0]
    output = {"статус":data["state"],"начало": data["startTime"][:8], "конец": data["endTime"][:8], "пройденоРейдов": str(data["raidsCompleted"])}
    return output
def get_clan_info():
    url = f"https://api.clashofclans.com/v1/clans/{tag}"
    response = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    data = response.json()
    output = {"тег":data["tag"], "название":data["name"], "лвлКлана":data["clanLevel"], "квСерияПобед":data["warWinStreak"], "квПобеды": data["warWins"], "квНичьи": data["warTies"], "квПоражения": data["warLosses"], "лигаЛВК": data["warLeague"]["name"], "всегоСоклановцев": data["members"], "ссылкаНаКлан": f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={tag}"}
    return output
def get_clan_war():
    return "Информация о войне недоступна"