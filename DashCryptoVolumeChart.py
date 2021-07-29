import krakenex
import bitfinex
import cbpro
from pykrakenapi import KrakenAPI
import datetime as dt
import pandas as pd
import json
import requests
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash.dependencies import Input, Output
'''
    Kraken API
    ohlc: Open, High, Low, Close data frame.
        - get_ohlc_data():
            - interval - return 720 rows of data for interval provided
                    = 21600 : returns 15 day time frame
                    = 10080 : returns 7 day time frame
                    = 1440 : returns daily time frame
                    = 240 : returns 4 hour time frame
                    = 60 : returns hourly time frame
                    = 30 : returns half hour time frame
                    = 15 : returns 15 min time frame
                    = 5 : returns 5 min time frame
                    = 1 : returns 1 min time frame
    
'''
api = krakenex.API()
k = KrakenAPI(api)
public_client = cbpro.PublicClient()
# bitfinex api
api_v2 = bitfinex.bitfinex_v2.api_v2()

class DataFrames():
    def __init__(self):
        # default 1 min time interval for all data frames
        self.interval = '1m'
        # pair is BTC/USD byt default
        self.pair = 'DOGE'
        # creating instance variables that hold no value
        self.kraken_df = ""
        self.bitfinex_df = ""
        self.cbpro_df = ""
        self.binance_df = ""
        self.gemini_df = ""

    # updates data to current time frame
    def refreshDataFrames(self, pair = 'BTC'):
        self.pair = pair
        # function calls that returns a data frame and stores into instance variables
        self.kraken_df = self.KrakenDataFrame(self.interval)  # kraken DF
        self.bitfinex_df = self.BitfinexDataFrame(self.interval)  # bitfinex DF
        self.cbpro_df = self.CoinbaseProDataFrame(self.interval)  # Coinbase pro DF
        self.binance_df = self.BinanceDataFrame()  # Binance DF
        self.gemini_df = self.GeminiDataFrame()  # Gemini DF

    def GeminiDataFrame(self):
        try:
            url = "https://api.gemini.com/v2"
            df = pd.DataFrame(json.loads(requests.get(url+"/candles/"+self.pair.lower()+"usd/"+self.interval).text))
            # Stripping first 6 columns from data frame. Not all data from Binance is required.
            df = df.iloc[:, 0:6]
            # Renaming columns to better access data.
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            # casting data frame as type float
            df = df.astype('float')
            # converting millisecond time stamp into date time
            df['Date'] = pd.to_datetime(df['Date'], unit='ms')
            return df
        except ValueError:
            columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            dff = pd.DataFrame(columns=columns)
            return dff
    """
        BinanceDataFrame():
            - Generates data frame containing crypto historical data.
            - Handles cases where tokens are not available on  exchange
            - Return data frame if token of interest is on the exchange, None if otherwise.
    """
    def BinanceDataFrame(self):
        try:
            url = "https://api.binance.com/api/v3/klines"
            #interval = '1m'
            startTime = str(int((dt.datetime.now() - dt.timedelta(minutes=100)).timestamp()) * 1000)
            endTime = str(int(dt.datetime.now().timestamp()) * 1000)
            limit = '1000'
            symbol = self.pair+"USDT"
            # Creating dictionary for parameters
            req_params = {'symbol': symbol,
                          'interval': self.interval,
                          'startTime': startTime,
                          'endTime': endTime,
                          'limit': limit}
            # Making request for data from Binance API. Passing generated parameters of data to receive.
            # Storing data into a data frame.
            df = pd.DataFrame(json.loads(requests.get(url, params=req_params).text))
            # Stripping first 6 columns from data frame. Not all data from Binance is required.
            df = df.iloc[:, 0:6]
            # Renaming columns to better access data.
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            # casting data frame as type float
            df = df.astype('float')
            # converting millisecond time stamp into date time
            df['Date'] = pd.to_datetime(df['Date'], unit='ms')
            # reverse order of data frame
            df = df.iloc[::-1]
            return df
        except ValueError:
            columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            dff = pd.DataFrame(columns=columns)
            return dff
    """
        CoinbaseProDataFrame():
            - retreives data from Coinbase api. 
            - Historical data in desired interval
            - New data is sent every 5 mins.
    """
    def CoinbaseProDataFrame(self, interval):
        # retrieving historical data using Coinbase Pro Api
        df = public_client.get_product_historic_rates(product_id=self.pair+"-USD",granularity=60)
        # renaming columns
        columns = ['Date', 'Low', 'High', 'Open', 'Close', 'Volume']
        df = pd.DataFrame(data=df,columns=columns)
        # converting timestamp from seconds to date time %Y-%m-d
        df['Date'] = pd.to_datetime(df['Date'], unit='s')
        return df
    """
        KrakenDataFrame():
            - Generates data frame containing crypto historical data.
            - Handles cases where tokens are not available on  exchange
            - Return data frame if token of interest is on the exchange, None if otherwise.
    """
    def KrakenDataFrame(self,interval):
        if self.pair in ['ADA','ETH','DOT','BTC']:
            # using kraken api to create data frame
            df, last = k.get_ohlc_data(pair=self.pair+"USD", interval=1, ascending=True)
            # adjusting column names of data frame
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'VWAP', 'Volume', 'Count']
            # reverse order of data frame
            df = df.iloc[::-1]
            return df
        else:
            columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            dff = pd.DataFrame(columns=columns)
            return dff

    """
         BitfinexDataFrame():
             - Generates data frame containing crypto historical data.
             - Handles cases where tokens are not available on  exchange
             - Return data frame if token of interest is on the exchange, None if otherwise.
    """
    def BitfinexDataFrame(self,interval):
        # end time is current date
        endTime = str(int(dt.datetime.now().timestamp()) * 1000)
        # start time is  one year from current date
        startTime = str(int((dt.datetime.now() - dt.timedelta(days = 50)).timestamp()) * 1000)
        # retrieving data from Bitfinex API V2 passing parameters
        symbol = self.pair + 'USD'
        result = api_v2.candles(symbol=symbol,interval=self.interval, limit=50, start=startTime,end=endTime)
        # renaming columns for better access
        columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        # creating data frame from information retireved from Bitfinex
        df = pd.DataFrame(result,columns=columns)
        # changing timestamp dates from milliseconds to %Y-%m-%d 00:00:00
        df['Date'] = pd.to_datetime(df['Date'], unit='ms')
        # return data update data frame
        return df

