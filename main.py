from datetime import datetime
from binance.client import Client
from dotenv import load_dotenv
import requests
import json
import os


load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
COINMARKETCAP_AUTH_KEY = os.getenv("COINMARKETCAP_AUTH_KEY")

SYMBOLS = ['CHZ', 'ATOM', 'NEO', 'XMR', 'DOGE', 'OMG', 'MTL', 'OXT', 'EOS', 'DOT', 'SOL', 'XLM', 'SXP', 'ENJ', 'LTC', 'BTC', 'HOT', 'CHR', 'MATIC', 'COTI', 'ADA', 'BAT', 'UNI', 'BNB', 'AVAX', 'LINK', 'STMX']

dir_path = os.path.dirname(os.path.realpath(__file__))

COINS_JSON_NAME = 'coins.json'
ORDERS_JSON_NAME = 'synced_orders.json'

COINS_JSON_PATH = os.path.join(dir_path, COINS_JSON_NAME)
ORDERS_JSON_PATH = os.path.join(dir_path, ORDERS_JSON_NAME)

print('COINS_JSON_PATH', COINS_JSON_PATH)
print('ORDERS_JSON_PATH', ORDERS_JSON_PATH)

coins = None
proccessed_orders = list()

with open(COINS_JSON_PATH) as json_file:
  coins = json.load(json_file)

with open(ORDERS_JSON_PATH) as json_file:
  proccessed_orders = json.load(json_file)

def get_coin_id(symbol):
  return coins[symbol]


def mark_order_as_synced(id: int):
  proccessed_orders.append(id)
  with open(ORDERS_JSON_PATH, 'w') as outfile:
      json.dump(proccessed_orders, outfile)

def parse_order(order):
    id = order['orderId']
   
    timestamp_milis = int(order['updateTime'])
    timestamp_secs = int(timestamp_milis/1000)
    date = datetime.fromtimestamp(timestamp_secs)
   
    price = float(order['price'])
    total_value = float(order['cummulativeQuoteQty'])
    qty = float(order['executedQty'])
    side = order['side']

    if price == 0:
        price = total_value/qty

    return id, date, price, qty, side, 

headers = {
  'authorization': 'Basic ' + COINMARKETCAP_AUTH_KEY,
  'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
}
def add_transaction_in_portfolio(coin_id: int, side: str, quantity: float, price: float, transactionTime: datetime, fee: float = 0, note: str = ""):
  payload = {
    "amount": str(quantity),
    "price": price,
    "transactionTime": transactionTime.isoformat(),
    "fee": str(fee),
    "note": note,
    "transactionType": side, 
    "cryptocurrencyId": coin_id,
    "cryptoUnit": 2781, 
    "fiatUnit": 2781,
    "portfolioSourceId": "default"
  }

  # print('payload', payload)

  r = requests.post(
    "https://api.coinmarketcap.com/asset/v3/portfolio/add",
    json=payload,
    headers=headers
  )

  res = r.json()

  if res['status']['error_message'] != 'SUCCESS':
    print('payload', payload)
    print('api response', res)
    raise Exception('failed to add transaction')

client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

def sync():
  fiat = "USDT"
  for symbol in SYMBOLS:
    # symbol = "LTC"
    coin_id = get_coin_id(symbol)
    orders = client.get_all_orders(symbol=symbol+fiat)
    print(symbol, '(id:', coin_id, '):', len(orders), 'orders')
    for order in orders:
      if order['status'] != 'FILLED':
          continue

      id, date, price, qty, side = parse_order(order)

      if id in proccessed_orders:
        print('skip already sync order', id)
        continue

      print(id, date, side, price, qty)

      add_transaction_in_portfolio(
        coin_id=coin_id,
        side=side.lower(),
        quantity=qty,
        price=price,
        transactionTime=date,
        fee=0,
        note='orderid:'+str(id)+';'
      )

      # todo save as done
      print('synced order', id, symbol)
      mark_order_as_synced(id)


sync()