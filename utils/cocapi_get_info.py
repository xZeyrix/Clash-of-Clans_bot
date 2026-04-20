import httpx
import asyncio
from datetime import datetime, timezone
from config import config

API_KEY = config.coc_api_key
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

            if response.status_code != 200:
                url = f"https://api.clashofclans.com/v1/clans/{tag}/currentwar"
                response = await client.get(url=url, headers=headers)
                war = response.json()

                prepStartTime, startTime, endTime, currentTime = str(war["preparationStartTime"]), str(war["startTime"]), str(war["endTime"]), str(datetime.now(timezone.utc))
                normPrepStartTime, normStartTime, normEndTime, normCurrentTime = normalizeCocTime(prepStartTime), normalizeCocTime(startTime), normalizeCocTime(endTime), normalizeDateTime(currentTime)
                warState, teamSize, attacksPerMember = war["state"], war["teamSize"], war["attacksPerMember"]
                clanName, opponentName = war["clan"]["name"], war["opponent"]["name"]
                clanStars, clanDestruction, opponentStars, opponentDestruction = war["clan"]["stars"], war["clan"]["destructionPercentage"], war["opponent"]["stars"], war["opponent"]["destructionPercentage"]
                clanMembers, opponentMembers = list(), list()
                def addMemberAttacks(members, type: str):
                    for member in war[type]["members"]:
                        try:
                            attacks = list()
                            for attack in member["attacks"]:
                                attacks.append({"звезды": attack["stars"], "процент разрушения": attack["destructionPercentage"]})
                            members.append({"ник": member["name"], "сделано атак": f"{len(attacks)} из {attacksPerMember}", "атаки": attacks})
                        except Exception as e:
                            members.append({"ник": member["name"], "сделано атак": f"0 из {attacksPerMember}"})
                            
                addMemberAttacks(clanMembers, "clan")
                addMemberAttacks(opponentMembers, "opponent")
                basicClanMembers = [x["ник"] for x in clanMembers]
                clanAttack, opponentAttack = sum(1 for x in clanMembers if x["сделано атак"] != "0 из 2"), sum(1 for x in opponentMembers if x["сделано атак"] != "0 из 2")

                matCurrentTime = datetime.fromisoformat(currentTime)
                matPrepStartTime, matStartTime, matEndTime, matCurrentTime = datetime.strptime(prepStartTime, "%Y%m%dT%H%M%S.%fZ"), datetime.strptime(startTime, "%Y%m%dT%H%M%S.%fZ"), datetime.strptime(endTime, "%Y%m%dT%H%M%S.%fZ"), matCurrentTime.replace(microsecond=0, tzinfo=None)
            
                def timeDifference(firstTime, secondTime):
                    delta = abs(firstTime - secondTime)
                    h, rem = divmod(int(delta.total_seconds()), 3600)
                    m = rem // 60
                    return f"{h:02d} часов и {m:02d} минут" # use h:02d | m:02d to convert to HH.MM
                
                if warState == "preparation":
                    return f"Идет день подготовки к войне (кв): наш клан {clanName} против {opponentName}. Подготовка к войне началась {timeDifference(matPrepStartTime, matCurrentTime)} назад, а сражение начнется через {timeDifference(matStartTime, matCurrentTime)}. У обоих кланов участвует в кв по {teamSize} человек, у каждого по {attacksPerMember} атаки. Список участников нашего клана: {basicClanMembers}"
                elif warState == "inWar":
                    return f"Идет война (кв): наш клан {clanName} (атаковали {clanAttack}/{teamSize} чел) против {opponentName} (атаковали {opponentAttack}/{teamSize} чел). Мы набрали {clanStars}/{teamSize*3} звезд, а противники {opponentStars}/{teamSize*3}. Война началась {timeDifference(matStartTime, matCurrentTime)} назад, а закончится через {timeDifference(matEndTime, matCurrentTime)}. У обоих кланов участвует в кв по {teamSize} человек, у каждого по {attacksPerMember} атаки. Список участников нашего клана: {clanMembers}"
                elif warState == "warEnded":
                    if clanStars > opponentStars:
                        warResult = "победа"
                    elif clanStars < opponentStars:
                        warResult = "поражение"
                    else:
                        if clanDestruction > opponentDestruction:
                            warResult = "победа"
                        elif clanDestruction < opponentDestruction:
                            warResult = "поражение"
                        else:
                            warResult = "ничья"
                            
                    return f"Война закончилась (кв): результат - {warResult}. Наш клан {clanName} (атаковали {clanAttack}/{teamSize} чел) сразился с {opponentName} (атаковали {opponentAttack}/{teamSize} чел). Мы набрали {clanStars}/{teamSize*3} звезд, а противники {opponentStars}/{teamSize*3}. Война длилась с {normPrepStartTime} по {normEndTime}, закончилась {timeDifference(matEndTime, matCurrentTime)} назад, новую войну еще не запустили. У обоих кланов участвовало в кв по {teamSize} человек, у каждого было по {attacksPerMember} атаки. Список участников с нашего клана, которые приняли участие в кв: {clanMembers}"
            elif response.status_code == 200:
                data = response.json()

                state = data["state"]

                if state == "inWar" or state == "preparation":
                    rounds = data["rounds"]
                    emptyRound = {"warTags": ["#0","#0","#0","#0"]}
                    activeRounds = list()
                    for r in rounds:
                        if r != emptyRound:
                            activeRounds.append(r)
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
    except Exception as e:
        print(f"🔴 Произошла ошибка get_war_status: {e}")
        return "Асуна (ты) не смогла получить данные о войне. Оптимально будет овтетить пользователю, что ты не можешь выполнить его запрос, и пусть лучше введет команду /war."