import datetime

# Import the backtrader platform
import backtrader as bt
import backtrader.analyzers as btanalyzers


class MyPair(bt.Strategy):
    params = dict(
        prop_size=1,
        eps=0.02,
        delta=0.01,
        short_margin=1.5,
    )

    def __init__(self):
        self.data0pctchg = bt.ind.PercentChange(self.datas[0], period=1)
        self.data1pctchg = bt.ind.PercentChange(self.datas[1], period=1)
        self.add_timer(datetime.time(0, 0, 0), monthdays=[1], monthcarry=True)
        self.status = 0
        self.data0pos = 0
        self.data1pos = 0

    def notify_timer(self, timer, when, *args, **kwargs):
        # Access the current positions
        positions = self.broker.positions

        # Get the current date and time
        current_datetime = self.datas[0].datetime.datetime()

        # Extract the current year and month
        current_year = current_datetime.year
        current_month = current_datetime.month
        print()
        print(f"Current year: {current_year}, Current month: {current_month}")

        # Print the current positions
        # for data, pos in positions.items():
        #     print(f"Data: {data._name}, Position: {pos.size}, Price: {pos.price}")

        # Print the current cash and value
        print(f"Current cash: {self.broker.get_cash()}, Current value: {self.broker.get_value()}")
        print()
    
    def _get_short_margin(self):
        total_short_value = 0

        for data, pos in self.broker.positions.items():
            if pos.size < 0:  # Only consider short positions
                short_value = abs(pos.size) * pos.price  # Calculate short value
                total_short_value += short_value

        return total_short_value * self.params.short_margin

    def _trade_count(self, price, total):
        return total * self.p.prop_size / price

    def next(self):
        margin_requirement = self._get_short_margin()
        excess_cash = self.broker.get_cash() - margin_requirement
        value_to_trade = excess_cash / (self.params.short_margin)
        amt0 = self._trade_count(self.data0.open[0], value_to_trade)
        amt1 = self._trade_count(self.data1.open[0], value_to_trade)

        if self.data0pctchg - self.data1pctchg > self.params.eps and self.status != -1:
            self.sell(data=self.data0, size=self.data0pos + amt0)
            self.buy(data=self.data1, size=self.data1pos + amt1)
            self.status = -1
            self.data0pos = amt0
            self.data1pos = amt1

        elif self.data0pctchg - self.data1pctchg < -self.params.eps and self.status != 1:
            self.buy(data=self.data0, size=self.data0pos + amt0)
            self.sell(data=self.data1, size=self.data1pos + amt1)
            self.status = 1
            self.data0pos = amt0
            self.data1pos = amt1
        
        elif abs(self.data0pctchg - self.data1pctchg) < self.params.delta and self.status != 0:
            self.close(data=self.data0)
            self.close(data=self.data1)
            self.status = 0
            self.data0pos = 0
            self.data1pos = 0


datapath0 = "./data/SOL_USDT_PERP_5m.csv"
datapath1 = "./data/BTC_USDT_PERP_5m.csv"

start = "2023-01-01"
end = "2023-10-01"

compression = 5

# Create a Data Feed
data0 = bt.feeds.GenericCSVData(
    dataname = datapath0,
    dtformat = ("%Y-%m-%d %H:%M:%S"), 
    compression = compression, 
    timeframe=bt.TimeFrame.Minutes,
    fromdate = datetime.datetime.strptime(start, '%Y-%m-%d'),
    todate = datetime.datetime.strptime(end, '%Y-%m-%d'),
    openinterest = -1,
    reverse = False)

data1 = bt.feeds.GenericCSVData(
    dataname = datapath1,
    dtformat = ("%Y-%m-%d %H:%M:%S"), 
    compression = compression, 
    timeframe=bt.TimeFrame.Minutes,
    fromdate = datetime.datetime.strptime(start, '%Y-%m-%d'),
    todate = datetime.datetime.strptime(end, '%Y-%m-%d'),
    openinterest = -1,
    reverse = False)


# Create a cerebro entity
cerebro = bt.Cerebro()

# Add a strategy
cerebro.addstrategy(MyPair)

# Add the Data Feed to Cerebro
cerebro.adddata(data0)
cerebro.adddata(data1)

cerebro.addanalyzer(btanalyzers.TradeAnalyzer)
cerebro.addanalyzer(btanalyzers.SharpeRatio, timeframe=bt.TimeFrame.Days, annualize=True)
cerebro.addanalyzer(btanalyzers.AnnualReturn)
cerebro.addanalyzer(btanalyzers.DrawDown)
cerebro.addanalyzer(btanalyzers.Transactions)

# Set our desired cash start
cerebro.broker.setcash(100000.0)

cerebro.broker.setcommission(commission=0.04 / 100)

# Print out the starting conditions
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Run over everything
startegies = cerebro.run()

# Print out the final result
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

# get all analyzers from strategies
sharpe_ratio = startegies[0].analyzers.sharperatio.get_analysis()
annual_return = startegies[0].analyzers.annualreturn.get_analysis()
drawdown = startegies[0].analyzers.drawdown.get_analysis()
trade_analyzer = startegies[0].analyzers.tradeanalyzer.get_analysis()
transactions = startegies[0].analyzers.transactions.get_analysis()

profit = cerebro.broker.getvalue() - 100000.0
print(f"Trading Pairs: {datapath0} and {datapath1}")
print(f"From {start} to {end}")

print()

# print all analyzers
print('Sharpe Ratio:', sharpe_ratio)
print()
print('Annual Return:', annual_return)
print()
print('Drawdown:', drawdown)
print()
print(f"{len(transactions.items())} transactions were made.")
print()
print(f"Average profit per trade: {profit / len(transactions.items())} USD")

# visualize
cerebro.plot()
