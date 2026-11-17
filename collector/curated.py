#!/usr/bin/env python3
"""X handles for the Motion leaderboard names, curated and checked by hand.

Motion's leaderboard API exposes only id, name, position and delta, so there is
no handle to read. Guessing one from the name was tried first and produced the
wrong person often enough to be worthless (Coffeezilla resolved to an unrelated
private account, Mark Cuban to a 3k-follower impostor, "Andy" to Andy Cohen).
This file replaces the guessing: every handle below was supplied deliberately,
then confirmed against X at build time — the account must exist, be verified and
clear a thousand followers before it is used.

FOUR NAMES ARE DELIBERATELY ABSENT. Adding a guess for them would put a real
stranger's face on someone else's row:

  Zohran Mamdani  two plausible accounts (@ZohranKMamdani personal,
                  @NYCMayor the office) and no way to tell which one the board
                  means, so neither is used
  Greg            @greg16676935420 looks right but nothing ties it to the Greg
                  at rank 28
  Jason           Jason Calacanis is the likeliest, still unconfirmed
  Andy            @Andy, @ajassy, @andy_murray and @AndyAyrey all miss

Those four rows show Motion's own avatar with initials and the card says the
account could not be confirmed. Supply a handle and it can be added here.

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
}

UNCONFIRMED = {
    "Zohran Mamdani": "two candidates: @ZohranKMamdani personal, @NYCMayor office",
    "Greg": "likely @greg16676935420, nothing ties it to rank 28",
    "Jason": "likely Jason Calacanis @Jason, unconfirmed",
    "Andy": "@Andy, @ajassy, @andy_murray, @AndyAyrey none fit",
}
