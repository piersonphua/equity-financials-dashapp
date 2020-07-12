#!/usr/bin/env python
import pandas as pd
from datetime import datetime, timedelta
import requests
import plotly
import chart_studio.plotly as py
import plotly.graph_objs as go
import plotly.express as px
# Import the main functionality from the SimFin Python API.
import simfin as sf
# Import names used for easy access to SimFin's data-columns.
from simfin.names import *
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate

sf.set_api_key(api_key='free')
sf.set_data_dir('~/simfin_data/')
df_income = sf.load_income(variant='annual', market='us')
df_income = df_income.drop(
    columns=['SimFinId', 'Fiscal Period', 'Publish Date', 'Restated Date', 'Currency', 'Fiscal Year'])
df_balance = sf.load_balance(variant='annual', market='us')
df_balance = df_balance.drop(
    columns=['SimFinId', 'Fiscal Period', 'Publish Date', 'Restated Date', 'Currency', 'Fiscal Year',
             'Shares (Basic)', 'Shares (Diluted)'])
df_cashflow = sf.load_cashflow(variant='annual', market='us')
df_cashflow = df_cashflow.drop(
    columns=['SimFinId', 'Fiscal Period', 'Publish Date', 'Restated Date', 'Currency', 'Fiscal Year',
             'Shares (Basic)', 'Shares (Diluted)'])
df = pd.concat([df_income, df_balance, df_cashflow], axis=1)

def update_news():
    from datetime import datetime, timedelta
    import requests

    current_date=datetime.today().strftime('%Y-%m-%d')
    prev_date=(datetime.today()-timedelta(days=2)).strftime('%Y-%m-%d')
    url = ('http://newsapi.org/v2/top-headlines?'
           'country=us&'
           'category=business&'
           'apiKey=b76b10c1759149ac8c25dd8c6f161b2c')
    response = requests.get(url)
    json_data = response.json()["articles"]
    df = pd.DataFrame(json_data)
    df = pd.DataFrame(df[["title", "url"]])
    max_rows = 10

    return html.Div(
            children=[
                html.P(className="p-news", children="Headlines"),
                html.P(
                    className="p-news float-right",
                    children="Last update : "
                    + datetime.now().strftime("%H:%M:%S"),
                ),
                html.Table(
                    className="table-news",
                    children=[
                        html.Tr(
                            children=[
                                html.Td(
                                    children=[
                                        html.A(
                                            className="td-link",
                                            children=df.iloc[i]["title"],
                                            href=df.iloc[i]["url"],
                                            target="_blank",
                                        )
                                    ]
                                )
                            ]
                        )
                        for i in range(min(len(df), max_rows))
                    ],
                ),
            ]
        )



# Initialise the app
app = dash.Dash(__name__)

# Define the app
app.layout = html.Div(children=[
                      dcc.Interval(id="i_news", interval=1 * 60000, n_intervals=0),
                      html.Div(className='row',  # Define the row element
                               children=[
                                  html.Div(className='four columns div-user-controls',
                                           children=[
                                               html.H2('Dash App - STOCK FINANCIALS'),
                                               html.P(''' US Equity Financials Visualisation'''),
                                               html.P('''Insert stock ticker symbol below:'''),
                                               html.Div(className='div-for-search',
                                                        children=[
                                                            dcc.Input(id="stock-input",placeholder='Please insert ticker', type="text",value='AAPL',debounce=True)
                                                                ]
                                                        ),
                                               html.Div(
                                                        className="div-news",
                                                        children=[html.Div(id="news", children=update_news())],
                                                        )
                                                    ]
                                           ),  # Define the left element
                                  html.Div(className='eight columns div-for-charts bg-grey',
                                           children=[
                                                dcc.Graph(id="Earnings & Revenue",config={'displayModeBar': False}),
                                                dcc.Graph(id="Financial Health",config={'displayModeBar': False}),
                                                dcc.Graph(id="Debt to Equity",config={'displayModeBar': False}),
                                                dcc.Graph(id="Profitability",config={'displayModeBar': False}),
                                                dcc.Graph(id="Solvency & Liquidity",config={'displayModeBar': False})
                                                    ]
                                           )  # Define the right element
                                  ])
                                ])# Run the app

@app.callback([Output('Earnings & Revenue', 'figure'),
              Output('Financial Health', 'figure'),
              Output('Debt to Equity', 'figure'),
              Output('Profitability', 'figure'),
              Output('Solvency & Liquidity', 'figure')],
              [Input('stock-input', 'value')])
