"""
Week 5-6: 第一个实盘策略 - 资金费率套利（Delta中性）

策略逻辑：
  1. 扫描高资金费率的永续合约（>0.05%/8h，年化>54%）
  2. 现货做多 + 永续做空 = Delta中性
  3. 每8小时收取资金费率
  4. 资金费率回落时平仓退出

风控：
  - 单品种最大仓位：总资金20%
  - 最大持仓品种数：5个
  - 强制止损：现货+永续合计亏损>3%平仓
"""
import ccxt
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class Position:
    symbol: str
    spot_size: float        # 现货持仓量（正数=多头）
    perp_size: float        # 永续持仓量（负数=空头）
    entry_spot_price: float
    entry_perp_price: float
    entry_funding_rate: float
    open_time: datetime = field(default_factory=datetime.now)
    total_funding_collected: float = 0.0  # 累计收取的资金费


@dataclass
class RiskConfig:
    max_position_pct: float = 0.20        # 单品种最大仓位占总资金比例
    max_open_positions: int = 5            # 最大同时持仓数
    min_funding_rate: float = 0.0005      # 最低入场资金费率 (0.05%/8h)
    exit_funding_rate: float = 0.0002     # 退出资金费率阈值 (0.02%/8h)
    max_loss_pct: float = 0.03            # 单笔最大亏损比例（3%强制止损）
    slippage_estimate: float = 0.001      # 预估滑点（0.1%）


