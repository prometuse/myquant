import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class Evaluator(object):
    def __init__(self):
        pass

    @staticmethod
    def stat_info(times, net_values, pct_values, btc_values):
        # max ratio
        max_ratio = np.max(pct_values)
        print(f"max ratio: {max_ratio}")
        print(f"final ratio: {pct_values[-1]}")

        # max revert
        max_revert = 1.0
        for i in range(1, len(net_values)):
            for j in range(1, i):
                if (net_values[i] - net_values[j]) / net_values[j] < max_revert:
                    max_revert = (net_values[i] - net_values[j]) / net_values[j]
        print(f"max revert: {max_revert}")

        # 绘制图形
        plot1 = plt.figure(1)
        plt.plot(times, net_values, label='nets')

        plot2 = plt.figure(2)
        plt.plot(times, pct_values, label='pcts', color="g")
        plt.plot(times, btc_values, label='pcts', color="r")

        plt.show()

        # # 保存文件
        # df.to_csv('数字货币轮动.csv', encoding='gbk', index=False)
        #
        #
        # temp = source_data.copy()
        #
        # # ===新建一个dataframe保存回测指标
        # results = pd.DataFrame()
        #
        # # ===计算累积净值
        # self.net =
        # results.loc[0, '累积净值'] = round(xtemp[tittle].iloc[-1], 2)
        #
        # # ===计算年化收益
        # annual_return = (temp[tittle].iloc[-1]) ** (
        #         '1 days 00:00:00' / (temp[time].iloc[-1] - temp[time].iloc[0]) * 365) - 1
        # results.loc[0, '年化收益'] = str(round(annual_return * 100, 2)) + '%'
        #
        # # ===计算最大回撤，最大回撤的含义：《如何通过3行代码计算最大回撤》https://mp.weixin.qq.com/s/Dwt4lkKR_PEnWRprLlvPVw
        # # 计算当日之前的资金曲线的最高点
        # temp['max2here'] = temp[tittle].expanding().max()
        # # 计算到历史最高值到当日的跌幅，drowdwon
        # temp['dd2here'] = temp[tittle] / temp['max2here'] - 1
        # # 计算最大回撤，以及最大回撤结束时间
        # end_date, max_draw_down = tuple(temp.sort_values(by=['dd2here']).iloc[0][[time, 'dd2here']])
        # # 计算最大回撤开始时间
        # start_date = temp[temp[time] <= end_date].sort_values(by=tittle, ascending=False).iloc[0][
        #     time]
        # # 将无关的变量删除
        # temp.drop(['max2here', 'dd2here'], axis=1, inplace=True)
        # results.loc[0, '最大回撤'] = format(max_draw_down, '.2%')
        # results.loc[0, '最大回撤开始时间'] = str(start_date)
        # results.loc[0, '最大回撤结束时间'] = str(end_date)
        #
        # # ===年化收益/回撤比：我个人比较关注的一个指标
        # results.loc[0, '年化收益/回撤比'] = round(annual_return / abs(max_draw_down), 2)

    def sharp(self):
        pass

    def apy(self):
        pass

    def maxRevert(self):
        pass
