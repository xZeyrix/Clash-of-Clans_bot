import httpx
import asyncio
from datetime import datetime, timezone
from config import COC_API_TOKEN

API_KEY = COC_API_TOKEN
tag = "%239G29PC8U"
basicTag = "#9G29PC8U"
headers = {"Authorization": f"Bearer {API_KEY}"}

def normalizeCocTime(time):
    return time[0:4] + "-" + time[4:6] + "-" + time[6:8] + " " + str(int(time[9:11]) + 3) + ":" + time[11:13] + " МСК"
def normalizeDateTime(time):
    return time[0:10] + " " + str(int(time[11:13]) + 3) + ":" + time[14:16] + " МСК"

async def get_cwl_prep_members():
    url = f"https://api.clashofclans.com/v1/clans/{tag}/currentwar/leaguegroup"
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers)
        data = response.json()
        for clan in data["clans"]:
            if clan["tag"] == "#9G29PC8U":
                members = list()
                for member in clan["members"]:
                    members.append(member["name"] + " - " + str(member["townHallLevel"]) + "тх")
                break
        return members
async def get_cwl_status():
    url = f"https://api.clashofclans.com/v1/clans/{tag}/currentwar/leaguegroup"
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers)
        data = response.json()
        return data["state"]
async def get_clan_members():
    url = f"https://api.clashofclans.com/v1/clans/{tag}/members"
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers)
        data = response.json()
        role = {"member":"участник", "admin":"старик", "coLeader":"сорук", "leader":"глава"}
        members = list()
        for member in data["items"]:
            argument = "ник:" + member["name"] + " роль:" + role[member["role"]] + " лига:" + member["leagueTier"]["name"]
            members.append(argument)
        response = {
            "membersTotalCount": len(members),
            "membersList": members
        }
        return response
async def get_raids():
    url = f"https://api.clashofclans.com/v1/clans/{tag}/capitalraidseasons"
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers)
        data = response.json()["items"][0]
        start, end, current = str(data["startTime"]), str(data["endTime"]), str(datetime.now(timezone.utc))
        startTime, endTime, currentTime = normalizeCocTime(start), normalizeCocTime(end), normalizeDateTime(current)
        output = {"статус":data["state"],"начало":startTime, "конец": endTime, "текущая дата&время":currentTime, "пройденоРейдов": str(data["raidsCompleted"])}
        return output
async def get_clan_info():
    url = f"https://api.clashofclans.com/v1/clans/{tag}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers)
        data = response.json()
        output = {"тег":data["tag"], "название":data["name"], "лвлКлана":data["clanLevel"], "квСерияПобед":data["warWinStreak"], "квПобеды": data["warWins"], "квНичьи": data["warTies"], "квПоражения": data["warLosses"], "лигаЛВК": data["warLeague"]["name"], "всегоСоклановцев": data["members"], "ссылкаНаКлан": f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={tag}"}
        return output
async def get_war_status():
    try:
        tag = "%239G29PC8U"
        url = f"https://api.clashofclans.com/v1/clans/{tag}/currentwar/leaguegroup"
        async with httpx.AsyncClient() as client:
            response = await client.get(url=url, headers=headers)
            data = response.json()

            state = data["state"]

            if state == "inWar" or state == "preparation":
                rounds = data["rounds"]
                emptyRound = {"warTags": ["#0","#0","#0","#0"]}
                activeRounds = list()
                for round in rounds:
                    if round != emptyRound:
                        activeRounds.append(round)
                if len(activeRounds) == 1:
                    warTags = activeRounds[0]["warTags"]
                    warDay = 0
                elif len(activeRounds) == 7:
                    warTags = activeRounds[-1]["warTags"]
                    for tag in warTags:
                        if tag != "#0":
                            warTag = tag
                    warTag = "%23" + warTags[0][1:]
                    warUrl = f"https://api.clashofclans.com/v1/clanwarleagues/wars/{warTag}"
                    warResponse = await client.get(url=warUrl, headers=headers)
                    war = warResponse.json()
                    if war["state"] == "inWar":
                        warTags = activeRounds[-1]["warTags"]
                        warDay = 7
                    elif war["state"] == "preparation":
                        warTags = activeRounds[-2]["warTags"]
                        warDay = 6
                else:
                    warTags = activeRounds[-2]["warTags"]
                    warDay = len(activeRounds)-1
                
                for warTag in warTags:
                    warTag = "%23" + warTag[1:]
                    warUrl = f"https://api.clashofclans.com/v1/clanwarleagues/wars/{warTag}"
                    warResponse = await client.get(url=warUrl, headers=headers)
                    war = warResponse.json()
                    if war["clan"]["tag"] == basicTag or war["opponent"]["tag"] == basicTag:
                        warState = war["state"]
                        warTeamSize = war["teamSize"]


                        prepStartTime, startTime, endTime, currentTime = str(war["preparationStartTime"]), str(war["startTime"]), str(war["endTime"]), str(datetime.now(timezone.utc))
                        prepStartTime, startTime, endTime, currentTime = normalizeCocTime(prepStartTime), normalizeCocTime(startTime), normalizeCocTime(endTime), normalizeDateTime(currentTime)

                        clan = war["clan"]
                        opponent = war["opponent"]

                        clanAttacks, clanStars = clan["attacks"], clan["stars"]
                        opponentAttacks, opponentStars = opponent["attacks"], opponent["stars"]

                        members = list()
                        for member in clan["members"]:
                            try:
                                attacks = list()
                                for attack in member["attacks"]:
                                    attacks.append({"звезды": attack["stars"], "процент разрушения": attack["destructionPercentage"]})
                                members.append({"ник": member["name"], "тх": member["townhallLevel"], "сделано атак": "1 из 1", "атаки": attacks})
                            except Exception as e:
                                members.append({"ник": member["name"], "тх": member["townhallLevel"], "атаки": "0 из 1"})
                        return {"тип": "лвк", "статус": warState, "день": f"{warDay} из 7", "размер": f"{warTeamSize} на {warTeamSize}", "звезды (мы vs противник)": f"{clanStars}/{warTeamSize*3} VS {opponentStars}/{warTeamSize*3}", "атаки (мы vs противник)": f"{clanAttacks}/{warTeamSize} VS {opponentAttacks}/{warTeamSize}", "начало": startTime, "конец (после конца идет след день)": endTime, "текущее время": currentTime, "участники": members}
    except:
        print(f"🔴 Произошла ошибка get_war_status: {e}")
        return "В ходе получения данных о войне произошла ошибка. Ответь пользователю, что тебе лень выполнять его запрос. А также, порекомендуй ему ввести команду /war."

# async def main():
#     print(await get_war_status())
# asyncio.run(main())