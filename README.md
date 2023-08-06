This web app calculates the average gas fee of transactions on specific contracts for every hour of the day (based on 1 month + data) and presents it on a chart in USD.

Login page- the creds for this are hard coded.

Tools page- presenting a chart showing, for any contract address you type in that has up to 5000 transactions, the Hourly average fee (USD) over 30 days, per day for the last 30 days.


the app uses 2 APIs from etherscan:
1. https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={timestemp}&closest=after&apikey={ETHERSCAN_API_KEY}
   -> Returns the nearest block number before the timestamp, the app uses it to get 2 block numbers:
     1. now timestamp block number - now_block
     2. 30 days ago timestamp block number- last_30_day_block
  this data will be helpful to the 2nd API.

2.  https://api.etherscan.io/api?module=account&action=txlist&address={contract_address}&startblock={last_30_day_block}&endblock={now_block}&sort=asc&apikey={ETHERSCAN_API_KEY}
   -> Returns transaction list of specific contract address from x block number to y block number

 The data is stored in elasticsearch database and then the app calculates the Hourly average gas fee (USD) over 30 days and presents it in a chart using https://www.highcharts.com/demo/line-basic.


* to run the app(python flask)- python app.py
