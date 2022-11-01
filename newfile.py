import gspread
import json
import pandas as pd
from tqdm import tqdm
from oauth2client.service_account import ServiceAccountCredentials
import requests
import urllib3
from fake_useragent import FakeUserAgent
import time
import random


ua = FakeUserAgent()

p = "http://sweet7068:8I7gDxWY47kc2RXs@proxy.packetstream.io:31112"

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
        # 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'user-agent' : ua.random ,
        'accept-language': 'en-us',
        'accept-encoding': 'br,gzip,deflate'
    }
    with requests.Session() as s:
        r = s.post("https://2fwotdvm2o-dsn.algolia.net/1/indexes/product_variants_v2/query", params=params, verify=False, data=byte_payload, timeout=30)
    results = r.json()["hits"][selection]
    # print(results['slug'])
    generalAPI = f"https://www.goat.com/api/v1/product_templates/{results['slug']}/show_v2"
    offerAPI = f"https://www.goat.com/api/v1/highest_offers?productTemplateId={results['id']}"
    askAPI = f"https://www.goat.com/api/v1/product_variants?productTemplateId={results['slug']}"
    general = requests.get(generalAPI, headers = header, proxies = {"http" : p, "https" : p} , ).json()
    bids = requests.get(offerAPI, headers=header, proxies = {"http" : p, "https" : p}).json()
    asks = requests.get(askAPI, headers=header, proxies = {"http" : p, "https" : p}).json()
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



scope_app =['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive'] 
    # #credentials to the account
cred = ServiceAccountCredentials.from_json_keyfile_name('config.json',scope_app) 

    # # authorize the clientsheet 
client = gspread.authorize(cred)

    # #open sheet to update
googlesheet = client.open('JJ SNEAKERS STORE')
    # #open Tab in sheet to update
worksheet1 = googlesheet.worksheet("Goat Price")
worksheet_dataframe = pd.DataFrame(worksheet1.get_all_records())

Fetched_sku = {}
for i, row in tqdm(worksheet_dataframe.iterrows() , total=worksheet_dataframe.shape[0]):
    if not pd.isnull(row.get("SKU")):
        if not Fetched_sku.get(row.get("SKU")):
            try:
                price_data = fetch_sku_data(row.get("SKU") , 0)
                Fetched_sku[row.get("SKU")] = price_data
                worksheet_dataframe.at[i , 'Goat Lowest Price' ] = Fetched_sku.get(row.get("SKU")).get(row.get("Size In US")).get("ask")
                time.sleep(random.randint(1,10))
                print("sleeping")
            except Exception as e:
                print(e)
                time.sleep(random.randint(1,10))
                print("error sleeping")

                # pass
        else:            
            try:
                print(Fetched_sku.get(row.get("SKU")))
                worksheet_dataframe.at[i , 'Goat Lowest Price' ] = Fetched_sku.get(row.get("SKU")).get(row.get("Size In US")).get("ask")
            except:
                pass
    if i > 1000:
        break
            
            
print("updating sheets")
worksheet_dataframe.to_csv("data.csv" , index =  False)
dataframe_to_upload = worksheet_dataframe.fillna("")
worksheet1.update([dataframe_to_upload.columns.values.tolist()] + dataframe_to_upload.values.tolist())
print("sheets updated")
time.sleep(5)