def update_graph(selected_ticker_symbol):

    ticker = df.loc[selected_ticker_symbol]

    # EARNINGS & REVENUE
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(x=ticker.index, y=ticker['Revenue'],
                             mode='lines+markers',
                             name='Revenue'), secondary_y=False, )
    fig.add_trace(go.Bar(x=ticker.index, y=(ticker['Revenue'] - ticker['Cost of Revenue']) / ticker['Revenue'],
                         opacity=0.2,
                         name='Profit Margin'), secondary_y=True, )

    fig.add_trace(go.Scatter(x=ticker.index, y=ticker['Net Income'],
                             mode='lines+markers',
                             name='Earnings'), secondary_y=False, )
    fig.add_trace(go.Scatter(x=ticker.index, y=ticker['Net Cash from Operating Activities'],
                             mode='lines+markers',
                             name='Operating Cash Flow'), secondary_y=False, )
    fig.add_trace(go.Scatter(x=ticker.index, y=ticker['Net Change in Cash'],
                             mode='lines+markers',
                             name='Free Cash Flow'), secondary_y=False, )
    fig.add_trace(go.Scatter(x=ticker.index, y=-1 * ticker['Operating Expenses'],
                             mode='lines+markers',
                             name='Operating Expenses'), secondary_y=False, )

    fig.update_layout(title="EARNINGS & REVENUE", barmode='group', hovermode='x', template="seaborn")
    fig.update_yaxes(title_text="in million USD", secondary_y=False)
    fig.update_yaxes(title_text="in %", secondary_y=True)
    fig.update_xaxes(rangeslider_visible=True)

    # FINANCIAL HEALTH
    colors = ['cornflowerblue', ] * 4
    colors[1] = 'darkred'
    colors[3] = 'darkred'

    fig2 = go.Figure([go.Bar(
        x=['Current Assets', 'Current Liabilities', 'Non-Current Assets', 'Non-Current Liabilities'],
        y=[ticker["Total Current Assets"].iloc[-1], ticker["Total Current Liabilities"].iloc[-1],
           ticker["Total Noncurrent Assets"].iloc[-1], ticker["Total Noncurrent Liabilities"].iloc[-1]],
        marker_color=colors
    )])
    fig2.update_layout(title="FINANCIAL HEALTH", barmode='group', hovermode='x', yaxis_title="in million USD",
                       template="seaborn")

    # DEBT TO EQUITY

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

    fig3.add_trace(go.Scatter(x=ticker.index, y=ticker['Long Term Debt'],
                              mode='lines+markers',
                              name='Long Term Debt'), secondary_y=False, )
    fig3.add_trace(go.Scatter(x=ticker.index, y=ticker['Total Equity'],
                              mode='lines+markers',
                              name='Total Equity'), secondary_y=False, )
    fig3.add_trace(go.Bar(x=ticker.index, y=((ticker['Long Term Debt'] / ticker['Total Equity']) * 100).round(3),
                          opacity=0.2,
                          name='Debt to Equity'), secondary_y=True, )
    fig3.add_trace(go.Scatter(x=ticker.index, y=ticker['Cash, Cash Equivalents & Short Term Investments'],
                              mode='lines+markers',
                              name='Cash & Cash Equivalents'), secondary_y=False, )

    fig3.update_layout(title="DEBT TO EQUITY", barmode='group', hovermode='x',template="seaborn")
    fig3.update_yaxes(title_text="in million USD", secondary_y=False)
    fig3.update_yaxes(title_text="in %", secondary_y=True)

    # PROFITABILITY
    ROE = ticker['Net Income'] / ticker['Total Equity']
    ROE = ROE.round(3)
    ROA = ticker['Net Income'] / ticker['Total Assets']
    ROA = ROA.round(3)

    fig4 = make_subplots(specs=[[{"secondary_y": True}]])

    fig4.add_trace(go.Bar(x=ticker.index, y=ROE * 100,
                          opacity=0.25,
                          name='ROE'), secondary_y=False)
    fig4.add_trace(go.Bar(x=ticker.index, y=ROA * 100,
                          opacity=0.25,
                          name='ROA'), secondary_y=False)
    fig4.add_trace(go.Scatter(x=ticker.index, y=ticker['Operating Income (Loss)'],
                              mode='lines+markers',
                              name='Operating Income'), secondary_y=True)

    fig4.update_layout(title="PROFITABILITY", barmode='group', hovermode='x',template="seaborn")
    fig4.update_yaxes(title_text="in million USD", secondary_y=False)
    fig4.update_yaxes(title_text="in %", secondary_y=True)

    # SOLVENCY & LIQUIDITY
    currentratio = ticker['Total Current Assets'] / ticker['Total Current Liabilities']
    currentratio = currentratio.round(3)
    # days receivables is the number of days of outstanding receivables. HIGH IS NOT GOOD
    salestoreceivable = ticker['Gross Profit'] / ticker['Accounts & Notes Receivable']
    daysreceivable = 365 / salestoreceivable
    daysreceivable = daysreceivable.round(3)

    fig5 = make_subplots(specs=[[{"secondary_y": True}]])
    # fig5.add_trace(go.Bar(x=ticker.index, y=ticker['Debt to Equity'],
    #                       name='Debt to Equity'), secondary_y=False, )
    fig5.add_trace(go.Bar(x=ticker.index, y=currentratio * 100,
                          name='Current Ratio'), secondary_y=False, )
    fig5.add_trace(go.Scatter(x=ticker.index, y=daysreceivable,
                              mode='lines+markers',
                              name='Days Outstanding Rec'), secondary_y=True, )

    fig5.update_layout(title="SOLVENCY & LIQUIDITY", barmode='group', hovermode='x',template="seaborn")
    fig5.update_yaxes(title_text="in %", secondary_y=False)
    fig5.update_yaxes(title_text="days", secondary_y=True)

    return fig, fig2, fig3, fig4, fig5



@app.callback(Output("news", "children"), [Input("i_news", "n_intervals")])
def update_news_div(n):
    return update_news()

if __name__ == '__main__':
    app.run_server(debug=True)