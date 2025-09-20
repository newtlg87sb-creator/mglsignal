from flask import Flask, render_template, jsonify, request
import MetaTrader5 as mt5
import ta
import pandas as pd
import time

def initialize_mt5(symbol, timeframe, candle_count=100, retry_delay=10):
    if not mt5.initialize():
        print("MT5 Initialization failed:", mt5.last_error())
        time.sleep(retry_delay)
        return None

    if not mt5.symbol_select(symbol, True):
        print(f"Symbol select failed for {symbol}")
        mt5.shutdown()
        time.sleep(retry_delay)
        return None

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, candle_count)
    if rates is None or len(rates) < candle_count:
        print("Not enough candle data")
        mt5.shutdown()
        time.sleep(retry_delay)
        return None

    return rates

symbol = 'GOLD'
app = Flask(__name__)

if not mt5.initialize():
    print("MT5 initialization failed")
    quit()

timeframe = mt5.TIMEFRAME_M1

symbol_info = mt5.symbol_info(symbol)
if not symbol_info:
    print(f"Failed to get symbol info for {symbol}")
    mt5.shutdown()
    quit()

last_prices = {}

# Translation dictionary for static text
translations = {
    'en': {
        'title': 'Live MT5 Prices with Buy/Sell Signals',
        'heading': 'Live MT5 Prices with Buy/Sell Signals',
    },
    'es': {
        'title': 'Precios MT5 en Vivo con Señales de Compra/Venta',
        'heading': 'Precios MT5 en Vivo con Señales de Compra/Venta',
    },
    'mn': {
        'title': 'MT5 амьд үнэ, худалдан авах/заруулах дохио',
        'heading': 'MT5 амьд үнэ, худалдан авах/заруулах дохио',
    }
}


@app.route('/')
def home():
    lang = request.args.get('lang', 'en')
    if lang not in translations:
        lang = 'en'

    text = translations[lang]
    return render_template('index2.html', text=text, lang=lang)

@app.route('/about')
def about():
    lang = request.args.get('lang', 'en')
    if lang not in translations:
        lang = 'en'
    text = translations[lang]
    return render_template('about.html', text=text, lang=lang)

@app.route('/dashboard')
def dashboard():
    lang = request.args.get('lang', 'en')
    if lang not in translations:
        lang = 'en'
    text = translations[lang]
    return render_template('dashboard.html', text=text, lang=lang)

@app.route('/prices')
def get_prices():
    symbols = {
        'BTCUSD': 'BTCUSD',
        'ETHUSD': 'ETHUSD',
        'USDJPY': 'USDJPY',
        'GOLD': 'GOLD'
    }

    trading_data = []

    for display_name, symbol in symbols.items():
        RSI_30_DOWN = False
        RSI_30_UP = False
        RSI_70_UP = False
        RSI_70_DOWN = False

        info = mt5.symbol_info(symbol)
        if info and not info.visible:
            mt5.symbol_select(symbol, True)

        tick = mt5.symbol_info_tick(symbol)

        latest_rsi = None
        previous_rsi = None
        prev_two_rsi = None
        hh = None
        ll = None

        rates = initialize_mt5(symbol, timeframe)
        if rates is not None and len(rates) >= 10:
            df = pd.DataFrame(rates)
            df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=7).rsi()
            latest_rsi = df['rsi'].iloc[-1]
            previous_rsi = df['rsi'].iloc[-2]
            prev_two_rsi = df['rsi'].iloc[-3]

            last_3_candles = df.iloc[-4:-1]
            hh = last_3_candles['open'].max()
            ll = last_3_candles['open'].min()

        if tick:
            current_price = tick.bid
            prev_price = last_prices.get(symbol)

            if prev_price is None:
                signal = "HOLD"
            elif current_price > prev_price:
                signal = "BUY"
            elif current_price < prev_price:
                signal = "SELL"
            else:
                signal = "HOLD"

            last_prices[symbol] = current_price
            print(f"Last prices: {last_prices}")

            if prev_two_rsi is not None and previous_rsi is not None:
                if prev_two_rsi >= 30 and previous_rsi < 30:
                    RSI_30_DOWN = True
                    short_30 = hh
                elif prev_two_rsi <= 30 and previous_rsi > 30:
                    RSI_30_UP = True
                    long_30 = ll
                elif prev_two_rsi <= 70 and previous_rsi > 70:
                    RSI_70_UP = True
                    long_70 = ll
                elif prev_two_rsi >= 70 and previous_rsi < 70:
                    RSI_70_DOWN = True
                    short_70 = hh

            if RSI_30_UP:
                custom_signal = "BUY 1"
            elif RSI_70_UP:
                custom_signal = "BUY 2"
            elif RSI_30_DOWN:
                custom_signal = "SELL 2"
            elif RSI_70_DOWN:
                custom_signal = "SELL 11"
            else:
                custom_signal = ""

            trading_data.append({
                "symbol": display_name,
                "price": f"{current_price:.5f}",
                "signal": signal,
                "rsi": f"{latest_rsi:.2f}" if latest_rsi is not None else "N/A",
                "custom_signal": custom_signal
            })
        else:
            trading_data.append({
                "symbol": display_name,
                "price": "N/A",
                "signal": "HOLD",
                "rsi": "N/A",
                "custom_signal": ""
            })

    return jsonify(trading_data)

if __name__ == '__main__':
    app.run(debug=True)
