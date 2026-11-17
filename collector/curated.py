#!/usr/bin/env python3
"""X handles for the Motion leaderboard names, curated and checked by hand.

Motion's leaderboard API exposes only id, name, position and delta, so there is
no handle to read. Guessing one from the name was tried first and produced the
wrong person often enough to be worthless (Coffeezilla resolved to an unrelated
private account, Mark Cuban to a 3k-follower impostor, "Andy" to Andy Cohen).
This file replaces the guessing: every handle below was supplied deliberately,
then confirmed against X at build time — the account must exist, be verified and
clear a thousand followers before it is used.

The last five were open questions for a while and are now settled on someone's
word rather than a guess: Zohran Mamdani uses the office account @NYCMayor, Greg
is @greg16676935420, Jason is Jason Calacanis, and Andy is Andy Cohen. Nobody
here should "fix" those by reasoning from the display name — the person who owns
this board made each call.

Two of them do not obviously match the Motion display name, and that is expected:

  @NYCMayor  displays as "Mayor Zohran Kwame Mamdani", not "Zohran Mamdani"
  @Jason     displays as "@jason"

That is exactly why the curated path skips the name-similarity test and only
checks existence, verification and the follower floor.

NOTE: Motion lowercases some names ("rasmr", "greg"). Matching is case-folded
so that does not matter.
"""

CURATED = {
    "IShowSpeed": "ishowspeedsui",
    "Marques Brownlee": "MKBHD",
    "Ludwig": "LudwigAhgren",
    "Kai Cenat": "KaiCenat",
    "Pat McAfee": "PatMcAfeeShow",
    "Lex Fridman": "lexfridman",
    "Bryan Johnson": "bryan_johnson",
    "Jake Paul": "jakepaul",
    "Gary Vaynerchuk": "garyvee",
    "Shams Charania": "ShamsCharania",
    "Greg Isenberg": "gregisenberg",
    "Dave Portnoy": "stoolpresidente",
    "Jake Lucky": "JakeSucky",
    "Druski": "druski",
    "Valkyrae": "Valkyrae",
    "DJ Akademiks": "Akademiks",
    "Andrew Huberman": "hubermanlab",
    "Grimes": "Grimezsz",
    "Theo Von": "TheoVon",
    "Naval": "naval",
    "Coffeezilla": "coffeebreak_YT",
    "Michael Saylor": "saylor",
    "Clemente": "clementetv_",
    "Ansem": "blknoiz06",
    "MINHxDYNASTY": "MINHxDYNASTY",
    "Logan Paul": "LoganPaul",
    "Mark Cuban": "mcuban",
    "Mark Rober": "MarkRober",
    "David Senra": "davidsenra",
    "DogeDesigner": "cb_doge",
    "Jim Cramer": "jimcramer",
    "David Sacks": "DavidSacks",
    "Chamath Palihapitiya": "chamath",
    "Threadguy": "notthreadguy",
    "Garry Tan": "garrytan",
    "rasmr": "rasmr_eth",
    "Murray Hill Guy": "MurrayHillGuy1",
    "Sir Doge of the Coin": "dogeofficialceo",
    "Flood": "ThinkingUSD",
    "Beff Jezos": "beffjezos",
    "PlaqueBoyMax": "PlaqueBoyMax",
    "ChooseRich": "chooserich",
    "Bill Ackman": "BillAckman",
    "Jack Butcher": "jackbutcher",
    "Roon": "tszzl",
    "AlexFinn": "AlexFinn",
    "Palmer Luckey": "PalmerLuckey",
    "Martin Shkreli": "MartinShkreli",
    "Tarek Mansour": "mansourtarek_",
    "Mert Mumtaz": "mert",
    "Balaji": "balajis",
    "Nikita Bier": "nikitabier",
    "Paul Graham": "paulg",
    "Taiki Maeda": "TaikiMaeda2",
    "Brian Armstrong": "brian_armstrong",
    "Tim Dillon": "TimJDillon",
    "Toly": "toly",
    "Mike Solana": "micsolana",
    "John Coogan": "johncoogan",
    "xQc": "xQc",
    "Vlad Tenev": "vladtenev",
    "Andrej Karpathy": "karpathy",
    "Haseeb Qureshi": "hosseeb",
    "Aaron Levie": "levie",
    "Marc Andreessen": "pmarca",
    "Vitalik Buterin": "VitalikButerin",
    "Dylan Field": "zoink",
    "Jordi Hays": "jordihays",
    "Kai Trump": "kaitrump",
    "David Holz": "DavidSHolz",
    "Cobie": "cobie",
    "Jynxzi": "jynxzi",
    "Chris Dixon": "cdixon",
    "Shayne Coplan": "shayne_coplan",
    "Brian Chesky": "bchesky",
    "Zohran Mamdani": "NYCMayor",
    "Greg": "greg16676935420",
    "Jason": "Jason",
    "Andy": "Andy",
}

UNCONFIRMED: dict[str, str] = {}
