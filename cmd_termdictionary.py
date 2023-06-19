from Uncute_Rina import *
from import_modules import *

del_separators_table = str.maketrans({" ":"", "-":"", "_":""})

class TermDictionary(commands.Cog):


    def __init__(self, client: Bot):
        global RinaDB
        RinaDB = client.RinaDB
        self.client = client

    @commands.command()
    async def dictionary(self, ctx: commands.Context, term: str, public: bool = False):#, source: int = 1):
        source = 1
        def simplify(q):
            if type(q) is str:
                return q.lower().translate(del_separators_table)
            if type(q) is list:
                return [text.lower().translate(del_separators_table) for text in q]
        result_str = ""  # to make my IDE happy. Will still crash on discord if it actually tries to send it tho: 'Empty message'
        results: list[any]
        # Odd numbers will move to the next odd number if no result is found -> passing all sources until the end. Otherwise, return ""
        if source == 1 or source == 2:
            collection = RinaDB["termDictionary"]
            query = {"synonyms": term.lower()}
            search = collection.find(query)

            result = False
            results = []
            result_str = ""
            for item in search:
                if simplify(term) in simplify(item["synonyms"]):
                    results.append([item["term"],item["definition"]])
                    result = True
            if result:
                result_str += f"I found {len(results)} result{'s'*(len(results)>1)} for '{term}' in our dictionary:\n"
                for x in results:
                    result_str += f"> **{x[0]}**: {x[1]}\n"
            else:
                # if mode has been left unset, it will move to the online API dictionary to look for a definition there.
                # Otherwise, it will return the 'not found' result of the term, and end the function.
                if source == 1:
                    source = 3
                #public = False
                else:
                    cmd_mention = self.client.get_command_mention("dictionary_staff define")
                    result_str += f"No information found for '{term}' in the custom dictionary.\nIf you would like to add a term, message a staff member (to use {cmd_mention})"
                    public = False
            if len(result_str.split("\n")) > 3 and public:
                public = False
                result_str += "\nDidn't send your message as public cause it would be spammy, having this many results."
            if len(result_str) > 1999:
                result_str = f"Your search ({term}) returned too many results (discord has a 2000-character message length D:). (Please ask staff to fix this (synonyms and stuff).)"
                # debug(f"{itx.user.name} ({itx.user.id})'s dictionary search ('{term}') gave back a result that was larger than 2000 characters! Results:'\n"+', '.join(results),color="red")
                await log_to_guild(self.client, ctx.server, f":warning: **!! Warning:** {ctx.author.name} ({ctx.author.id})'s dictionary search ('{term}') gave back a result that was larger than 2000 characters!'")
        if source == 3 or source == 4:
            response_api = requests.get(f'https://en.pronouns.page/api/terms/search/{term.lower().replace("/"," ").replace("%"," ")}').text
            data = json.loads(response_api)
            if len(data) == 0:
                if source == 3:
                    source = 5
                else:
                    result_str = f"I didn't find any results for '{term}' on en.pronouns.page"
                    public = False
            # if len(data) == 0:
            #     await itx.response.send_message(f"No results found for '{term}' on en.pronouns.page... :(",ephemeral=not public)
            #     return

            # edit definitions to hide links to other pages:
            else:
                search = []
                for item in data:
                    item_db = item['definition']
                    while item['definition'] == item_db:
                        replacement = re.search("(?<==).+?(?=})",item['definition'])
                        if replacement is not None:
                            item['definition'] = re.sub("{(#.+?=).+?}", replacement.group(), item['definition'],1)
                        if item['definition'] == item_db: #if nothing changed:
                            break
                        item_db = item['definition']
                    while item['definition'] == item_db:
                        replacement = re.search("(?<={).+?(?=})",item['definition'])
                        if replacement is not None:
                            item['definition'] = re.sub("{.+?}", replacement.group(), item['definition'],1)
                        if item['definition'] == item_db: #if nothing changed:
                            break
                        item_db = item['definition']
                    search.append(item)

                # if one of the search results matches exactly with the search, give that definition
                results: list[dict] = []
                for item in search:
                    if simplify(term) in simplify(item['term'].split('|')):
                        results.append(item)
                if len(results) > 0:
                    result_str = f"I found {len(results)} exact result{'s'*(len(results)!=1)} for '{term}' on en.pronouns.page! \n"
                    for item in results:
                        result_str += f"> **{', '.join(item['term'].split('|'))}:** {item['definition']}\n"
                    result_str += f"{len(search)-len(results)} other non-exact results found."*((len(search)-len(results)) > 0)
                    if len(result_str) > 1999:
                        result_str = f"Your search ('{term}') returned a too-long result! (revolt has a 2000-character message length D:). To still let you get better results, I've rewritten the terms so you might be able to look for a more specific one:"
                        for item in results:
                            result_str += f"> {', '.join(item['term'].split('|'))}\n"
                    await ctx.channel.send(result_str)
                    return

                # if search doesn't exactly match with a result / synonym
                result_str = f"I found {len(search)} result{'s'*(len(results)!=1)} for '{term}' on en.pronouns.page! "
                if len(search) > 25:
                    result_str += "Here is a list to make your search more specific:\n"
                    results: list[str] = []
                    for item in search:
                        temp = item['term']
                        if "|" in temp:
                            temp = temp.split("|")[0]
                        results.append(temp)
                    result_str += ', '.join(results)
                    public = False
                elif len(search) > 2:
                    result_str += "Here is a list to make your search more specific:\n"
                    results: list[str] = []
                    for item in search:
                        if "|" in item['term']:
                            temp = "- __"  + item['term'].split("|")[0] + "__"
                            temp += " ("  + ', '.join(item['term'].split("|")[1:]) + ")"
                        else:
                            temp = "- __" + item['term'] + "__"
                        results.append(temp)
                    result_str += '\n'.join(results)
                    public = False
                elif len(search) > 0:
                    result_str += "\n"
                    for item in search:
                        result_str += f"> **{', '.join(item['term'].split('|'))}:** {item['definition']}\n"
                else:
                    result_str = f"I didn't find any results for '{term}' on en.pronouns.page!"
                    if source == 4:
                        source = 6
                msg_length = len(result_str)
                if msg_length > 1999:
                    public = False
                    result_str = f"Your search ('{term}') returned too many results ({len(search)} in total!) (discord has a 2000-character message length, and this message was {msg_length} characters D:). Please search more specifically.\n\
    Here is a link for expanded info on each term: <https://en.pronouns.page/dictionary/terminology#{term.lower()}>"
                #print(response_api.status_code)
        if source == 5 or source == 6:
            response_api = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{term.lower().replace("/","%2F")}').text
            try:
                data: any = json.loads(response_api)
            except json.decoder.JSONDecodeError: # if a bad api response is given, catch and continue as if empty results
                data: dict = {} # specify class to make IDE happy
            results = []
            if type(data) is dict:
                if source == 5:
                    source = 7
                else:
                    result_str = f"I didn't find any results for '{term}' on dictionaryapi.dev!"
                    public = False
            else:
                for result in data:
                    meanings = []
                    synonyms = []
                    antonyms = []
                    for meaning in result["meanings"]:
                        meaning_list = [meaning['partOfSpeech']]
                        # **verb**:
                        # meaning one is very useful
                        # meaning two is not as useful
                        for definition in meaning["definitions"]:
                            meaning_list.append("- "+definition['definition'])
                            for synonym in definition['synonyms']:
                                if synonym not in synonyms:
                                    synonyms.append(synonym)
                            for antonym in definition['antonyms']:
                                if antonym not in antonyms:
                                    antonyms.append(antonym)
                        for synonym in meaning['synonyms']:
                            if synonym not in synonyms:
                                synonyms.append(synonym)
                        for antonym in meaning['antonyms']:
                            if antonym not in antonyms:
                                antonyms.append(antonym)
                        meanings.append(meaning_list)

                    results.append([
                        # train
                        result["word"],
                        # [  ["noun", "- Hello there this is 1", "- number two"], ["verb", ...], [...]  ]
                        meanings,
                        ', '.join(synonyms),
                        ', '.join(antonyms),
                        '\n'.join(result["sourceUrls"])
                    ])

                pages = []
                page = 0
                for result in results:
                    result_id = 0
                    embed = CustomEmbed(colour="#816C6C")
                    embed.add_field(value=f"## __{result[0].capitalize()}__")
                    for meaning_index in range(len(result[1])):
                        _part = result[1][meaning_index][1:]
                        part = []
                        for definition in _part:
                            part.append(definition)
                        value = '\n'.join(part)
                        if len(value) > 995: # limit to 1024 chars in Value field
                            value = value[:995] + "... (shortened due to size)"
                        embed.add_field(name=result[1][meaning_index][0].capitalize(),
                                        value=value,
                                        inline=False)
                    if len(result[2]) > 0:
                        embed.add_field(name="Synonyms",
                                        value=result[2],
                                        inline=False)
                    if len(result[3]) > 0:
                        embed.add_field(name="Antonyms",
                                        value=result[3],
                                        inline=False)
                    if len(result[4]) > 0:
                        embed.add_field(name="More info:",
                                        value=result[4],
                                        inline=False)
                    pages.append(embed)
                    # [meaning, [type, definition1, definition2], synonym, antonym, sources]

                msg = PagedMessage(self.client, ctx, pages, content=f"I found the following `{len(results)}` results on dictionaryapi.dev: ")
                await msg.send()
                return
        if source == 7 or source == 8:
            response_api = requests.get(f'https://api.urbandictionary.com/v0/define?term={term.lower()}').text
            # who decided to put the output into a dictionary with a list named 'list'? {"list":[{},{},{}]}
            data = json.loads(response_api)['list']
            if len(data) == 0:
                if source == 7:
                    result_str = f"I didn't find any results for '{term}' online or in our fancy dictionaries"
                    cmd_mention_dict = self.client.get_command_mention("dictionary")
                    cmd_mention_def = self.client.get_command_mention("dictionary_staff define")
                    await log_to_guild(self.client, ctx.server, f":warning: **!! Alert:** {ctx.author.name} ({ctx.author.id}) searched for '{term}' "\
                                                                f"in the terminology dictionary and online, but there were no results. Maybe we "\
                                                                f"should add this term to the {cmd_mention_dict} command ({cmd_mention_def})")
                else:
                    result_str = f"I didn't find any results for '{term}' on urban dictionary"
                public=False
            else:
                pages = []
                page = 0
                for result in data:
                    embed = discord.Embed(color=8481900,
                                          title=f"__{result['word'].capitalize()}__",
                                          description=result['definition'],
                                          url=result['permalink'])
                    post_date = int(mktime(
                        datetime.strptime(
                            result['written_on'][:-1], # "2009-03-04T01:16:08.000Z" ([:-1] to remove Z at end)
                            "%Y-%m-%dT%H:%M:%S.%f"
                        ).timetuple()
                    ))
                    warning = ""
                    if len(result['example']) > 800:
                          warning = "... (shortened due to size)"
                    embed.add_field(name="Example",
                                    value=f"{result['example'][:800]}{warning}\n\n"
                                          f"{result['thumbs_up']}:thumbsup: :thumbsdown: {result['thumbs_down']}\n"
                                          f"Sent by {result['author']} on <t:{post_date}:d> at <t:{post_date}:T> (<t:{post_date}:R>)",
                                    inline=False)
                    pages.append(embed)

                
                msg = PagedMessage(self.client, ctx, pages, content=f"I found the following `{len(pages)}` results on urbandictionary.com: ", timeout=90)
                await msg.send()
                return

        assert len(result_str) > 0
        await ctx.send(result_str)

    admin = app_commands.Group(name='dictionary_staff', description='Change custom entries in the dictionary')

    @admin.command(name="define",description="Add a dictionary entry for a word!")
    @app_commands.describe(term="This is the main word for the dictionary entry: Egg, Hormone Replacement Therapy (HRT), (case sens.)",
                           definition="Give this term a definition",
                           synonyms="Add synonyms (SEPARATE WITH \", \")")
    async def define(self, itx: discord.Interaction, term: str, definition: str, synonyms: str = ""):
        if not is_staff(itx):
            await itx.response.send_message("You can't add words to the dictionary without staff roles!", ephemeral=True)
            return
        def simplify(q):
            if type(q) is str:
                return q.lower().translate(del_separators_table)
            if type(q) is list:
                return [text.lower().translate(del_separators_table) for text in q]
        # Test if this term is already defined in this dictionary.
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is not None:
            cmd_mention = self.client.get_command_mention("dictionary")
            await itx.response.send_message(f"You have already previously defined this term (try to find it with {cmd_mention}).", ephemeral=True)
            return
        await itx.response.defer(ephemeral=True)
        # Test if a synonym is already used before
        if synonyms != "":
            synonyms = synonyms.split(", ")
            synonyms = [simplify(i) for i in synonyms]
        else:
            synonyms = []
        if simplify(term) not in synonyms:
            synonyms.append(simplify(term))

        query = {"synonyms": {"$in": synonyms}}
        synonym_overlap = collection.find(query)
        warnings = ""
        for overlap in synonym_overlap:
            warnings += f"You have already given a synonym before in {overlap['term']}.\n"

        # Add term to dictionary
        post = {"term": term, "definition": definition, "synonyms": synonyms}
        collection.insert_one(post)

        await log_to_guild(self.client, itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) added the dictionary definition of '{term}' and set it to '{definition}', with synonyms: {synonyms}")
        await itx.followup.send(content=warnings+f"Successfully added '{term}' to the dictionary (with synonyms: {synonyms}): {definition}", ephemeral=True)

    @admin.command(name="redefine",description="Edit a dictionary entry for a word!")
    @app_commands.describe(term="This is the main word for the dictionary entry (case sens.) Example: Egg, Hormone Replacement Therapy (HRT), etc.",
                           definition="Redefine this definition")
    async def redefine(self, itx: discord.Interaction, term: str, definition: str):
        if not is_staff(itx):
            await itx.response.send_message("You can't add words to the dictionary without staff roles!", ephemeral=True)
            return
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            cmd_mention = self.client.get_command_mention("dictionary_staff define")
            await itx.response.send_message(f"This term hasn't been added to the dictionary yet, and thus cannot be redefined! Use {cmd_mention}.",ephemeral=True)
            return
        collection.update_one(query, {"$set":{"definition":definition}})

        await log_to_guild(self.client, itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) changed the dictionary definition of '{term}' to '{definition}'")
        await itx.response.send_message(f"Successfully redefined '{term}'", ephemeral=True)

    @admin.command(name="undefine",description="Remove a dictionary entry for a word!")
    @app_commands.describe(term="What word do you need to undefine (case sensitive). Example: Egg, Hormone Replacement Therapy (HRT), etc")
    async def undefine(self, itx: discord.Interaction, term: str):
        if not is_staff(itx):
            await itx.response.send_message("You can't remove words to the dictionary without staff roles!", ephemeral=True)
            return
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            await itx.response.send_message("This term hasn't been added to the dictionary yet, and thus cannot be undefined!",ephemeral=True)
            return
        await log_to_guild(self.client, itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) undefined the dictionary definition of '{term}' from '{search['definition']}' with synonyms: {search['synonyms']}")
        collection.delete_one(query)


        await itx.response.send_message(f"Successfully undefined '{term}'", ephemeral=True)

    @admin.command(name="editsynonym",description="Add a synonym to a previously defined word")
    @app_commands.describe(term="This is the main word for the dictionary entry (case sens.): Egg, Hormone Transfer Therapy, etc",
                           mode="Add or remove a synonym?",
                           synonym="Which synonym to add/remove?")
    @app_commands.choices(mode=[
            discord.app_commands.Choice(name='Add a synonym', value=1),
            discord.app_commands.Choice(name='Remove a synonym', value=2),
        ])
    async def edit_synonym(self, itx: discord.Interaction, term: str, mode: int, synonym: str):
        if not is_staff(itx):
            await itx.response.send_message("You can't add synonyms to the dictionary without staff roles!", ephemeral=True)
            return
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            cmd_mention = self.client.get_command_mention("dictionary_staff define")
            await itx.response.send_message(f"This term hasn't been added to the dictionary yet, and thus cannot get new synonyms! Use {cmd_mention}.",ephemeral=True)
            return

        if mode == 1:
            synonyms = search["synonyms"]
            if synonym.lower() in synonyms:
                await itx.response.send_message("This term already has this synonym!", ephemeral=True)
                return
            synonyms.append(synonym.lower())
            collection.update_one(query, {"$set":{"synonyms":synonyms}}, upsert=True)
            await log_to_guild(self.client, itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) added synonym '{synonym}' the dictionary definition of '{term}'")
            await itx.response.send_message("Successfully added synonym", ephemeral=True)
        if mode == 2:
            synonyms = search["synonyms"]
            if synonym.lower() not in synonyms:
                await itx.response.send_message("This term doesn't have this synonym!", ephemeral=True)
                return
            synonyms.remove(synonym.lower())
            if len(synonyms) < 1:
                await itx.response.send_message("You can't remove all the synonyms to a term! Then you can't find it in the dictionary anymore :P. First, add a synonym before removing one.", ephemeral=True)
                return
            collection.update_one(query, {"$set":{"synonyms":synonyms}}, upsert=True)
            await log_to_guild(self.client, itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) removed synonym '{synonym}' the dictionary definition of '{term}'")
            await itx.response.send_message("Successfully removed synonym", ephemeral=True)

def setup(client: Bot):
    client.add_cog(TermDictionary(client))
    # await client.add_cog(DictionaryGroup(client))