class FundingRateArbBot:
    """资金费率套利机器人"""

    def __init__(self, exchange_id: str = "binance"):
        self.exchange = getattr(ccxt, exchange_id)({
            "apiKey": os.getenv("EXCHANGE_API_KEY", ""),
            "secret": os.getenv("EXCHANGE_SECRET", ""),
            "enableRateLimit": True,
            "options": {"defaultType": "future"},  # 默认使用合约账户
        })
        self.spot_exchange = getattr(ccxt, exchange_id)({
            "apiKey": os.getenv("EXCHANGE_API_KEY", ""),
            "secret": os.getenv("EXCHANGE_SECRET", ""),
            "enableRateLimit": True,
        })
        self.risk = RiskConfig()
        self.positions: dict[str, Position] = {}
        self.paper_mode = True  # 默认纸交易模式
        logger.info(f"初始化套利机器人 | 交易所: {exchange_id} | 模式: {'纸交易' if self.paper_mode else '实盘'}")

    def get_account_balance(self) -> float:
        """获取账户USDT余额"""
        if self.paper_mode:
            return 10000.0  # 纸交易模拟余额

        balance = self.spot_exchange.fetch_balance()
        return float(balance.get("USDT", {}).get("free", 0))

    def calculate_opportunity_score(
        self, symbol: str, funding_rate: float, spot_price: float
    ) -> float:
        """
        计算套利机会评分

        评分 = 资金费率年化 - 开仓成本年化 - 预期关仓成本年化
        """
        annual_funding = funding_rate * 3 * 365  # 8h结算*3*365天
        open_cost = self.risk.slippage_estimate * 2  # 现货+永续各一次
        close_cost = self.risk.slippage_estimate * 2

        net_annual_return = annual_funding - (open_cost + close_cost) * 12  # 月均1次换仓
        return net_annual_return

    def scan_opportunities(self) -> list[dict]:
        """扫描市场中的套利机会"""
        opportunities = []
        markets = self.exchange.load_markets()
        swap_symbols = [
            s for s, m in markets.items()
            if m.get("swap") and "/USDT:" in s and m.get("active")
        ]

        for symbol in swap_symbols[:100]:
            try:
                rate_info = self.exchange.fetch_funding_rate(symbol)
                funding_rate = rate_info.get("fundingRate", 0)

                if funding_rate < self.risk.min_funding_rate:
                    continue

                # 对应现货品种
                spot_symbol = symbol.replace(":USDT", "")
                ticker = self.spot_exchange.fetch_ticker(spot_symbol)
                spot_price = ticker["last"]

                score = self.calculate_opportunity_score(symbol, funding_rate, spot_price)

                opportunities.append({
                    "symbol": symbol,
                    "spot_symbol": spot_symbol,
                    "funding_rate": funding_rate,
                    "annual_rate_pct": funding_rate * 3 * 365 * 100,
                    "spot_price": spot_price,
                    "next_funding": rate_info.get("fundingDatetime"),
                    "score": score,
                })
                time.sleep(0.2)
            except Exception as e:
                logger.debug(f"跳过 {symbol}: {e}")

        return sorted(opportunities, key=lambda x: x["score"], reverse=True)

    def open_position(self, opportunity: dict, position_size_usd: float) -> Optional[Position]:
        """开仓：现货做多 + 永续做空"""
        spot_symbol = opportunity["spot_symbol"]
        perp_symbol = opportunity["symbol"]
        spot_price = opportunity["spot_price"]
        coin_amount = position_size_usd / spot_price

        logger.info(
            f"开仓 {spot_symbol} | 规模: ${position_size_usd:.0f} | "
            f"资金费率: {opportunity['funding_rate']*100:.4f}% | "
            f"年化: {opportunity['annual_rate_pct']:.1f}%"
        )

        if self.paper_mode:
            logger.info(f"  [纸交易] 现货买入 {coin_amount:.4f} {spot_symbol} @ {spot_price}")
            logger.info(f"  [纸交易] 永续做空 {coin_amount:.4f} {perp_symbol} @ {spot_price}")
            return Position(
                symbol=spot_symbol,
                spot_size=coin_amount,
                perp_size=-coin_amount,
                entry_spot_price=spot_price,
                entry_perp_price=spot_price,
                entry_funding_rate=opportunity["funding_rate"],
            )

        # 实盘执行（先现货，再永续）
        try:
            spot_order = self.spot_exchange.create_market_buy_order(spot_symbol, coin_amount)
            perp_order = self.exchange.create_market_sell_order(perp_symbol, coin_amount)
            logger.info(f"开仓成功 | 现货订单: {spot_order['id']} | 永续订单: {perp_order['id']}")
            return Position(
                symbol=spot_symbol,
                spot_size=coin_amount,
                perp_size=-coin_amount,
                entry_spot_price=float(spot_order.get("average", spot_price)),
                entry_perp_price=float(perp_order.get("average", spot_price)),
                entry_funding_rate=opportunity["funding_rate"],
            )
        except Exception as e:
            logger.error(f"开仓失败: {e}")
            return None

    def close_position(self, position: Position, reason: str = "策略退出") -> float:
        """平仓，返回本次交易P&L（USD）"""
        logger.info(f"平仓 {position.symbol} | 原因: {reason}")

        try:
            spot_ticker = self.spot_exchange.fetch_ticker(position.symbol)
            current_price = spot_ticker["last"]
        except Exception:
            current_price = position.entry_spot_price  # fallback

        price_pnl = (current_price - position.entry_spot_price) * position.spot_size
        price_pnl += (position.entry_perp_price - current_price) * abs(position.perp_size)
        total_pnl = price_pnl + position.total_funding_collected

        logger.info(
            f"  价格P&L: ${price_pnl:.2f} | 资金费收入: ${position.total_funding_collected:.2f} | "
            f"总P&L: ${total_pnl:.2f}"
        )

        if not self.paper_mode:
            self.spot_exchange.create_market_sell_order(position.symbol, position.spot_size)
            perp_symbol = f"{position.symbol}/USDT:USDT"
            self.exchange.create_market_buy_order(perp_symbol, abs(position.perp_size))

        return total_pnl

    def check_exit_conditions(self, position: Position) -> Optional[str]:
        """检查是否需要平仓"""
        try:
            perp_symbol = f"{position.symbol}/USDT:USDT"
            rate_info = self.exchange.fetch_funding_rate(perp_symbol)
            current_rate = rate_info.get("fundingRate", position.entry_funding_rate)
        except Exception:
            current_rate = position.entry_funding_rate

        # 资金费率回落
        if current_rate < self.risk.exit_funding_rate:
            return f"资金费率回落至 {current_rate*100:.4f}%（低于退出阈值）"

        # 亏损止损检查
        try:
            ticker = self.spot_exchange.fetch_ticker(position.symbol)
            current_price = ticker["last"]
            price_loss_pct = (
                (position.entry_spot_price - current_price) / position.entry_spot_price
            )
            if price_loss_pct > self.risk.max_loss_pct:
                return f"触发止损：价格亏损 {price_loss_pct*100:.2f}%"
        except Exception:
            pass

        return None  # 继续持仓

    def run(self, check_interval_minutes: int = 60):
        """主循环"""
        logger.info("启动资金费率套利机器人...")
        total_pnl = 0.0

        while True:
            try:
                balance = self.get_account_balance()
                logger.info(f"账户余额: ${balance:.2f} | 当前持仓: {len(self.positions)} 个")

                # 检查现有持仓是否需要退出
                to_close = []
                for sym, pos in self.positions.items():
                    reason = self.check_exit_conditions(pos)
                    if reason:
                        to_close.append((sym, reason))

                for sym, reason in to_close:
                    pnl = self.close_position(self.positions[sym], reason)
                    total_pnl += pnl
                    del self.positions[sym]

                # 寻找新机会
                if len(self.positions) < self.risk.max_open_positions:
                    logger.info("扫描新机会...")
                    opportunities = self.scan_opportunities()

                    for opp in opportunities[:3]:
                        sym = opp["spot_symbol"]
                        if sym in self.positions:
                            continue

                        position_size = balance * self.risk.max_position_pct
                        pos = self.open_position(opp, position_size)
                        if pos:
                            self.positions[sym] = pos

                        if len(self.positions) >= self.risk.max_open_positions:
                            break

                logger.info(f"累计P&L: ${total_pnl:.2f} | 下次检查: {check_interval_minutes}分钟后")
                time.sleep(check_interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("收到停止信号，退出中...")
                break
            except Exception as e:
                logger.error(f"主循环异常: {e}", exc_info=True)
                time.sleep(60)


if __name__ == "__main__":
    # 纸交易模式测试
    bot = FundingRateArbBot("binance")
    bot.paper_mode = True
    bot.run(check_interval_minutes=5)  # 5分钟检查一次（测试用）
