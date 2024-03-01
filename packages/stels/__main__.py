from pybit.unified_trading import HTTP
from colorama import Fore, Style
import time
import random
from gate_api import ApiClient, Configuration, Order, SpotApi

currency_pair = "SQR_USDT"
coin = currency_pair.split("_")[0]
currency = currency_pair.split("_")[1]

def get_wallet_balance(session, name, coin):
    try:
        balance = session.get_wallet_balance(accountType="UNIFIED", coin=coin)
        return {
            "worker": name,
            "usdt": balance["result"]["list"][0]["totalAvailableBalance"],
            "coin": balance["result"]["list"][0]["coin"][0]["walletBalance"],
            "estimated": balance["result"]["list"][0]["totalEquity"]
        }
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None


def get_orderbook(session, symbol):
    return session.get_orderbook(category="spot", symbol=symbol)


def cancel_order(session, symbol):
    return session.cancel_all_orders(category="spot", symbol=symbol)


def place_order(session, symbol, side, qty):
    order_link_id = f"{symbol}-{int(time.time() * 1000)}-{side.lower()}"

    return session.place_order(
        category="spot",
        symbol=symbol,
        side=side,
        orderType="Market",
        qty=str(qty),
        orderLinkId=order_link_id,
        isLeverage=0,
        orderFilter="Order",
    )


def calculate_profit(buy_price, sell_price, buy_volume, sell_volume):
    print("Buy price:", sell_price)
    print("Sell price:", sell_price)
    res = min(buy_volume, sell_volume) * (sell_price - buy_price)
    return res


def check_spread_threshold(spread, threshold):
    return abs(spread) > threshold


def process_worker(session, worker_name, pair, qty_bid, qty_ask, target, split):

    config = Configuration(key="b182631b05c9e02b4c042865c09ca1bf",
                           secret="875867edb4cfb8fd7d22738166455df5f52dac74af8ea41c380bc5990718d592")

    spot_api_gate = SpotApi(ApiClient(config))

    coin_balance = spot_api_gate.list_spot_accounts(currency=coin)
    usdt_balance = spot_api_gate.list_spot_accounts(currency=currency)

    balance = get_wallet_balance(session=session, name=worker_name, coin="SQR")

    prc = round(random.uniform(1, 1.79), 2)
    sum_usdt = target

    amount = round(random.uniform(float(sum_usdt) * split, float(sum_usdt) * split), 2)

    print(Fore.YELLOW, f"-POINT: {amount}")
    print(Fore.YELLOW, f"-SPLIT: {round((sum_usdt + (amount * 2)) - sum_usdt, 2)}")

    full_balance = round(float(balance["usdt"]) + float(usdt_balance[0].available), 4)
    full_balance_coin = round(float(balance["coin"]) + float(coin_balance[0].available), 4)

    print(Fore.YELLOW,
          f"-DISTANCE: {round(round(round(full_balance_coin, 4) * round((full_balance / full_balance_coin), 4) - full_balance, 2) / 1000, 2)}")
    print(Fore.YELLOW, f"-STELS: {round((full_balance / full_balance_coin), 4)}")
    print(Fore.WHITE, f"|--------------------------------------------|")

    if round(float(balance["usdt"]), 2) + float(usdt_balance[0].available) > (sum_usdt + (amount * 2)):
        if round(float(qty_ask), 2) > amount:
            place_order(session, pair, "Buy", round(float(amount), 2))
            print(Fore.GREEN, f"-BYBIT Buy: {round(float(amount), 2)}")

            order = Order(amount=str(round(float(amount), 2)), type="market", time_in_force="ioc", side='buy',
                          currency_pair=currency_pair)

            spot_api_gate.create_order(order)

            print(Fore.CYAN, f"-GATE Buy: {round(float(amount), 2)}")
        else:
            place_order(session, pair, "Buy", round(float(amount), 2))
            print(Fore.GREEN, f"-BYBIT Buy: {round(float(amount), 2)}")
            order = Order(amount=str(round(float(amount), 2)), type="market", time_in_force="ioc", side='buy',
                          currency_pair=currency_pair)

            spot_api_gate.create_order(order)

            print(Fore.CYAN, f"-GATE Buy: {round(float(amount), 2)}")
    else:
        if round(float(qty_bid), 2) > amount:
            place_order(session, pair, "Sell", round(float(amount) / prc, 2))
            print(Fore.RED, f"-BYBIT Sell: {round(float(amount) / prc, 2)}")

            order = Order(amount=str(round(float(amount) / prc, 2)), type="market", time_in_force="ioc", side='sell',
                          currency_pair=currency_pair)

            spot_api_gate.create_order(order)

            print(Fore.CYAN, f"-GATE Sell: {round(float(amount) / prc, 2)}")
        else:
            place_order(session, pair, "Sell", round(float(amount) / prc, 2))
            print(Fore.RED, f"-BYBIT Sell: {round(float(amount) / prc, 2)}")
            order = Order(amount=str(round(float(amount) / prc, 2)), type="market", time_in_force="ioc", side='sell',
                          currency_pair=currency_pair)

            spot_api_gate.create_order(order)
            print(Fore.CYAN, f"-GATE Sell: {round(float(amount) / prc, 2)}")

    print(Fore.MAGENTA, f"-SQR BALANCE: {round(full_balance_coin, 4)}")
    print(Fore.WHITE, f"|--------------------------------------------|")
    print(Fore.BLUE, f"-USD BALANCE BYBIT: {round(float(balance["usdt"]), 2)}")
    print(Fore.BLUE, f"-USD BALANCE GATE: {round(float(usdt_balance[0].available), 2)}")
    print(Fore.WHITE, f"|--------------------------------------------|")
    print(Fore.LIGHTGREEN_EX, f"-TARGET: {full_balance}")
    print(Fore.MAGENTA, f"|---------------Worker {worker_name}------------------|")
    print(Style.RESET_ALL)


def main():
    target = 415000
    while True:
        try:

            session_core = HTTP(
                testnet=False,
                api_key="w9sVxEr2AF5HJxUwlv",
                api_secret="ICSq48sbuDNYBBqCWHF8JczVN8AvmCsi5Oqz",
            )

            pair = coin + currency

            # Started
            book = get_orderbook(session_core, symbol=pair)

            qty_ask = book["result"]["a"][0][1]
            qty_bid = book["result"]["b"][0][1]

            sessions = [
                session_core
            ]
            worker_names = [
                "CORE",
            ]

            workers = len(worker_names)

            for i in range(workers):
                process_worker(
                    session=sessions[i],
                    worker_name=worker_names[i],
                    pair=pair,
                    target=target,
                    split=0.0021,
                    qty_bid=qty_bid,
                    qty_ask=qty_ask
                )

            session_core.client.close()
            target += 5
            time.sleep(5.2)

        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(0)