# DataFrames() object which data will be accessed from,
df = DataFrames()
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# list of tokens that are found on dropdown.
token_list = ['BTC','ETH','ADA','DOGE','BNB','XRP']
# layout of trading volume app
app.layout = html.Div(
    html.Div(
        [
            html.H1(id='header',
                    style={'position':'absolute',
                           'top':'2%',
                           'left':'3.5%',
                           }
                    ),
            html.Div(
                  children=[
                      html.H6("Update Charts:",
                              style={"position": "absolute",
                                     "top":"5%",
                                     "left":'5%',
                                     }
                              ),
                      html.Button(
                          'update',
                          id='refresh-button',
                          style={"display": "inline-block",
                                 'position': 'absolute',
                                 'top' : '15%',
                                 'left': '57%',
                                 }
                      ),
                  ],style={'width': '32vh',
                           'height': '6vh',
                           "border": "1px #5c5c5c solid",
                           "position": "absolute",
                           "top": "7%",
                           "left": "87.15%",
                           "transform": "translate(-50%, -50%)"
                           }
                ),
            html.Div(
                children=[
                    html.H6("Crypto Currencies: ",
                            style={'display':'inline-block',
                                   'position':'absolute',
                                   "left":'5%',
                                   }
                            ),
                    dcc.Dropdown(
                        id='token-dropdown',
                        options=[{'label': x, 'value': x} for x in token_list],
                        value='BTC',
                        multi=False,
                        style={"display": "inline-block",
                               "width":'25vh',
                               'position':'absolute',
                               'left':"35%",
                               "top": '5%'
                               }
                    ),
                ],style={"width":'50vh',
                         "height":'6vh',
                         "position": "absolute",
                         "top": "73.4%",
                         "left": "47.4%",
                         "transform": "translate(-50%, -50%)",
                         },
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.H4(
                                "Volume Share",
                                style={"textAlign":'center'},
                            ),
                            dcc.Graph(
                                id='pie-chart',
                                style={'width': '58vh',
                                       'height': '60vh',
                                       "overflow": "hidden",
                                       "position": "absolute",
                                       "top": "60%",
                                       "left": "50%",
                                       "transform": "translate(-50%, -50%)",
                                       },
                                config=dict(displayModeBar=False),
                            ),
                        ],style={'width': '58vh',
                                 'height': '60vh',
                                 "border": "1px #5c5c5c solid",
                                 "overflow": "hidden",
                                 "position": "absolute",
                                 "top": "40%",
                                 "left": "18%",
                                 "transform": "translate(-50%, -50%)",
                                 },
                    ),
                    dcc.Graph(
                        id='bar-graph',
                        style={'width': '120vh',
                               'height': '60vh',
                               "display": "inline-block",
                               "border": "1px #5c5c5c solid",
                               "overflow": "hidden",
                               "position": "absolute",
                               "top": "40%",
                               "left": "65%",
                               "transform": "translate(-50%, -50%)",
                               },
                        #config=dict(displayModeBar=False),
                    ),
                ]
            ),
        ],
    )
)#main Div
"""
    First Callback:
        - Output 1: returns a bar chart figure to a data core component graph.
        - Output 2: returns a pie chart figure to a data core component graph.
        - Output 3: returns a string of the current crypto token that is plotted.
        - Input 1: receives input from a dropdown and passes the token value to our method.
        - Input 2: receives input when user clicks the refresh button to update chart.
        - Method: createFigures()
                    - takes in dropdown value and refresh button clicks.
                    - creates and updates data frames from callbacks inputs.
                    - gathers total volume from each crypto exchange and calculates distribution of volume.
                    - returns: bar chart figure, pie chart figure, and current token name to header.
"""
@app.callback(
    Output(component_id='bar-graph',component_property='figure'),
    Output(component_id='pie-chart',component_property='figure'),
    Output(component_id='header',component_property='children'),
    [Input(component_id='token-dropdown',component_property='value'),
     Input(component_id='refresh-button',component_property='n_clicks'),]
)
def createFigures(value,refresh_clicks):
    if refresh_clicks != None or value is not None:
        print(value)
        df.refreshDataFrames(value)
    # data frame list
    data_frame_list = [df.kraken_df,df.bitfinex_df,df.cbpro_df,df.binance_df,df.gemini_df]
    # data frame list is used to calculate the total volume of each data frame using a 30 minute interval.
    for i in range(len(data_frame_list)):
        data_frame_list[i] = sum(data_frame_list[i]['Volume'].iloc[0:30])
    # making copies of data frames
    bit = (df.bitfinex_df.copy()).iloc[0:30] # copy of bitfinex data frame
    bin = (df.binance_df.copy()).iloc[0:30] # copy of binance data frame
    cbp = (df.cbpro_df.copy()).iloc[0:30] # copy of coinbase pro data frame
    kra = (df.kraken_df.copy()).iloc[0:30] # copy of kraken data frame
    gem = (df.gemini_df.copy()).iloc[0:30] # copy of gemini data frame
    # creating list of values and list of exchange names.
    exchanges = ['Kraken','Bitfinex','Coinbase Pro','Binance','Gemini']
    # pie chart figure
    pie_fig = go.Figure(
        data=[
            go.Pie(
                labels=exchanges,
                values=data_frame_list,
            )
        ]
    )
    # bar chart figure
    bar_fig = go.Figure(
        data=[
            go.Bar(
                name='Bitfinex',
                x=bit['Date'],
                y=bit['Volume'].astype('float'),
            ),
            go.Bar(
                name='Binance',
                x=bin['Date'],
                y=bin['Volume'].astype('float'),
            ),
            go.Bar(
                name='Coinbase Pro',
                x=cbp['Date'],
                y=cbp['Volume'].astype('float'),
            ),
            go.Bar(
                name='Kraken',
                x=bit['Date'],
                y=kra['Volume'].astype('float'),
            ),
            go.Bar(
                name='Gemini',
                x=gem['Date'],
                y=gem['Volume'].astype('float'),
            ),
        ]
    )
    # configuring pie chart legend placement
    pie_fig.update_layout(
        legend=dict(orientation='h',
                    yanchor='bottom',
                    y=1.2,
                    xanchor='right',
                    x=.88,
                    )
    )
    # configuring bar chart legend placement
    # adding title to chart and axis labels
    bar_fig.update_layout(
        title=df.pair + "/USD",
        yaxis_title="Volume",
        barmode='stack',
        legend=dict(orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=.94
                    )
    )
    return bar_fig, pie_fig, "{}/USD Trading Volume".format(value)
"""
    main()
        - Uses Plotly Dash app to build charts.
"""
if __name__ == '__main__':
    app.run_server(debug=True)