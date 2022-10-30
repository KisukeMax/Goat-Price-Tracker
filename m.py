import discord
import os
from discord.ext import commands
import requests
import json
from tabulate import tabulate
import asyncio
import urllib3
import pandas as pd
import time

start_time = time.time()


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

selection = 0
def fetch_sku_data(keywords , selection):
    json_string = json.dumps({"params": f"distinct=true&facetFilters=()&facets=%5B%22size%22%5D&hitsPerPage=20&numericFilters=%5B%5D&page=0&query={keywords}"})
    byte_payload = bytes(json_string, 'utf-8')
    params = {
        "x-algolia-agent": "Algolia for vanilla JavaScript 3.25.1", 
        "x-algolia-application-id": "2FWOTDVM2O", 
        "x-algolia-api-key": "ac96de6fef0e02bb95d433d8d5c7038a"
    }
    header = {
        'accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'accept-language': 'en-us',
        'accept-encoding': 'br,gzip,deflate'
    }
    with requests.Session() as s:
        r = s.post("https://2fwotdvm2o-dsn.algolia.net/1/indexes/product_variants_v2/query", params=params, verify=False, data=byte_payload, timeout=30)
    results = r.json()["hits"][selection]
    generalAPI = f"https://www.goat.com/api/v1/product_templates/{results['slug']}/show_v2"
    offerAPI = f"https://www.goat.com/api/v1/highest_offers?productTemplateId={results['id']}"
    askAPI = f"https://www.goat.com/api/v1/product_variants?productTemplateId={results['slug']}"
    general = requests.get(generalAPI, headers=header).json()
    bids = requests.get(offerAPI, headers=header).json()
    asks = requests.get(askAPI, headers=header).json()
    link = f"https://goat.com/sneakers/{results['slug']}"

    priceDict = {}
    for size in general['sizeOptions']:
            priceDict[float(size["value"])] = {"ask": 0, "bid": 0}
    for ask in general['availableSizesNewV2']:
        if ask[2] == "good_condition":
            priceDict[float(ask[0])]["ask"] = ask[1][:-2]
    for bid in bids:
        if bid["size"] in priceDict:
            priceDict[bid["size"]]["bid"] = str(bid["offerAmountCents"]["amountUsdCents"])[:-2]
    for ask in asks:
        if ask["boxCondition"] == "good_condition":
            priceDict[ask["size"]]["ask"] = str(ask["lowestPriceCents"]["amountUsdCents"])[:-2]

    if general["productCategory"] == "clothing":
        priceDict2 = {}
        for size in priceDict:
            for size2 in general["sizeOptions"]:
                if size == size2["value"]:
                    priceDict2[size2["presentation"].upper()] = priceDict[size]
        priceDict = priceDict2

    priceDict = {k: v for k,v in priceDict.items() if v["ask"] != 0 or v["bid"] != 0}
        
    return priceDict
    
# print(fetch_sku_data("553558-612" ,selection))
# print(fetch_sku_data("553558-612" ,0))


df = pd.read_excel("data.xlsx")


Fetched_sku = {}

for i ,  row in df.iterrows():
    if not pd.isnull(row.get("SKU")):
        # print(row.get("SKU"))
        if not Fetched_sku.get(row.get("SKU")):
            try:
                price = fetch_sku_data(row.get("SKU") , 0).get(row["Size"]).get("ask")
                # print(price)
                Fetched_sku[row.get("SKU")] = price
                df.at[i , 'Price' ] = price
            except:
                pass
        else:
            df.at[i , 'Price' ] = Fetched_sku.get(row.get("SKU"))
            
            
# len(Fetched_sku)
df.to_csv("data.csv" , index =  False)

print("--- %s seconds ---" % (time.time() - start_time))